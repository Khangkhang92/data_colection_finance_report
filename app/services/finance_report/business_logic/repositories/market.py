from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from common.utils.dates import parse_date, parse_datetime
from common.orm.models import HistoryPrice, MarketMention, SessionQuote


class MarketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_history_price_date(self, symbol: str) -> date | None:
        return self.session.execute(
            select(HistoryPrice.date)
            .where(HistoryPrice.symbol_ticker == symbol)
            .order_by(HistoryPrice.date.desc())
            .limit(1)
        ).scalar_one_or_none()

    def upsert_market_mention(self, row: dict) -> None:
        stmt = insert(MarketMention).values(**row)
        update_values = {key: row.get(key) for key in row if key not in {"symbol_ticker", "date"}}
        if update_values:
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol_ticker", "date"],
                set_=update_values,
            )
        else:
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["symbol_ticker", "date"],
            )
        self.session.execute(stmt)

    def upsert_session_quote(self, raw: dict) -> None:
        row = {
            "symbol_ticker": raw.get("Symbol"),
            "side": raw.get("Side"),
            "match_price": raw.get("Price"),
            "volume": raw.get("Volume"),
            "total_volume": raw.get("TotalVolume"),
            "datetime": parse_datetime(raw.get("Date")),
        }
        stmt = insert(SessionQuote).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_ticker", "datetime"],
            set_={key: row.get(key) for key in row if key not in {"symbol_ticker", "datetime"}},
        )
        self.session.execute(stmt)

    def upsert_history_price(self, raw: dict) -> None:
        row = {
            "symbol_ticker": raw.get("symbol"),
            "price_high": raw.get("priceHigh"),
            "price_low": raw.get("priceLow"),
            "price_open": raw.get("priceOpen"),
            "price_average": raw.get("priceAverage"),
            "price_close": raw.get("priceClose"),
            "price_basic": raw.get("priceBasic"),
            "total_volume": raw.get("totalVolume"),
            "deal_volume": raw.get("dealVolume"),
            "putthrough_volume": raw.get("putthroughVolume"),
            "total_value": raw.get("totalValue"),
            "putthrough_value": raw.get("putthroughValue"),
            "buy_foreign_quantity": raw.get("buyForeignQuantity"),
            "buy_foreign_value": raw.get("buyForeignValue"),
            "sell_foreign_quantity": raw.get("sellForeignQuantity"),
            "sell_foreign_value": raw.get("sellForeignValue"),
            "buy_count": raw.get("buyCount"),
            "buy_quantity": raw.get("buyQuantity"),
            "sell_count": raw.get("sellCount"),
            "sell_quantity": raw.get("sellQuantity"),
            "adj_ratio": raw.get("adjRatio"),
            "current_foreign_room": raw.get("currentForeignRoom"),
            "prop_trading_net_deal_value": raw.get("propTradingNetDealValue"),
            "prop_trading_net_pt_value": raw.get("propTradingNetPTValue"),
            "prop_trading_net_value": raw.get("propTradingNetValue"),
            "date": parse_date(raw.get("date")),
        }
        stmt = insert(HistoryPrice).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_ticker", "date"],
            set_={key: row.get(key) for key in row if key not in {"symbol_ticker", "date"}},
        )
        self.session.execute(stmt)

    def mention_row_for_period(
        self,
        symbol: str,
        points: int | None,
        color: str | None,
        period: str,
        target_date: date,
    ) -> dict:
        row = {"symbol_ticker": symbol, "date": target_date}
        if period == "today":
            row.update({"day": points, "day_color": color})
        elif period == "weekly":
            row.update({"week": points, "week_color": color})
        elif period == "monthly":
            row.update({"month": points, "month_color": color})
        return row
