import os
import requests
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv
from loguru import logger
from models import Symbol
from common.db import ScopedSession
from baseCallApi import baseCallAPI


def fetch_allsymbol():
    load_dotenv()
    url = os.getenv("ALL_SYMBOL_URL2")
    jwt_token = os.getenv("TOKEN")
    basecallapi = baseCallAPI(url, jwt_token)
    raw_data = basecallapi.fetch_posts()
    mapping_exchange(raw_data)


def mapping_exchange(raw_data):
    symbol_info_list = [
        {
            "ticker": data.get("symbol"),
            "company_name": data.get("name"),
            "exchange": data.get("exchange"),
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
