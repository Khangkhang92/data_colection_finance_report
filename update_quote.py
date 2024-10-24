from getdata.base import Base
from dotenv import load_dotenv
import os
import redis
import json
from loguru import logger
from common.db import ScopedSession
from sqlalchemy import select, not_
from sqlalchemy.dialects.postgresql import insert
from functools import lru_cache
from models import Symbol, UpdateQuote
from datetime import datetime

# Load environment variables
load_dotenv()

# Cache the list of symbols
@lru_cache(maxsize=1)
def get_all_symbols():
    excluded_tickers = {
        'USD-VND', 'VNINDEX', 'VN30', 'HNXINDEX', 'UPINDEX', 'HNX30'
    }
    with ScopedSession() as session:
        stmt = select(Symbol.ticker).where(not_(Symbol.ticker.in_(excluded_tickers)))
        return session.execute(stmt).scalars().all()

# Initialize Redis client
try:
    redis_client = redis.Redis(host="127.0.0.1", port="6379", db=0)
except redis.ConnectionError as e:
    logger.error("Could not connect to Redis: {}", e)
    raise



def convert_hash_data(hash_data):
    converted_data = {
        'symbol_ticker': str(hash_data.get('symbol_ticker', '')),
        'price_bid1': float(hash_data.get('price_bid1', '0.0')),
        'price_bid2': float(hash_data.get('price_bid2', '0.0')),
        'quantity_bid2': float(hash_data.get('quantity_bid2', '0.0')),
        'price_bid3': float(hash_data.get('price_bid3', '0.0')),
        'quantity_bid3': float(hash_data.get('quantity_bid3', '0.0')),
        'datetime': datetime.fromisoformat(hash_data.get('datetime', '1970-01-01T00:00:00')),
        'quantity_ask1': float(hash_data.get('quantity_ask1', '0.0')),
        'price_ask1': float(hash_data.get('price_ask1', '0.0')),
        'price_ask2': float(hash_data.get('price_ask2', '0.0')),
        'quantity_ask2': float(hash_data.get('quantity_ask2', '0.0')),
        'price_ask3': float(hash_data.get('price_ask3', '0.0')),
        'quantity_ask3': float(hash_data.get('quantity_ask3', '0.0')),
        'price_current': float(hash_data.get('price_current', '0.0')),
        'price_last': float(hash_data.get('price_last', '0.0')),
        'price_high': float(hash_data.get('price_high', '0.0')),
        'price_low': float(hash_data.get('price_low', '0.0')),
        'price_open': float(hash_data.get('price_open', '0.0')),
        'price_close': float(hash_data.get('price_close', '0.0')),
        'price_average': float(hash_data.get('price_average', '0.0')),
        'total_volume': float(hash_data.get('total_volume', '0.0')),
        'volume': float(hash_data.get('volume', '0.0')),
        'total_value': float(hash_data.get('total_value', '0.0')),
        'total_active_buy_volume': float(hash_data.get('total_active_buy_volume', '0.0')),
        'total_active_sell_volume': float(hash_data.get('total_active_sell_volume', '0.0')),
        'price_percent_change': float(hash_data.get('price_percent_change', '0.0')),
        'price_change': float(hash_data.get('price_change', '0.0')),
        'quantity_bid1': float(hash_data.get('quantity_bid1', '0.0')),
        'buy_foreign_quantity': float(hash_data.get('buy_foreign_quantity', '0.0')),
        'buy_foreign_value': float(hash_data.get('buy_foreign_value', '0.0')),
        'sell_foreign_quantity': float(hash_data.get('sell_foreign_quantity', '0.0')),
        'sell_foreign_value': float(hash_data.get('sell_foreign_value', '0.0')),
        'current_foreign_room': float(hash_data.get('current_foreign_room', '0.0')),
    }

    # Extract the date from the datetime object
    converted_data['date'] = converted_data['datetime'].date()

    return converted_data



def upsert_update_quotes(data_from_redis):

    if not data_from_redis:
        logger.warning("No data to upsert.")
        return
    
    with ScopedSession() as session:
        for record in data_from_redis:
            stmt = insert(UpdateQuote).values(**record).on_conflict_do_update(
                index_elements=['symbol_ticker', 'date'],  # Unique constraint columns
                set_={
                    'price_current': record.get("price_current"),
                    'price_last': record.get("price_last"),
                    'price_high': record.get("price_high"),
                    'price_low': record.get("price_low"),
                    'price_open': record.get("price_open"),
                    'price_close': record.get("price_close"),
                    'price_average': record.get("price_average"),
                    'price_change': record.get("price_change"),
                    'price_percent_change': record.get("price_percent_change"),
                    'volume': record.get("volume"),
                    'total_active_buy_volume': record.get("total_active_buy_volume"),
                    'total_active_sell_volume': record.get("total_active_sell_volume"),
                    'buy_foreign_quantity': record.get("buy_foreign_quantity"),
                    'buy_foreign_value': record.get("buy_foreign_value"),
                    'sell_foreign_quantity': record.get("sell_foreign_quantity"),
                    'sell_foreign_value': record.get("sell_foreign_value"),
                    'current_foreign_room': record.get("current_foreign_room"),
                    'total_volume': record.get("total_volume"),
                    'total_value': record.get("total_value"),
                    'price_bid1': record.get("price_bid1"),
                    'quantity_bid1': record.get("quantity_bid1"),
                    'price_bid2': record.get("price_bid2"),
                    'quantity_bid2': record.get("quantity_bid2"),
                    'price_bid3': record.get("price_bid3"),
                    'quantity_bid3': record.get("quantity_bid3"),
                    'price_ask1': record.get("price_ask1"),
                    'quantity_ask1': record.get("quantity_ask1"),
                    'price_ask2': record.get("price_ask2"),
                    'quantity_ask2': record.get("quantity_ask2"),
                    'price_ask3': record.get("price_ask3"),
                    'quantity_ask3': record.get("quantity_ask3"),
                    'datetime': record.get("datetime"),
                    'date': record.get("date"),
                }
            )
            try:
                session.execute(stmt)
                logger.info("Upserted record for symbol: {}", record["symbol_ticker"])
            except Exception as e:
                logger.error("Error upserting record for symbol {}: {}", record["symbol_ticker"], e)

        session.commit()
        logger.info("Upsert operation completed.")



data_from_redis = []
all_symbols = get_all_symbols()

for redis_key in all_symbols:
    hash_data = redis_client.hgetall(redis_key)

    if hash_data:
        hash_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in hash_data.items()}
        converted_data = convert_hash_data(hash_data)
        
        if converted_data:
            data_from_redis.append(converted_data)
            logger.info("Fetched data from Redis: {}", converted_data)
        else:
            logger.warning("Skipping invalid data for key: {}", redis_key)


upsert_update_quotes(data_from_redis)


