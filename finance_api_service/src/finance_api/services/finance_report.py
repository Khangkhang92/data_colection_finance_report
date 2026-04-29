from __future__ import annotations

from finance_api.clients import ApiClient
from finance_api.config import Settings
from finance_api.repositories.finance_report import FinanceStatementRepository
from finance_api.schemas import FinanceStatementsSyncRequest, SyncResponse
from finance_api.services.symbols import get_symbols
from loguru import logger
from sqlalchemy.orm import Session


class FinanceStatementService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = FinanceStatementRepository(session)

    def sync(self, request: FinanceStatementsSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session, request.symbols)
        logger.info(
            "Finance statements sync started symbols={symbols} "
            "report_types={report_types} year={year} quarter={quarter}",
            symbols=len(symbols),
            report_types=request.report_types,
            year=request.year,
            quarter=request.quarter,
        )

        for symbol in symbols:
            for report_type in request.report_types:
                url = f"{self.settings.finance_url}/{symbol}/full-financial-reports"
                params = {
                    "type": report_type,
                    "year": request.year,
                    "quarter": request.quarter,
                    "limit": request.limit,
                }
                try:
                    rows = self.client.get_json(url, params=params)
                    if not rows:
                        logger.info(
                            "Finance statements returned no rows "
                            "symbol={symbol} report_type={report_type}",
                            symbol=symbol,
                            report_type=report_type,
                        )
                        continue
                    fetched += len(rows)
                    saved_rows = self.repository.save_report_tree(rows, symbol, report_type)
                    saved += saved_rows
                    logger.info(
                        "Finance statements synced symbol={symbol} report_type={report_type} "
                        "fetched={fetched_rows} saved={saved_rows}",
                        symbol=symbol,
                        report_type=report_type,
                        fetched_rows=len(rows),
                        saved_rows=saved_rows,
                    )
                except Exception as exc:
                    errors.append(f"{symbol}:{report_type}: {exc}")
                    logger.exception(
                        "Finance statements sync failed symbol={symbol} report_type={report_type}",
                        symbol=symbol,
                        report_type=report_type,
                    )

        logger.info(
            "Finance statements sync finished status={status} "
            "fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="finance_statements",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={"symbols": len(symbols)},
        )
