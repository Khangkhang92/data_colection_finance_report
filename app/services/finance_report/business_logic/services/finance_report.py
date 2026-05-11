from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from business_logic.clients import ApiClient
from common.config.finance_api import Settings
from business_logic.repositories.finance_report import FinanceStatementRepository
from common.orm.schemas import FinanceStatementsSyncRequest, FinancialReportType, SyncResponse
from business_logic.services.symbols import get_financial_report_symbols
from loguru import logger
from sqlalchemy.orm import Session


@dataclass
class PendingFinanceBatch:
    symbol: str
    report_type: int
    latest_existing: tuple[int, int] | None
    missing_periods: list[tuple[int, int]]


class FinanceStatementService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = FinanceStatementRepository(session)

    def sync(self, request: FinanceStatementsSyncRequest | None = None) -> SyncResponse:
        request = request or FinanceStatementsSyncRequest()
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_financial_report_symbols(self.session)
        anchor_year, anchor_quarter = self._current_reporting_period(date.today())
        target_periods = self._build_target_periods(
            start_year=anchor_year,
            start_quarter=anchor_quarter,
            limit=request.limit,
        )
        pending_batches = self._collect_pending_batches(
            symbols=symbols,
            report_types=request.report_types,
            target_periods=target_periods,
        )
        logger.info(
            "Finance statements sync started symbols={symbols} "
            "report_types={report_types} anchor_year={year} anchor_quarter={quarter} limit={limit} pending_batches={pending_batches}",
            symbols=len(symbols),
            report_types=[int(report_type) for report_type in request.report_types],
            year=anchor_year,
            quarter=anchor_quarter,
            limit=request.limit,
            pending_batches=len(pending_batches),
        )

        for pending in pending_batches:
            symbol = pending.symbol
            report_type_value = pending.report_type
            latest_existing = pending.latest_existing
            missing_before = pending.missing_periods

            url = f"{self.settings.finance_url}/{symbol}/full-financial-reports"
            params = {
                "type": report_type_value,
                "year": anchor_year,
                "quarter": anchor_quarter,
                "limit": request.limit,
            }
            try:
                rows = self.client.get_json(url, params=params)
                if not rows:
                    logger.info(
                        "Finance statements returned no rows "
                        "symbol={symbol} report_type={report_type} latest_existing={latest_existing}",
                        symbol=symbol,
                        report_type=report_type_value,
                        latest_existing=latest_existing,
                    )
                    continue
                fetched += len(rows)
                saved_rows = self.repository.save_report_tree(rows, symbol, report_type_value)
                saved += saved_rows
                existing_after = self.repository.get_existing_periods(
                    symbol, report_type_value, target_periods
                )
                missing_after = [
                    period for period in target_periods if period not in existing_after
                ]
                logger.info(
                    "Finance statements synced symbol={symbol} report_type={report_type} "
                    "fetched={fetched_rows} saved={saved_rows} "
                    "latest_existing={latest_existing} missing_before={missing_before} missing_after={missing_after}",
                    symbol=symbol,
                    report_type=report_type_value,
                    fetched_rows=len(rows),
                    saved_rows=saved_rows,
                    latest_existing=latest_existing,
                    missing_before=len(missing_before),
                    missing_after=len(missing_after),
                )
                # Commit per symbol/report_type batch so long sync jobs do not lose all progress.
                self.session.commit()
                logger.info(
                    "Finance statements batch committed symbol={symbol} report_type={report_type}",
                    symbol=symbol,
                    report_type=report_type_value,
                )
                if missing_after:
                    errors.append(
                        f"{symbol}:{report_type_value}: missing periods after sync {missing_after}"
                    )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"{symbol}:{report_type_value}: {exc}")
                logger.exception(
                    "Finance statements sync failed symbol={symbol} report_type={report_type}",
                    symbol=symbol,
                    report_type=report_type_value,
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
            meta={
                "symbols": len(symbols),
                "pending_batches": len(pending_batches),
                "anchor_year": anchor_year,
                "anchor_quarter": anchor_quarter,
                "limit": request.limit,
            },
        )

    def _collect_pending_batches(
        self,
        symbols: list[str],
        report_types: list[FinancialReportType],
        target_periods: list[tuple[int, int]],
    ) -> list[PendingFinanceBatch]:
        pending: list[PendingFinanceBatch] = []
        for symbol in symbols:
            for report_type in report_types:
                report_type_value = int(report_type)
                latest_existing = self.repository.get_latest_period(symbol, report_type_value)
                existing_periods = self.repository.get_existing_periods(
                    symbol, report_type_value, target_periods
                )
                missing_periods = [
                    period for period in target_periods if period not in existing_periods
                ]
                if not missing_periods:
                    logger.info(
                        "Finance statements already covered symbol={symbol} report_type={report_type} "
                        "latest_existing={latest_existing} periods={period_count}",
                        symbol=symbol,
                        report_type=report_type_value,
                        latest_existing=latest_existing,
                        period_count=len(target_periods),
                    )
                    continue
                pending.append(
                    PendingFinanceBatch(
                        symbol=symbol,
                        report_type=report_type_value,
                        latest_existing=latest_existing,
                        missing_periods=missing_periods,
                    )
                )
        return pending

    @staticmethod
    def _build_target_periods(
        start_year: int,
        start_quarter: int,
        limit: int,
    ) -> list[tuple[int, int]]:
        periods: list[tuple[int, int]] = []
        year = start_year
        quarter = start_quarter
        total = max(limit, 1)

        for _ in range(total):
            periods.append((year, quarter))
            year, quarter = FinanceStatementService._previous_period(year, quarter)
        return periods

    @staticmethod
    def _previous_period(year: int, quarter: int) -> tuple[int, int]:
        if quarter == 0:
            return (year - 1, 0)
        if quarter == 1:
            return (year - 1, 4)
        return (year, quarter - 1)

    @staticmethod
    def _current_reporting_period(today: date) -> tuple[int, int]:
        current_quarter = ((today.month - 1) // 3) + 1
        if current_quarter == 1:
            return (today.year - 1, 4)
        return (today.year, current_quarter - 1)
