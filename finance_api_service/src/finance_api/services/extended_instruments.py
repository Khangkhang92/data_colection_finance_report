from __future__ import annotations

from typing import Any

from finance_api.clients import ApiClient
from finance_api.config import Settings
from finance_api.repositories.extended_instruments import ExtendedInstrumentRepository
from finance_api.schemas import ExtendedInstrumentsSyncRequest, SyncResponse
from loguru import logger
from sqlalchemy.orm import Session


class ExtendedInstrumentService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = ExtendedInstrumentRepository(session)

    def sync(self, request: ExtendedInstrumentsSyncRequest) -> SyncResponse:
        request = request or ExtendedInstrumentsSyncRequest()
        fetched = 0
        saved = 0
        errors: list[str] = []
        warrant_symbols: set[str] = set()

        if request.include_futures:
            result = self._sync_symbol_search_type(
                keywords=request.futures_keywords,
                instrument_type="futures",
                limit=request.search_limit,
                include_auth=request.include_auth,
                errors=errors,
            )
            fetched += result[0]
            saved += result[1]

        if request.include_warrants:
            result = self._sync_symbol_search_type(
                keywords=request.warrant_keywords,
                instrument_type="warrant",
                limit=request.search_limit,
                include_auth=request.include_auth,
                errors=errors,
            )
            fetched += result[0]
            saved += result[1]
            warrant_symbols.update(result[2])
            warrant_result = self._sync_warrant_infos(
                symbols=sorted(warrant_symbols),
                include_auth=request.include_auth,
                errors=errors,
            )
            fetched += warrant_result[0]
            saved += warrant_result[1]

        if request.include_etf_details:
            result = self._sync_symbol_details(
                symbols=request.etf_symbols,
                include_auth=request.include_auth,
                errors=errors,
            )
            fetched += result[0]
            saved += result[1]

        if request.include_mxv_contracts:
            result = self._sync_mxv_contracts(
                limit=request.mxv_limit,
                include_auth=request.include_auth,
                errors=errors,
            )
            fetched += result[0]
            saved += result[1]

        logger.info(
            "Extended instruments sync finished status={status} fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="extended_instruments",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={
                "include_futures": request.include_futures,
                "include_warrants": request.include_warrants,
                "include_etf_details": request.include_etf_details,
                "include_mxv_contracts": request.include_mxv_contracts,
            },
        )

    def _sync_symbol_search_type(
        self,
        keywords: list[str],
        instrument_type: str,
        limit: int,
        include_auth: bool,
        errors: list[str],
    ) -> tuple[int, int, set[str]]:
        fetched = 0
        saved = 0
        symbols: set[str] = set()
        for keyword in keywords:
            try:
                rows = self.client.get_json(
                    self.settings.symbol_search_url,
                    params={"keywords": keyword, "type": instrument_type, "limit": limit},
                    include_auth=include_auth,
                )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"{instrument_type}:{keyword}: {exc}")
                logger.exception(
                    "Extended symbol search failed type={type} keyword={keyword}",
                    type=instrument_type,
                    keyword=keyword,
                )
                continue

            for raw in self._extract_rows(rows):
                symbol_row = self._symbol_row(raw, default_type=instrument_type)
                if symbol_row is None:
                    continue
                self.repository.upsert_symbol(symbol_row)
                if instrument_type == "futures":
                    self.repository.upsert_derivative_contract(
                        self._derivative_row(raw, symbol_row)
                    )
                if instrument_type == "warrant":
                    symbols.add(symbol_row["ticker"])
                saved += 1
            self.session.commit()
            fetched += len(rows or [])
            logger.info(
                "Extended symbol search synced type={type} keyword={keyword} fetched={fetched_rows}",
                type=instrument_type,
                keyword=keyword,
                fetched_rows=len(rows or []),
            )
        return fetched, saved, symbols

    def _sync_symbol_details(
        self,
        symbols: list[str],
        include_auth: bool,
        errors: list[str],
    ) -> tuple[int, int]:
        fetched = 0
        saved = 0
        for symbol in symbols:
            try:
                raw = self.client.get_json(
                    self.settings.symbol_detail_url.format(symbol=symbol),
                    include_auth=include_auth,
                )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"symbol_detail:{symbol}: {exc}")
                logger.exception("Extended symbol detail failed symbol={symbol}", symbol=symbol)
                continue
            if not isinstance(raw, dict):
                continue
            row = self._symbol_row(raw)
            if row is None:
                continue
            self.repository.upsert_symbol(row)
            self.session.commit()
            fetched += 1
            saved += 1
        return fetched, saved

    def _sync_warrant_infos(
        self,
        symbols: list[str],
        include_auth: bool,
        errors: list[str],
    ) -> tuple[int, int]:
        fetched = 0
        saved = 0
        for symbol in symbols:
            try:
                raw = self.client.get_json(
                    self.settings.symbol_warrant_info_url.format(symbol=symbol),
                    include_auth=include_auth,
                )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"warrant_info:{symbol}: {exc}")
                logger.exception("Warrant info sync failed symbol={symbol}", symbol=symbol)
                continue
            if not isinstance(raw, dict):
                continue
            self.repository.upsert_warrant_info(raw)
            self.session.commit()
            fetched += 1
            saved += 1
        return fetched, saved

    def _sync_mxv_contracts(
        self,
        limit: int,
        include_auth: bool,
        errors: list[str],
    ) -> tuple[int, int]:
        try:
            rows = self.client.get_json(
                self.settings.mxv_contracts_url,
                params={"limit": limit},
                include_auth=include_auth,
            )
        except Exception as exc:
            self.session.rollback()
            errors.append(f"mxv_contracts: {exc}")
            logger.exception("MXV contracts sync failed")
            return 0, 0

        saved = 0
        for raw in self._extract_rows(rows):
            self.repository.upsert_commodity_contract(raw)
            saved += 1
        self.session.commit()
        return len(rows or []), saved

    def _extract_rows(self, raw_rows: Any) -> list[dict[str, Any]]:
        if isinstance(raw_rows, list):
            return [row for row in raw_rows if isinstance(row, dict)]
        if isinstance(raw_rows, dict):
            for value in raw_rows.values():
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
        return []

    def _symbol_row(
        self,
        raw: dict[str, Any],
        default_type: str | None = None,
    ) -> dict[str, Any] | None:
        ticker = raw.get("symbol") or raw.get("instrument")
        if not ticker:
            return None
        return {
            "ticker": str(ticker).upper(),
            "exchange": raw.get("exchange") or "UNKNOWN",
            "company_name": raw.get("name"),
            "instrument_type": raw.get("type") or raw.get("instrumentType") or default_type,
            "instrument_code": raw.get("instrument"),
            "is_listing": raw.get("isListing")
            if raw.get("isListing") is not None
            else raw.get("is_listing"),
            "industry_code": raw.get("industryCode") or raw.get("industry_code"),
            "icb_code": raw.get("icbCode") or raw.get("icb_code"),
            "industry": raw.get("industry"),
            "sector": raw.get("sector"),
            "short_industry": raw.get("shortIndustry") or raw.get("short_industry"),
            "cap_ratio": raw.get("capRatio") or raw.get("cap_ratio"),
        }

    def _derivative_row(self, raw: dict[str, Any], symbol_row: dict[str, Any]) -> dict[str, Any]:
        symbol = symbol_row["ticker"]
        return {
            "symbol_ticker": symbol,
            "contract_code": symbol,
            "contract_name": raw.get("name"),
            "contract_type": symbol_row.get("instrument_type"),
            "underlying_symbol": "VN30" if symbol.startswith("VN30F") else None,
            "exchange": symbol_row.get("exchange"),
            "instrument_code": symbol_row.get("instrument_code"),
            "is_listing": symbol_row.get("is_listing"),
            "source": "fireant_symbols_search",
        }
