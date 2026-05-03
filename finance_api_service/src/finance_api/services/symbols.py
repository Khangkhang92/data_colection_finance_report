from __future__ import annotations

from typing import Any

from finance_api.clients import ApiClient
from finance_api.config import Settings
from finance_api.repositories.symbols import SymbolRepository
from finance_api.schemas import SymbolsSyncRequest, SyncResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from finance_schema.models import Symbol
from loguru import logger


NON_REPORT_PREFIXES = ("FUE", "FUC", "E1")
NON_REPORT_NAME_KEYWORDS = (
    "quy etf",
    "quy đầu tư",
    "quỹ đầu tư",
    "quy mo",
    "quỹ mở",
    "quy dong",
    "quỹ đóng",
    "fund",
    "etf",
    "index",
    "chi so",
    "chỉ số",
)


def get_symbols(session: Session, symbols: list[str] | None = None) -> list[str]:
    if symbols:
        logger.info(
            "Ignoring request symbols and loading from database requested_count={count}",
            count=len(symbols),
        )
    result = list(
        session.execute(select(Symbol.ticker).order_by(Symbol.ticker.asc())).scalars().all()
    )
    logger.info("Loaded symbols from database count={count} order=alphabetical", count=len(result))
    return result


def is_financial_report_symbol(ticker: str, company_name: str | None) -> bool:
    upper_ticker = ticker.upper()
    if upper_ticker.startswith(NON_REPORT_PREFIXES):
        return False

    normalized_name = (company_name or "").strip().lower()
    return not any(keyword in normalized_name for keyword in NON_REPORT_NAME_KEYWORDS)


def get_financial_report_symbols(session: Session) -> list[str]:
    rows = session.execute(
        select(Symbol.ticker, Symbol.company_name).order_by(Symbol.ticker.asc())
    ).all()
    symbols = [
        row.ticker
        for row in rows
        if is_financial_report_symbol(row.ticker, row.company_name)
    ]
    skipped = len(rows) - len(symbols)
    logger.info(
        "Loaded financial-report symbols count={count} skipped_non_company={skipped} order=alphabetical",
        count=len(symbols),
        skipped=skipped,
    )
    return symbols


class SymbolService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = SymbolRepository(session)

    def sync(self, request: SymbolsSyncRequest) -> SyncResponse:
        raw_rows = self.client.get_json(
            self.settings.all_symbol_url or "",
            include_auth=request.include_auth,
        )
        rows = self._extract_rows(raw_rows)
        rows.sort(key=self._symbol_sort_key)
        allowed_types = set(request.instrument_types or [])
        fetched = len(rows)
        saved = 0
        skipped = 0

        logger.info(
            "Symbols sync started fetched={fetched} instrument_types={instrument_types}",
            fetched=fetched,
            instrument_types=request.instrument_types,
        )

        for raw in rows:
            if allowed_types and raw.get("type") not in allowed_types:
                skipped += 1
                continue
            row = self._symbol_row(raw)
            if row is None:
                skipped += 1
                continue
            self.repository.upsert_symbol(row)
            saved += 1

        logger.info(
            "Symbols sync finished fetched={fetched} saved={saved} skipped={skipped}",
            fetched=fetched,
            saved=saved,
            skipped=skipped,
        )
        return SyncResponse(
            service="symbols",
            fetched=fetched,
            saved=saved,
            meta={
                "skipped": skipped,
                "instrument_types": request.instrument_types,
            },
        )

    def _symbol_sort_key(self, raw: dict[str, Any]) -> tuple[str, str]:
        ticker = str(raw.get("symbol") or raw.get("instrument") or "").upper()
        exchange = str(raw.get("exchange") or "").upper()
        return ticker, exchange

    def _extract_rows(self, raw_rows: Any) -> list[dict[str, Any]]:
        if isinstance(raw_rows, list):
            return [row for row in raw_rows if isinstance(row, dict)]
        if isinstance(raw_rows, dict):
            for value in raw_rows.values():
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
        return []

    def _symbol_row(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        ticker = raw.get("symbol") or raw.get("instrument")
        exchange = raw.get("exchange")
        if not ticker or not exchange:
            return None
        return {
            "ticker": str(ticker).upper(),
            "exchange": exchange,
            "company_name": raw.get("name"),
            "industry_code": raw.get("industryCode") or raw.get("industry_code"),
            "icb_code": raw.get("icbCode") or raw.get("icb_code"),
            "industry": raw.get("industry"),
            "sector": raw.get("sector"),
            "short_industry": raw.get("shortIndustry") or raw.get("short_industry"),
            "cap_ratio": raw.get("capRatio") or raw.get("cap_ratio"),
        }
