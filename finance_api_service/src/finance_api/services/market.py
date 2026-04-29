from __future__ import annotations

from datetime import date

from finance_api.clients import ApiClient
from finance_api.config import Settings
from finance_api.repositories.market import MarketRepository
from finance_api.schemas import (
    HistoryPricesSyncRequest,
    MarketMentionsSyncRequest,
    SessionQuotesSyncRequest,
    SyncResponse,
)
from finance_api.services.symbols import get_symbols
from loguru import logger
from sqlalchemy.orm import Session


class MarketService:
    def __init__(self, settings: Settings, client: ApiClient, session: Session) -> None:
        self.settings = settings
        self.client = client
        self.session = session
        self.repository = MarketRepository(session)

    def sync_mentions(self, request: MarketMentionsSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []
        target_date = request.target_date or date.today()
        symbols = set(get_symbols(self.session))
        logger.info(
            "Market mentions sync started periods={periods} "
            "target_date={target_date} symbols={symbols}",
            periods=request.periods,
            target_date=target_date,
            symbols=len(symbols),
        )

        for period in request.periods:
            try:
                rows = self.client.get_json(
                    f"{self.settings.market_mention_url}/{period}",
                    params={"limit": request.limit},
                )
            except Exception as exc:
                errors.append(f"{period}: {exc}")
                logger.exception("Market mentions sync failed period={period}", period=period)
                continue

            saved_before = saved
            for row in rows or []:
                symbol = row.get("symbol")
                if symbol not in symbols:
                    continue
                mention = self.repository.mention_row_for_period(
                    symbol=symbol,
                    points=row.get("points"),
                    color=row.get("color"),
                    period=period,
                    target_date=target_date,
                )
                self.repository.upsert_market_mention(mention)
                saved += 1
            fetched += len(rows or [])
            logger.info(
                "Market mentions period synced period={period} "
                "fetched={fetched_rows} saved={saved_rows}",
                period=period,
                fetched_rows=len(rows or []),
                saved_rows=saved - saved_before,
            )

        logger.info(
            "Market mentions sync finished status={status} "
            "fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="market_mentions",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
        )

    def sync_session_quotes(self, request: SessionQuotesSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session, request.symbols)
        logger.info("Session quotes sync started symbols={symbols}", symbols=len(symbols))

        for symbol in symbols:
            try:
                rows = self.client.get_json(
                    self.settings.session_quote_url or "",
                    params={"symbol": symbol},
                    include_auth=False,
                )
            except Exception as exc:
                errors.append(f"{symbol}: {exc}")
                logger.exception("Session quotes sync failed symbol={symbol}", symbol=symbol)
                continue

            for row in rows or []:
                self.repository.upsert_session_quote(row)
                saved += 1
            fetched += len(rows or [])
            logger.info(
                "Session quotes synced symbol={symbol} fetched={fetched_rows} saved={saved_rows}",
                symbol=symbol,
                fetched_rows=len(rows or []),
                saved_rows=len(rows or []),
            )

        logger.info(
            "Session quotes sync finished status={status} "
            "fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="session_quotes",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={"symbols": len(symbols)},
        )

    def sync_history_prices(self, request: HistoryPricesSyncRequest) -> SyncResponse:
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session, request.symbols)
        logger.info(
            "History prices sync started symbols={symbols} "
            "start_date={start_date} end_date={end_date}",
            symbols=len(symbols),
            start_date=request.start_date,
            end_date=request.end_date,
        )

        for symbol in symbols:
            try:
                rows = self.client.get_json(
                    f"{self.settings.subsidiaries_url}/{symbol}/historical-quotes",
                    params={
                        "startDate": request.start_date.isoformat(),
                        "endDate": request.end_date.isoformat(),
                        "limit": request.limit,
                    },
                )
            except Exception as exc:
                errors.append(f"{symbol}: {exc}")
                logger.exception("History prices sync failed symbol={symbol}", symbol=symbol)
                continue

            for row in rows or []:
                self.repository.upsert_history_price(row)
                saved += 1
            fetched += len(rows or [])
            logger.info(
                "History prices synced symbol={symbol} fetched={fetched_rows} saved={saved_rows}",
                symbol=symbol,
                fetched_rows=len(rows or []),
                saved_rows=len(rows or []),
            )

        logger.info(
            "History prices sync finished status={status} "
            "fetched={fetched} saved={saved} errors={errors}",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=len(errors),
        )
        return SyncResponse(
            service="history_prices",
            status="ok" if not errors else "partial_error",
            fetched=fetched,
            saved=saved,
            errors=errors,
            meta={"symbols": len(symbols)},
        )
