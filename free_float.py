from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, and_
from models import Symbol,Market
from dotenv import load_dotenv
from common.db import ScopedSession
from datetime import datetime
import os
import requests
from loguru import logger



def fetch_allsymbol():
    load_dotenv()
    url = os.getenv("LASTEST_FINANCIAL_INFO_URL")
    jwt_token = os.getenv("TOKEN")
    headers = {"JWTToken": f"{jwt_token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            raw_data = response.json()
            mapping_data(raw_data)

        else:
            logger.error(f"Error: Received response code {response.status_code}")
            logger.error(response.text)
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None



def mapping_data(raw_data):
    symbol_info_dict = {}
    for data in raw_data:
        symbol_info_dict[data.get("Symbol")] = {
                "date" : datetime.fromisoformat(data.get("Date")).strftime('%Y-%m-%d') if data.get("Date") else None,
                "shares_out_standing": data.get("SharesOutstanding", None),
                "market_capitalization": data.get("MarketCapitalization", None),
                "free_shares": data.get("FreeShares", None),
            }
        
    logger.info(f"get all symbol is ok!")
    with ScopedSession() as session:
        save_2_db(session, symbol_info_dict)


def save_2_db(session, symbol_info_dict):
    try:
            stmt = select(Market).where(Market.date == '2024-09-04')
            existing_items = session.execute(stmt).scalars().all()
            for item in existing_items:
                item.shares_out_standing = symbol_info_dict.get(item.symbol_ticker).get("shares_out_standing", item.shares_out_standing)
                item.market_capitalization = symbol_info_dict.get(item.symbol_ticker).get("market_capitalization", item.market_capitalization)
                item.free_shares = symbol_info_dict.get(item.symbol_ticker).get("free_shares", item.free_shares)
                try:
                    session.flush()  # Ensure that the changes are sent to the database
                    session.commit()  # Commit each change individually
                    logger.info(f"Successfully updated record with symbol {item.symbol_ticker} in the database.")
                except Exception as e:
                    session.rollback()  # Rollback in case of an error
                    logger.error(f"An error occurred while updating record with symbol {item.symbol_ticker}: {e}")

    except Exception as e:
        logger.error(f"An error occurred while processing the records: {e}")


fetch_allsymbol()
