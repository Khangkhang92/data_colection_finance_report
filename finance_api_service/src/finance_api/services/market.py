from __future__ import annotations

from datetime import date, timedelta

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
        request = request or MarketMentionsSyncRequest()
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
        symbols = get_symbols(self.session)
        logger.info("Session quotes sync started symbols={symbols}", symbols=len(symbols))

        for symbol in symbols:
            try:
                rows = self.client.get_json(
                    self.settings.session_quote_url or "",
                    params={"symbol": symbol},
                    include_auth=False,
                )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"{symbol}: {exc}")
                logger.exception("Session quotes sync failed symbol={symbol}", symbol=symbol)
                continue

            for row in rows or []:
                self.repository.upsert_session_quote(row)
                saved += 1
            self.session.commit()
            fetched += len(rows or [])
            logger.info(
                "Session quotes synced symbol={symbol} fetched={fetched_rows} saved={saved_rows}",
                symbol=symbol,
                fetched_rows=len(rows or []),
                saved_rows=len(rows or []),
            )
            logger.info("Session quotes batch committed symbol={symbol}", symbol=symbol)

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

    def sync_history_prices(self, request: HistoryPricesSyncRequest | None = None) -> SyncResponse:
        request = request or HistoryPricesSyncRequest()
        fetched = 0
        saved = 0
        errors: list[str] = []
        symbols = get_symbols(self.session)
        default_end_date = date.today()
        default_start_date = default_end_date - timedelta(days=365)
        logger.info(
            "History prices sync started symbols={symbols} "
            "default_start_date={start_date} end_date={end_date}",
            symbols=len(symbols),
            start_date=default_start_date,
            end_date=default_end_date,
        )

        for symbol in symbols:
            start_date = self.repository.get_latest_history_price_date(symbol) or default_start_date
            end_date = default_end_date
            if start_date > end_date:
                logger.info(
                    "History prices skipped symbol={symbol} reason=already_up_to_date latest_date={latest_date}",
                    symbol=symbol,
                    latest_date=start_date,
                )
                continue
            try:
                rows = self.client.get_json(
                    f"{self.settings.subsidiaries_url}/{symbol}/historical-quotes",
                    params={
                        "startDate": start_date.isoformat(),
                        "endDate": end_date.isoformat(),
                        "limit": request.limit,
                    },
                )
            except Exception as exc:
                self.session.rollback()
                errors.append(f"{symbol}: {exc}")
                logger.exception("History prices sync failed symbol={symbol}", symbol=symbol)
                continue

            for row in rows or []:
                self.repository.upsert_history_price(row)
                saved += 1
            self.session.commit()
            fetched += len(rows or [])
            logger.info(
                "History prices synced symbol={symbol} start_date={start_date} end_date={end_date} fetched={fetched_rows} saved={saved_rows}",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                fetched_rows=len(rows or []),
                saved_rows=len(rows or []),
            )
            logger.info("History prices batch committed symbol={symbol}", symbol=symbol)

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
            meta={
                "symbols": len(symbols),
                "default_start_date": default_start_date.isoformat(),
                "end_date": default_end_date.isoformat(),
                "limit": request.limit,
            },
        )
