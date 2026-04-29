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


def get_symbols(session: Session, symbols: list[str] | None = None) -> list[str]:
    if symbols:
        logger.info("Using symbols from request count={count}", count=len(symbols))
        return symbols
    result = list(session.execute(select(Symbol.ticker)).scalars().all())
    logger.info("Loaded symbols from database count={count}", count=len(result))
    return result


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
            "industry": raw.get("industry"),
            "sector": raw.get("sector"),
            "short_industry": raw.get("shortIndustry") or raw.get("short_industry"),
            "cap_ratio": raw.get("capRatio") or raw.get("cap_ratio"),
        }
