from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import Symbol, Report, Data
from dotenv import load_dotenv
from common.db import ScopedSession
import os
import requests
from loguru import logger
from const import DISPLAY_NAME, REPORT_TYPE
import concurrent.futures
from functools import lru_cache

logger.add("logs.log", rotation="1 week", retention="1 month", level="WARNING")


@lru_cache(maxsize=None)
def get_env_variables():
    load_dotenv()
    return os.getenv("FINANCE_URL"), os.getenv("TOKEN")


def fetch_financial_reports(symbol, report_type, year, quarter, count):
    url, jwt_token = get_env_variables()
    full_url = f"{url}/{symbol}/{report_type}/{year}/{quarter}/{count}/vi-vn"
    headers = {"JWTToken": jwt_token, "Content-Type": "application/json"}

    try:
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            save_2_db(data, symbol, report_type)
        else:
            logger.warning(
                f"No data for {REPORT_TYPE.get(report_type)} {year}/{quarter} for {symbol}"
            )
    except requests.RequestException as e:
        logger.error(f"Error fetching data for {symbol}: {e}")


def _save_report(session, symbol, report_type, item, name, parent_id):
    if item.get("Level") > 1 and parent_id is None:
        logger.error(item.get("Name"), item.get("ParentID"))
    stmt = (
        insert(Report).values(
            symbol_ticker=symbol,
            type=report_type,
            lever=item.get("Level"),
            parent_id=parent_id,
            name=name,
            display_name=DISPLAY_NAME.get(name, name),
        )
        # ).on_conflict_do_update(
        #         index_elements=["name", "symbol_ticker"],
        #         set_={"parent_id": parent_id,
        #               "name" : item.get("Name")},
        #     )
        .on_conflict_do_nothing(index_elements=["name", "symbol_ticker"])
    )

    session.execute(stmt)
    session.commit()
    report_id = (
        session.query(Report.id).filter_by(name=name, symbol_ticker=symbol).scalar()
    )
    logger.info(name)
    return report_id


def _save_data_entries(session, report_id, values):
    for value in values:
        if value.get("Value", None) is None:
            continue
        stmt = (
            insert(Data)
            .values(
                report_id=report_id,
                value=value.get("Value", None),
                year=value.get("Year", None),
                quarter=value.get("Quarter", None),
            )
            .on_conflict_do_update(
                index_elements=["report_id", "quarter", "year"],
                set_={"value": value.get("Value")},
            )
        )
        session.execute(stmt)
    session.commit()


def update_data_and_get_child(data, item_id):
    children = []
    new_data = []

    for item in data:
        if item.get("ParentID") == item_id:
            children.append(item)
        else:
            new_data.append(item)
    data[:] = new_data

    return children


def _get_children_item(item, data):
    item_id = item.get("ID")
    parent_name = item.get("Name")
    children_item = update_data_and_get_child(data, item_id)
    if len(children_item) != 0:
        for child in children_item:
            if child.get("Name") in ["- Nguyên giá", "- Giá trị hao mòn lũy kế"]:
                child["Name"] = (
                    child["Name"]
                    + " "
                    + "("
                    + DISPLAY_NAME.get(parent_name, parent_name).lower()
                    + ")"
                )
    return children_item


def save_finance_report(
    session, data, symbol, report_type, parent_id=None, children_item=None
):
    items = children_item or data
    for item in items:
        report_id = _save_report(
            session, symbol, report_type, item, item.get("Name"), parent_id
        )
        if item.get("Values"):
            _save_data_entries(session, report_id, item.get("Values", []))
        children_item = _get_children_item(item, data)
        save_finance_report(
            session,
            data,
            symbol,
            report_type,
            parent_id=report_id,
            children_item=children_item,
        )


def save_2_db(data, symbol, report_type):
    with ScopedSession() as session:
        save_finance_report(session, data, symbol, report_type)


@lru_cache(maxsize=1)
def get_all_symbols():
    with ScopedSession() as session:
        return session.execute(select(Symbol.ticker)).scalars().all()


def fetch_symbol_data(symbol):
    logger.warning(f"Fetching Finance_report: {symbol}")
    for report_type in [1, 2, 3]:
        logger.info(f"Fetching {REPORT_TYPE.get(report_type)} for {symbol}")
        fetch_financial_reports(symbol, report_type, start_year, start_quarter, count)
    logger.warning(f"Finished fetching Finance_report: {symbol}")


def fetch_all_data():
    all_symbols = get_all_symbols()
    logger.info("Retrieved list of symbols")

    start_index = all_symbols.index("ACV")
    symbols_to_fetch = all_symbols[start_index:]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(fetch_symbol_data, symbols_to_fetch)


if __name__ == "__main__":
    count = 60
    start_year = 2024
    start_quarter = 2
    fetch_all_data()


"""
Logic Flow:
                                +-------------------+
                                |   fetch_all_data  |
                                +-------------------+
                                          |
                                          v
                            +-------------------------------+
                            |        get_all_symbols        |
                            | (cached list of all symbols)  |
                            +-------------------------------+
                                          |
                                          v
                            +-------------------------------+
                            |    ThreadPoolExecutor.map     |
                            | (concurrent execution)        |
                            +-------------------------------+
                                          |
                                          v
                            +-------------------------------+
                            |      fetch_symbol_data        |
                            | (for each symbol)             |
                            +-------------------------------+
                                          |
                                          v
                    +-----------------------------------------------+
                    |            fetch_financial_reports            |
                    | (for each report type: 1, 2, 3)               |
                    +-----------------------------------------------+
                                          |
                                          v
                    +-----------------------------------------------+
                    |               API Request                     |
                    | (get data from external financial service)    |
                    +-----------------------------------------------+
                                          |
                                          v
                                +-----------------+
                                |    save_2_db    |
                                +-----------------+
                                          |
                                          v
                            +-------------------------------+
                            |      save_finance_report      |
                            | (recursive saving of data)    |
                            +-------------------------------+
                                          |
                                          v
                    +-----------------------------------------------+
                    |               _save_report                    |
                    | (save report info to database)                |
                    +-----------------------------------------------+
                                          |
                                          v
                    +-----------------------------------------------+
                    |             _save_data_entries                |
                    | (save associated data to database)            |
                    +-----------------------------------------------+
                                          |
                                          v
                    +-----------------------------------------------+
                    |            _get_children_item                 |
                    | (process child items for recursive saving)    |
                    +-----------------------------------------------+
"""
