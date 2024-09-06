import os
import requests
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv
from loguru import logger
from models import Symbol
from common.db import ScopedSession

def fetch_allsymbol():
    load_dotenv()
    url = os.getenv("ALL_SYMBOL_URL")
    jwt_token = os.getenv("TOKEN")
    headers = {"JWTToken": jwt_token, "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
        mapping_exchange(raw_data)
    except requests.RequestException as e:
        logger.error(f"An error occurred: {e}")

def mapping_exchange(raw_data):
    convert = {"HOSTC": "HSX", "HASTC": "HNX", "UPCOM": "UPCOM"}
    symbol_info_list = [
        {
            "ticker": data.get("<Symbol>k__BackingField"),
            "company_name": data.get("<Name>k__BackingField"),
            "exchange": convert.get(data.get("<Exchange>k__BackingField")),
            "industry": data.get("<Industry>k__BackingField"),
            "sector": data.get("<Sector>k__BackingField"),
        }
        for data in raw_data
    ]
    logger.info("Get all symbols completed successfully")
    
    with ScopedSession() as session:
        save_2_db(Symbol, session, symbol_info_list)

def save_2_db(model, session, values_to_insert):
    stmt = insert(model).values(values_to_insert)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker"],
        set_={
            "exchange": stmt.excluded.exchange,
            "company_name": stmt.excluded.company_name,
        },
    )
    session.execute(stmt)
    logger.info(f"Stored {len(values_to_insert)} symbols")

if __name__ == "__main__":
    fetch_allsymbol()
