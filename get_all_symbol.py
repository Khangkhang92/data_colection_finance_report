from sqlalchemy.dialects.postgresql import insert
from models import Symbol
from dotenv import load_dotenv
from common.db import ScopedSession
import os
import requests
from loguru import logger


def fetch_allsymbol():
    load_dotenv()
    url = os.getenv("ALL_SYMBOL_URL")
    jwt_token = os.getenv("TOKEN")
    headers = {"JWTToken": f"{jwt_token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            raw_data = response.json()
            mapping_exchange(raw_data)

        else:
            logger.error(f"Error: Received response code {response.status_code}")
            logger.error(response.text)
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def mapping_exchange(raw_data):
    symbol_info_list = []
    convert = {"HOSTC": "HSX", "HASTC": "HNX", "UPCOM": "UPCOM"}
    for data in raw_data:
        symbol_info_list.append(
            {
                "ticker": data.get("<Symbol>k__BackingField", None),
                "company_name": data.get("<Name>k__BackingField", None),
                "exchange": convert[data.get("<Exchange>k__BackingField", None)],
                "industry": data.get("<Industry>k__BackingField", None),
                "sector": data.get("<Sector>k__BackingField", None),
            }
        )
    logger.info(f"get all symbol is ok!")
    with ScopedSession() as session:
        save_2_db(Symbol, session, symbol_info_list)


def save_2_db(model, session, values_to_insert):

    for item in values_to_insert:
        stmt = insert(model).values(**item)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={
                "exchange": stmt.excluded.exchange,
                "company_name": stmt.excluded.company_name,
            },
        )
        session.execute(stmt)
        ticker = item.get("ticker")
        logger.info(f"{ticker} is store")


fetch_allsymbol()
