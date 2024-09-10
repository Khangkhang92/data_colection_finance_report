from models import Symbol, MajorHolder
from dotenv import load_dotenv
from common.db import ScopedSession
from datetime import datetime, date
import os
import requests
from loguru import logger
from const import MAJOR_HOLDER_MAPPING
from functools import lru_cache
from sqlalchemy import select, text, func
from sqlalchemy import inspect


def get_all_symbols(session):
    return session.execute(select(Symbol)).scalars().all()


def major_holder_by(symbol, session):
    load_dotenv()
    major_holder_url = os.getenv("MAJOR_HOLDERS_URL")
    full_url = f"{major_holder_url}/{symbol.ticker}/vi-vn"
    jwt_token = os.getenv("TOKEN")
    headers = {"JWTToken": jwt_token, "Content-Type": "application/json"}

    try:
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
        data = mapping_data(raw_data)
        save_major_holders(symbol, data, session)
    except requests.RequestException as e:
        logger.error(f"An error occurred while fetching data for {symbol.ticker}: {e}")


def save_major_holders(symbol, data, session):
    holders = [MajorHolder(symbol=symbol, **item) for item in data]
    session.bulk_save_objects(holders, return_defaults=False)
    session.commit()
    logger.info(f"Saved {len(holders)} major holders for symbol {symbol.ticker}")


def mapping_data(raw_data):
    data = []
    for item in raw_data:
        mapped_item = {}
        for key, value in MAJOR_HOLDER_MAPPING.items():
            if key in item:
                if value == 'date':
                    # Convert datetime string to date object
                    mapped_item[value] = datetime.strptime(item[key], '%Y-%m-%d').date()
                else:
                    mapped_item[value] = item[key]
        if mapped_item:
            data.append(mapped_item)
    return data


def clean_major_holders():
    with ScopedSession() as session:
        inspector = inspect(session.bind)
        if 'major_holder' in inspector.get_table_names():
            # Check if there's any data in the table
            count = session.query(func.count(MajorHolder.id)).scalar()
            if count > 0:
                truncate_stmt = text("TRUNCATE TABLE major_holder")
                session.execute(truncate_stmt)
                session.commit()
                logger.warning(
                    f"MajorHolder table has been truncated. {count} rows were deleted."
                )
                
                # Vacuum the major_holder table outside the transaction
                session.execute(text("COMMIT"))  # Ensure any open transaction is committed
                session.execute(text("VACUUM major_holder"))
                logger.info("MajorHolder table has been vacuumed.")
            else:
                logger.warning("MajorHolder table is empty. No truncation or vacuum needed.")
        else:
            logger.warning("MajorHolder table does not exist. Skipping truncation and vacuum.")


def fetch_major_holder():
    clean_major_holders()
    with ScopedSession() as session:
        all_symbols = get_all_symbols(session)
        for symbol in all_symbols:
            major_holder_by(symbol, session)


if __name__ == "__main__":
    fetch_major_holder()
