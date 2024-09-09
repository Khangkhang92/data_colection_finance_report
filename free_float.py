from sqlalchemy import select, update, and_
from models import Market
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
    headers = {"JWTToken": jwt_token, "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
        mapping_data(raw_data)
    except requests.RequestException as e:
        logger.error(f"An error occurred while fetching data: {e}")


def mapping_data(raw_data):
    symbol_info_dict = {
        data["Symbol"]: {
            "date": (
                datetime.fromisoformat(data.get("Date")).strftime("%Y-%m-%d")
                if data.get("Date")
                else None
            ),
            "shares_out_standing": data.get("SharesOutstanding"),
            "market_capitalization": data.get("MarketCapitalization"),
            "free_shares": data.get("FreeShares"),
        }
        for data in raw_data
    }

    logger.info("Get all symbol is ok!")
    with ScopedSession() as session:
        save_2_db(session, symbol_info_dict)


def save_2_db(session, symbol_info_dict):
    try:
        for symbol, info in symbol_info_dict.items():
            stmt = (
                update(Market)
                .where(
                    and_(Market.symbol_ticker == symbol, Market.date == info["date"])
                )
                .values(
                    {
                        Market.shares_out_standing: info["shares_out_standing"],
                        Market.market_capitalization: info["market_capitalization"],
                        Market.free_shares: info["free_shares"],
                    }
                )
            )
            result = session.execute(stmt)
        session.commit()
        logger.info("Successfully updated records in the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"An error occurred while updating records: {e}")


if __name__ == "__main__":
    fetch_allsymbol()
