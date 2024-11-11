from getdata.base import Base
import json
from loguru import logger
from common.db import ScopedSession
from sqlalchemy.dialects.postgresql import insert
from functools import lru_cache
from models import Symbol, UpdateQuote
from datetime import datetime
from sqlalchemy import select, not_
import json


@lru_cache(maxsize=1)
def get_all_symbols():
    excluded_tickers = {"USD-VND", "VNINDEX", "VN30", "HNXINDEX", "UPINDEX", "HNX30"}
    with ScopedSession() as session:
        stmt = select(Symbol.ticker).where(not_(Symbol.ticker.in_(excluded_tickers)))
        return session.execute(stmt).scalars().all()


with open("data.json", "r", encoding="utf-8") as file:
    raw_data_list = json.load(file)

data_list = []


def convert_data(raw_data):
    converted_data = {
        "symbol_ticker": raw_data.get("Symbol", ""),
        "price_current": raw_data.get("PriceCurrent", "0.0"),
        "price_last": raw_data.get("PriceLast", "0.0"),
        "price_high": raw_data.get("PriceHigh", "0.0"),
        "price_low": raw_data.get("PriceLow", "0.0"),
        "price_open": raw_data.get("PriceOpen", "0.0"),
        "price_close": raw_data.get("PriceClose", "0.0"),
        "price_average": raw_data.get("PriceAverage", "0.0"),
        "price_percent_change": raw_data.get("PricePercentChange", "0.0"),
        "price_change": raw_data.get("PriceChange", "0.0"),
        "price_bid1": raw_data.get("PriceBid1", "0.0"),
        "quantity_bid1": raw_data.get("QuantityBid1", "0.0"),
        "price_ask1": raw_data.get("PriceAsk1", "0.0"),
        "quantity_ask1": raw_data.get("QuantityAsk1", "0.0"),
        "price_bid2": raw_data.get("PriceBid2", "0.0"),
        "quantity_bid2": raw_data.get("QuantityBid2", "0.0"),
        "price_ask2": raw_data.get("PriceAsk2", "0.0"),
        "quantity_ask2": raw_data.get("QuantityAsk2", "0.0"),
        "price_bid3": raw_data.get("PriceBid3", "0.0"),
        "quantity_bid3": raw_data.get("QuantityBid3", "0.0"),
        "price_ask3": raw_data.get("PriceAsk3", "0.0"),
        "quantity_ask3": raw_data.get("QuantityAsk3", "0.0"),
        "total_volume": raw_data.get("TotalVolume", "0.0"),
        "total_value": raw_data.get("TotalValue", "0.0"),
        "total_active_buy_volume": raw_data.get("TotalActiveBuyVolume", "0.0"),
        "total_active_sell_volume": raw_data.get("TotalActiveSellVolume", "0.0"),
        "buy_foreign_quantity": raw_data.get("BuyForeignQuantity", "0.0"),
        "buy_foreign_value": raw_data.get("BuyForeignValue", "0.0"),
        "sell_foreign_quantity": raw_data.get("SellForeignQuantity", "0.0"),
        "sell_foreign_value": raw_data.get("SellForeignValue", "0.0"),
        "current_foreign_room": raw_data.get("CurrentForeignRoom", "0.0"),
        "buy_count": raw_data.get("BuyCount", "0.0"),
        "sell_count": raw_data.get("SellCount", "0.0"),
        "buy_quantity": raw_data.get("BuyQuantity", "0.0"),
        "sell_quantity": raw_data.get("SellQuantity", "0.0"),
        "datetime": datetime.fromisoformat(raw_data.get("Date", "1970-01-01T00:00:00")),
    }
    converted_data["date"] = converted_data["datetime"].date()

    return converted_data


def upsert_update_quotes(data_list):

    if not data_list:
        logger.warning("No data to upsert.")
        return

    with ScopedSession() as session:
        for record in data_list:
            stmt = (
                insert(UpdateQuote)
                .values(**record)
                .on_conflict_do_update(
                    index_elements=[
                        "symbol_ticker",
                        "date",
                    ],  # Unique constraint columns
                    set_={
                        "price_current": record.get("price_current"),
                        "price_last": record.get("price_last"),
                        "price_high": record.get("price_high"),
                        "price_low": record.get("price_low"),
                        "price_open": record.get("price_open"),
                        "price_close": record.get("price_close"),
                        "price_average": record.get("price_average"),
                        "price_change": record.get("price_change"),
                        "price_percent_change": record.get("price_percent_change"),
                        "volume": record.get("volume"),
                        "total_active_buy_volume": record.get(
                            "total_active_buy_volume"
                        ),
                        "total_active_sell_volume": record.get(
                            "total_active_sell_volume"
                        ),
                        "buy_count": record.get("buy_count"),
                        "sell_count": record.get("sell_count"),
                        "buy_quantity": record.get("buy_quantity"),
                        "sell_quantity": record.get("sell_quantity"),
                        "buy_foreign_quantity": record.get("buy_foreign_quantity"),
                        "buy_foreign_value": record.get("buy_foreign_value"),
                        "sell_foreign_quantity": record.get("sell_foreign_quantity"),
                        "sell_foreign_value": record.get("sell_foreign_value"),
                        "current_foreign_room": record.get("current_foreign_room"),
                        "total_volume": record.get("total_volume"),
                        "total_value": record.get("total_value"),
                        "price_bid1": record.get("price_bid1"),
                        "quantity_bid1": record.get("quantity_bid1"),
                        "price_bid2": record.get("price_bid2"),
                        "quantity_bid2": record.get("quantity_bid2"),
                        "price_bid3": record.get("price_bid3"),
                        "quantity_bid3": record.get("quantity_bid3"),
                        "price_ask1": record.get("price_ask1"),
                        "quantity_ask1": record.get("quantity_ask1"),
                        "price_ask2": record.get("price_ask2"),
                        "quantity_ask2": record.get("quantity_ask2"),
                        "price_ask3": record.get("price_ask3"),
                        "quantity_ask3": record.get("quantity_ask3"),
                        "datetime": record.get("datetime"),
                        "date": record.get("date"),
                    },
                )
            )
            try:
                session.execute(stmt)
                logger.info("Upserted record for symbol: {}", record["symbol_ticker"])
            except Exception as e:
                logger.error(
                    "Error upserting record for symbol {}: {}",
                    record["symbol_ticker"],
                    e,
                )

        session.commit()
        logger.info("Upsert operation completed.")


for raw_data in raw_data_list["R"]:
    all_symbol = get_all_symbols()
    if raw_data["Symbol"] in all_symbol:
        data_list.append(convert_data(raw_data))

upsert_update_quotes(data_list)
