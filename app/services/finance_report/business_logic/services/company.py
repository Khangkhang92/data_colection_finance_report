from __future__ import annotations

from business_logic.clients import ApiClient
from common.config.finance_api import Settings
from business_logic.repositories.company import CompanyRepository
from common.orm.schemas import CompanyDetailsSyncRequest, SyncResponse
from business_logic.services.symbols import get_symbols
from loguru import logger
from sqlalchemy.orm import Session


class CompanyService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = CompanyRepository(session)

    def sync(self, request: CompanyDetailsSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session)
        logger.info(
            "Company details sync started symbols={symbols} "
            "holders={holders} subsidiaries={subsidiaries}",
            symbols=len(symbols),
            holders=request.include_holders,
            subsidiaries=request.include_subsidiaries,
        )

        for symbol in symbols:
            if request.include_holders:
                try:
                    rows = self.client.get_json(f"{self.settings.holder_url}/{symbol}/holders")
                    fetched += len(rows or [])
                    saved_rows = self.repository.replace_holders(symbol, rows or [])
                    saved += saved_rows
                    logger.info(
                        "Company holders synced symbol={symbol} "
                        "fetched={fetched_rows} saved={saved_rows}",
                        symbol=symbol,
                        fetched_rows=len(rows or []),
                        saved_rows=saved_rows,
                    )
                except Exception as exc:
                    errors.append(f"{symbol}:holders: {exc}")
                    logger.exception("Company holders sync failed symbol={symbol}", symbol=symbol)

            if request.include_subsidiaries:
                try:
                    rows = self.client.get_json(
                        f"{self.settings.subsidiaries_url}/{symbol}/subsidiaries"
                    )
                    fetched += len(rows or [])
                    saved_rows = self.repository.replace_subsidiaries(symbol, rows or [])
                    saved += saved_rows
                    logger.info(
                        "Company subsidiaries synced symbol={symbol} "
                        "fetched={fetched_rows} saved={saved_rows}",
                        symbol=symbol,
                        fetched_rows=len(rows or []),
                        saved_rows=saved_rows,
                    )
                except Exception as exc:
                    errors.append(f"{symbol}:subsidiaries: {exc}")
                    logger.exception(
                        "Company subsidiaries sync failed symbol={symbol}",
                        symbol=symbol,
                    )

        logger.info(
            "Company details sync finished status={status} "
            "fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="company_details",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={"symbols": len(symbols)},
        )
