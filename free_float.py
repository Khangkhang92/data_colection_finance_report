from sqlalchemy import  insert
from models import Market
from common.db import ScopedSession
import os
from loguru import logger
from getdata.base import Base




def get_subsidiaries(symbol):
    SUBSIDIARIES = os.getenv("SUBSIDIARIES")
    if not SUBSIDIARIES:
        logger.error("SUBSIDIARIES environment variable is not set.")
        return
    FULL_URL = f"{SUBSIDIARIES}/{symbol}/fundamental"
    try:
        base_call_api = Base(FULL_URL)
        raw_data = base_call_api.fetch_posts()
        mapping_data(raw_data,symbol)
    except Exception as e:
        logger.error(f"Failed to fetch holders for {symbol}: {e}")
        return


def mapping_data(raw_data,symbol):
    symbol_info_dict = {
            'symbol_ticker': symbol,
            "shares_out_standing": raw_data.get("sharesOutstanding"),
            "market_capitalization": raw_data.get("marketCap"),
            "free_shares": raw_data.get("freeShares"),
           
    }

    logger.info("Get all symbol is ok!")
    with ScopedSession() as session:
        save_2_db(session, symbol_info_dict)


def save_2_db(session, info):
    try:
       
        stmt = (
                insert(Market).values(
                    symbol_ticker=symbol,
                    shares_out_standing=info["shares_out_standing"],
                    market_capitalization=info["market_capitalization"],
                    free_shares=info["free_shares"],
                )
            )
        session.execute(stmt)
        session.commit()
        logger.info("Successfully updated records in the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"An error occurred while updating records: {e}")


base = Base()
all_symbols = base.get_all_symbols()


for symbol in all_symbols:
    get_subsidiaries(symbol)
    logger.info(f"save data for {symbol}")