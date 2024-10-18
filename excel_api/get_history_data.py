from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import Symbol, Market
from dotenv import load_dotenv
from common.db import ScopedSession
from sqlalchemy.exc import SQLAlchemyError
import os
import requests
from loguru import logger
from datetime import datetime, date
from sqlalchemy import func
from models.market import Market
import sys

# Create log directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(log_dir, "get_history_data.log")

# Configure logger
config = {
    "handlers": [
        {
            "sink": sys.stderr,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        },
        {
            "sink": log_file,
            "rotation": "10 MB",
            "retention": "1 week",
            "compression": "zip",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        },
    ],
}

# Remove default logger and apply new configuration
logger.configure(**config)


def get_date_range():
    with ScopedSession() as session:
        # Get the latest date for each symbol
        subquery = (
            session.query(
                Market.symbol_ticker, func.max(Market.date).label("latest_date")
            )
            .group_by(Market.symbol_ticker)
            .subquery()
        )

        # Join with the Symbol table to get all symbols
        latest_dates = (
            session.query(Symbol.ticker, subquery.c.latest_date)
            .outerjoin(subquery, Symbol.ticker == subquery.c.symbol_ticker)
            .all()
        )

        current_date = date.today()
        return latest_dates, current_date


# Update the from_date, to_date assignment
latest_dates, to_date = get_date_range()
to_date = to_date.strftime("%Y-%m-%d")


def get_all_symbol():
    try:
        with ScopedSession() as session:
            stmt = select(Symbol.ticker)
            all_symbols = session.execute(stmt).scalars().all()

            # Batch processing
            batch_size = 100
            for i in range(0, len(all_symbols), batch_size):
                batch = all_symbols[i : i + batch_size]
                process_symbol_batch(batch, session)

    except SQLAlchemyError as e:
        logger.error(f"An error occurred: {e}")


def process_symbol_batch(symbols, session):
    for symbol in symbols:
        from_date = next((date for sym, date in latest_dates if sym == symbol), None)
        from_date = (
            from_date.strftime("%Y-%m-%d") if from_date else "2024-01-01"
        )  # Default if no data
        raw_data = fetch_price(symbol, from_date, to_date)
        if raw_data:
            save_2_db(Market, session, raw_data, symbol)
        logger.warning(f"Processed {symbol}")


def fetch_price(symbol, from_date, to_date):
    load_dotenv()
    url = os.getenv("HISTORY_PRICE_URL")
    url = url + f"/{symbol}/{from_date}/{to_date}"
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
        # Define a mapping of API fields to database columns
        field_mapping = {
            "Date": "date",
            "PriceHigh": "high",
            "PriceLow": "low",
            "PriceOpen": "open",
            "PriceClose": "close",
            "PriceAverage": "average",
            "PricePreviousClose": "price_previous_close",
            "PriceBasic": "price_basic",
            "TotalVolume": "total_volume",
            "DealVolume": "deal_volume",
            "Volume": "volume",
            "PutthroughVolume": "putthrough_volume",
            "TotalTrade": "total_trade",
            "TotalValue": "total_value",
            "PutthroughValue": "putthrough_value",
            "BuyForeignQuantity": "buy_foreign_quantity",
            "BuyForeignValue": "buy_foreign_value",
            "SellForeignQuantity": "sell_foreign_quantity",
            "SellForeignValue": "sell_foreign_value",
            "BuyCount": "buy_count",
            "BuyQuantity": "buy_quantity",
            "SellCount": "sell_count",
            "SellQuantity": "sell_quantity",
            "BuyAvg": "buy_avg",
            "SellAvg": "sell_avg",
            "AdjRatio": "adj_ratio",
            "AdjClose": "adj_close",
            "AdjOpen": "adj_open",
            "AdjHigh": "adj_high",
            "AdjLow": "adj_low",
            "CurrentForeignRoom": "current_foreign_room",
            "Shares": "shares",
            "MarketCap": "market_cap",
        }

        # Prepare bulk insert data
        bulk_insert_data = []
        for item in values_to_insert:
            item_mapped = {
                db_col: item.get(api_field)
                for api_field, db_col in field_mapping.items()
            }
            item_mapped["date"] = datetime.strptime(
                item["Date"], "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            item_mapped["symbol_ticker"] = symbol
            bulk_insert_data.append(item_mapped)

        # Perform bulk upsert
        stmt = insert(model).values(bulk_insert_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_ticker", "date"],
            set_={col: stmt.excluded[col] for col in field_mapping.values()},
        )

        result = session.execute(stmt)

        # Check if the insert was successful
        if result.rowcount > 0:
            session.flush()  # Ensure all changes are sent to the database
            session.commit()
            logger.info(
                f"Data for symbol {symbol} stored successfully. Rows affected: {result.rowcount}"
            )
        else:
            logger.warning(f"No rows were inserted or updated for symbol {symbol}")

    except Exception as e:
        logger.error(f"Error saving data to the database: {e}")
        session.rollback()


if __name__ == "__main__":
    get_all_symbol()
