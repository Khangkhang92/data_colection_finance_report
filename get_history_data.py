from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import Symbol,Market
from dotenv import load_dotenv
from common.db import ScopedSession
from sqlalchemy.exc import SQLAlchemyError
import os
import requests
from loguru import logger
from datetime import datetime

from_date = "2024-09-04"
to_date = "2024-09-04"
logger.add("get_history_data.log", rotation="1 week", retention="1 month", level="WARNING")


def get_all_symbol():
    try:
        with ScopedSession() as session:
            stmt = select(Symbol.ticker)
            all_symbol = session.execute(stmt).scalars().all()
            for symbol in all_symbol:
                raw_data = fetch_price(symbol)
                save_2_db(Market,session,raw_data,symbol)
                logger.warning(f"{symbol}")  
    except SQLAlchemyError as e:
        logger.error(f"An error occurred: {e}")


def fetch_price(symbol):
    load_dotenv()
    url = os.getenv("HISTORY_PRICE_URL")
    url = url +f"/{symbol}/{from_date}/{to_date}"
    jwt_token = os.getenv("TOKEN")
    headers = {"JWTToken": f"{jwt_token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            raw_data = response.json()
            return raw_data

        else:
            logger.error(f"Error: Received response code {response.status_code}")
            logger.error(response.text)
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def save_2_db(model, session, values_to_insert, symbol):
    try:
        for item in values_to_insert:
            item_mapped = {
                "date": datetime.strptime(item.get("Date"), "%Y-%m-%dT%H:%M:%SZ").date(),
                "high": item.get("PriceHigh", None),
                "low": item.get("PriceLow", None),
                "open": item.get("PriceOpen", None),
                "close": item.get("PriceClose", None),
                "average": item.get("PriceAverage", None),
                "price_previous_close": item.get("PricePreviousClose", None),
                "price_basic": item.get("PriceBasic", None),
                "total_volume": item.get("TotalVolume", None),
                "deal_volume": item.get("DealVolume", None),
                "volume": item.get("Volume", None),
                "putthrough_volume": item.get("PutthroughVolume", None),
                "total_trade": item.get("TotalTrade", None),
                "total_value": item.get("TotalValue", None),
                "putthrough_value": item.get("PutthroughValue", None),
                "buy_foreign_quantity": item.get("BuyForeignQuantity", None),
                "buy_foreign_value": item.get("BuyForeignValue", None),
                "sell_foreign_quantity": item.get("SellForeignQuantity", None),
                "sell_foreign_value": item.get("SellForeignValue", None),
                "buy_count": item.get("BuyCount", None),
                "buy_quantity": item.get("BuyQuantity", None),
                "sell_count": item.get("SellCount", None),
                "sell_quantity": item.get("SellQuantity", None),
                "buy_avg": item.get("BuyAvg", None),
                "sell_avg": item.get("SellAvg", None),
                "adj_ratio": item.get("AdjRatio", None),
                "adj_close": item.get("AdjClose", None),
                "adj_open": item.get("AdjOpen", None),
                "adj_high": item.get("AdjHigh", None),
                "adj_low": item.get("AdjLow", None),
                "current_foreign_room": item.get("CurrentForeignRoom", None),
                "shares": item.get("Shares", None),
                "market_cap": item.get("MarketCap", None),
                "symbol_ticker": symbol,  
            }

            stmt = insert(model).values(**item_mapped)
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol_ticker", "date"],
                set_={
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "open": stmt.excluded.open,
                    "close": stmt.excluded.close,
                    "average": stmt.excluded.average,
                    "price_previous_close": stmt.excluded.price_previous_close,
                    "price_basic": stmt.excluded.price_basic,
                    "total_volume": stmt.excluded.total_volume,
                    "deal_volume": stmt.excluded.deal_volume,
                    "volume": stmt.excluded.volume,
                    "putthrough_volume": stmt.excluded.putthrough_volume,
                    "total_trade": stmt.excluded.total_trade,
                    "total_value": stmt.excluded.total_value,
                    "putthrough_value": stmt.excluded.putthrough_value,
                    "buy_foreign_quantity": stmt.excluded.buy_foreign_quantity,
                    "buy_foreign_value": stmt.excluded.buy_foreign_value,
                    "sell_foreign_quantity": stmt.excluded.sell_foreign_quantity,
                    "sell_foreign_value": stmt.excluded.sell_foreign_value,
                    "buy_count": stmt.excluded.buy_count,
                    "buy_quantity": stmt.excluded.buy_quantity,
                    "sell_count": stmt.excluded.sell_count,
                    "sell_quantity": stmt.excluded.sell_quantity,
                    "buy_avg": stmt.excluded.buy_avg,
                    "sell_avg": stmt.excluded.sell_avg,
                    "adj_ratio": stmt.excluded.adj_ratio,
                    "adj_close": stmt.excluded.adj_close,
                    "adj_open": stmt.excluded.adj_open,
                    "adj_high": stmt.excluded.adj_high,
                    "adj_low": stmt.excluded.adj_low,
                    "current_foreign_room": stmt.excluded.current_foreign_room,
                    "shares": stmt.excluded.shares,
                    "market_cap": stmt.excluded.market_cap,
                }
            )

            session.execute(stmt)
            date = item.get("Date")
            logger.info(f"{date} is store")
        session.commit()  
        

    except Exception as e:
        logger.error(f"Error saving data to the database: {e}")
        session.rollback()  # Rollback session on error

        
get_all_symbol()
