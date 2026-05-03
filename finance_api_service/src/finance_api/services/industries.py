from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from finance_api.clients import ApiClient
from finance_api.config import Settings
from finance_api.repositories.industries import IndustryRepository
from finance_api.schemas import IndustriesSyncRequest, SyncResponse
from finance_api.services.symbols import get_symbols


class IndustryService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = IndustryRepository(session)

    def sync(self, request: IndustriesSyncRequest) -> SyncResponse:
        raw_industries = self.client.get_json(
            self.settings.industries_url,
            include_auth=request.include_auth,
        )
        industry_rows = [
            row for row in (self._industry_row(raw) for raw in self._extract_rows(raw_industries))
            if row is not None
        ]
        fetched_industries = len(industry_rows)
        saved_industries = 0
        fetched_symbols = 0
        saved_symbols = 0
        errors: list[str] = []

        logger.info(
            "Industries sync started fetched_industries={count} include_symbols={include_symbols}",
            count=fetched_industries,
            include_symbols=request.include_symbols,
        )

        industry_names: dict[str, str | None] = {}
        for row in industry_rows:
            self.repository.upsert_industry(row)
            industry_names[row["industry_code"]] = row.get("name")
            saved_industries += 1

        if request.include_symbols:
            if request.icb_codes:
                fetched_symbols, saved_symbols, symbol_errors = (
                    self._sync_symbol_mappings_from_icb_codes(request.icb_codes, request.include_auth)
                )
            else:
                fetched_symbols, saved_symbols, symbol_errors = self._sync_symbol_mappings(
                    industry_names,
                    request.include_auth,
                )
            errors.extend(symbol_errors)

        logger.info(
            "Industries sync finished status={status} industries={industries} symbols={symbols} "
            "errors={errors}",
            status="ok" if not errors else "partial_error",
            industries=saved_industries,
            symbols=saved_symbols,
            errors=len(errors),
        )
        return SyncResponse(
            service="industries",
            status="ok" if not errors else "partial_error",
            fetched=fetched_industries + fetched_symbols,
            saved=saved_industries + saved_symbols,
            errors=errors,
            meta={
                "fetched_industries": fetched_industries,
                "saved_industries": saved_industries,
                "fetched_symbols": fetched_symbols,
                "saved_symbols": saved_symbols,
            },
        )

    def _industry_symbols_url(self, industry_code: str) -> str:
        template = self.settings.industry_symbols_url
        if "{industry_code}" in template:
            return template.format(industry_code=industry_code)
        return f"{template.rstrip('/')}/{industry_code}/symbols"

    def _sync_symbol_mappings(
        self,
        industry_names: dict[str, str | None],
        include_auth: bool,
    ) -> tuple[int, int, list[str]]:
        if self.settings.all_symbol_url:
            fetched, saved, errors = self._sync_symbol_mappings_from_instruments(
                industry_names,
                include_auth,
            )
            if saved > 0 or errors:
                return fetched, saved, errors
            logger.info(
                "No industry mapping fields found in instruments response; "
                "falling back to per-symbol details"
            )
            detail_fetched, detail_saved, detail_errors = self._sync_symbol_mappings_from_details(
                industry_names,
                include_auth,
            )
            return fetched + detail_fetched, detail_saved, detail_errors
        return self._sync_symbol_mappings_from_industry_members(industry_names, include_auth)

    def _sync_symbol_mappings_from_instruments(
        self,
        industry_names: dict[str, str | None],
        include_auth: bool,
    ) -> tuple[int, int, list[str]]:
        raw_symbols = self.client.get_json(
            self.settings.all_symbol_url,
            include_auth=include_auth,
        )
        symbol_rows = self._extract_rows(raw_symbols)
        saved = 0
        for raw_symbol in symbol_rows:
            industry_code = raw_symbol.get("industryCode") or raw_symbol.get("industry_code")
            row = self._symbol_mapping_row(
                raw_symbol,
                str(industry_code) if industry_code else None,
                industry_names.get(str(industry_code)) if industry_code else None,
            )
            if row is None:
                continue
            self.repository.upsert_symbol_mapping(row)
            saved += 1
        logger.info(
            "Industry symbol mappings synced from instruments fetched={fetched} saved={saved}",
            fetched=len(symbol_rows),
            saved=saved,
        )
        return len(symbol_rows), saved, []

    def _sync_symbol_mappings_from_details(
        self,
        industry_names: dict[str, str | None],
        include_auth: bool,
    ) -> tuple[int, int, list[str]]:
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session)
        for symbol in symbols:
            try:
                raw_symbol = self.client.get_json(
                    self._symbol_detail_url(symbol),
                    include_auth=include_auth,
                )
                fetched += 1
                industry_code = raw_symbol.get("industryCode") or raw_symbol.get("industry_code")
                row = self._symbol_mapping_row(
                    raw_symbol,
                    str(industry_code) if industry_code else None,
                    industry_names.get(str(industry_code)) if industry_code else None,
                )
                if row is None:
                    continue
                self.repository.upsert_symbol_mapping(row)
                saved += 1
            except Exception as exc:
                errors.append(f"{symbol}:detail: {exc}")
                logger.exception("Symbol industry detail sync failed symbol={symbol}", symbol=symbol)
        logger.info(
            "Industry symbol mappings synced from symbol details fetched={fetched} saved={saved}",
            fetched=fetched,
            saved=saved,
        )
        return fetched, saved, errors

    def _sync_symbol_mappings_from_icb_codes(
        self,
        icb_codes: list[str],
        include_auth: bool,
    ) -> tuple[int, int, list[str]]:
        fetched = 0
        saved = 0
        errors: list[str] = []
        for icb_code in icb_codes:
            try:
                raw_symbols = self.client.get_json(
                    self._industry_symbols_url(icb_code),
                    include_auth=include_auth,
                )
                symbol_rows = self._extract_symbol_rows(raw_symbols)
                fetched += len(symbol_rows)
                for raw_symbol in symbol_rows:
                    row = self._symbol_mapping_row(raw_symbol, None, None, icb_code=icb_code)
                    if row is None:
                        continue
                    self.repository.upsert_symbol_mapping(row)
                    saved += 1
                logger.info(
                    "ICB symbols synced icb_code={icb_code} fetched={fetched} saved_total={saved}",
                    icb_code=icb_code,
                    fetched=len(symbol_rows),
                    saved=saved,
                )
            except Exception as exc:
                errors.append(f"{icb_code}:symbols: {exc}")
                logger.exception("ICB symbols sync failed icb_code={icb_code}", icb_code=icb_code)
        return fetched, saved, errors

    def _sync_symbol_mappings_from_industry_members(
        self,
        industry_names: dict[str, str | None],
        include_auth: bool,
    ) -> tuple[int, int, list[str]]:
        fetched = 0
        saved = 0
        errors: list[str] = []
        for industry_code, industry_name in industry_names.items():
            try:
                raw_symbols = self.client.get_json(
                    self._industry_symbols_url(industry_code),
                    include_auth=include_auth,
                )
                symbol_rows = self._extract_symbol_rows(raw_symbols)
                fetched += len(symbol_rows)
                for raw_symbol in symbol_rows:
                    row = self._symbol_mapping_row(raw_symbol, industry_code, industry_name)
                    if row is None:
                        continue
                    self.repository.upsert_symbol_mapping(row)
                    saved += 1
                logger.info(
                    "Industry symbols synced industry_code={industry_code} "
                    "fetched={fetched} saved_total={saved_total}",
                    industry_code=industry_code,
                    fetched=len(symbol_rows),
                    saved_total=saved,
                )
            except Exception as exc:
                errors.append(f"{industry_code}:symbols: {exc}")
                logger.exception(
                    "Industry symbols sync failed industry_code={industry_code}",
                    industry_code=industry_code,
                )
        return fetched, saved, errors

    def _symbol_detail_url(self, symbol: str) -> str:
        template = self.settings.symbol_detail_url
        if "{symbol}" in template:
            return template.format(symbol=symbol)
        return f"{template.rstrip('/')}/{symbol}"

    def _extract_rows(self, raw_rows: Any) -> list[dict[str, Any]]:
        if isinstance(raw_rows, list):
            return [row for row in raw_rows if isinstance(row, dict)]
        if isinstance(raw_rows, dict):
            for value in raw_rows.values():
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
        return []

    def _extract_symbol_rows(self, raw_rows: Any) -> list[dict[str, Any]]:
        if isinstance(raw_rows, list):
            rows: list[dict[str, Any]] = []
            for row in raw_rows:
                if isinstance(row, dict):
                    rows.append(row)
                elif isinstance(row, str) and row.strip():
                    rows.append({"symbol": row.strip()})
            return rows
        if isinstance(raw_rows, dict):
            for value in raw_rows.values():
                if isinstance(value, list):
                    return self._extract_symbol_rows(value)
        return []

    def _industry_row(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        industry_code = raw.get("industryCode") or raw.get("industry_code")
        if not industry_code:
            return None
        return {
            "industry_code": str(industry_code),
            "parent_industry_code": (
                raw.get("parentIndustryCode")
                or raw.get("parent_industry_code")
                or raw.get("parentCode")
            ),
            "level": raw.get("level"),
            "name": raw.get("name"),
            "description": raw.get("description"),
        }

    def _symbol_mapping_row(
        self,
        raw: dict[str, Any],
        industry_code: str | None,
        industry_name: str | None,
        icb_code: str | None = None,
    ) -> dict[str, Any] | None:
        ticker = raw.get("symbol") or raw.get("instrument")
        if not ticker:
            return None
        resolved_industry_code = raw.get("industryCode") or raw.get("industry_code") or industry_code
        resolved_icb_code = raw.get("icbCode") or raw.get("icb_code") or icb_code
        if not resolved_industry_code and not resolved_icb_code:
            return None
        row = {
            "ticker": str(ticker).upper(),
            "exchange": raw.get("exchange"),
            "company_name": raw.get("name"),
            "industry_code": resolved_industry_code,
            "icb_code": resolved_icb_code,
            "industry": industry_name,
        }
        return {key: value for key, value in row.items() if value is not None}
