from getdata.base import Base
from loguru import logger
import os
from common.db import ScopedSession
from sqlalchemy.dialects.postgresql import insert
from models import SessionQuote
from datetime import datetime


BUY_SELL_DURING_SESSION_URL = os.getenv("BUY_SELL_DURING_SESSION")
base_call_api = Base(BUY_SELL_DURING_SESSION_URL)
all_symbols = base_call_api.get_all_symbols()
del base_call_api.headers["Authorization"]


def tranfer_data(transaction):
    return {
        "symbol_ticker": transaction.get("Symbol"),
        "side": transaction.get("Side"),
        "match_price": transaction.get("Price"),
        "volume": transaction.get("Volume"),
        "total_volume": transaction.get("TotalVolume"),
        # "date" : datetime.fromisoformat(transaction.get("Date").replace("Z", "+00:00")).date(),
        "datetime": transaction.get("Date"),
    }


def upsert_transactions_quotes(symbol_transactions):

    if not symbol_transactions:
        logger.warning("No data to upsert.")
        return

    with ScopedSession() as session:
        for transaction in symbol_transactions:
            data = tranfer_data(transaction)
            stmt = (
                insert(SessionQuote)
                .values(**data)
                .on_conflict_do_update(
                    index_elements=[
                        "symbol_ticker",
                        "datetime",
                    ],  # Unique constraint columns
                    set_={
                        "side": data.get("side"),
                        "match_price": data.get("match_price"),
                        "volume": data.get("volume"),
                        "total_volume": data.get("total_volume"),
                        # 'date': data.get("date"),
                        "datetime": data.get("datetime"),
                    },
                )
            )
            try:
                session.execute(stmt)
            except Exception as e:
                logger.error(e)
        session.commit()
        logger.success(f"transactions of {symbol}")


# start_index = all_symbols.index("VN30")
# symbols_to_fetch = all_symbols[start_index:]

for symbol in all_symbols:
    symbol_transactions = base_call_api.fetch_posts({"symbol": symbol})
    logger.info(f"get data for {symbol} ok")
    upsert_transactions_quotes(symbol_transactions)
    logger.success(f"transactions of {symbol}")
