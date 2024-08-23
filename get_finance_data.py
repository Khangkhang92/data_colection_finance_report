from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import Symbol, Report, Data
from dotenv import load_dotenv
from common.db import ScopedSession
import os
import requests
from loguru import logger
from const import DISPLAY_NAME,REPORT_TYPE

logger.add("logs.log", rotation="1 week", retention="1 month", level="WARNING")


def fetch_financial_reports(symbol, report_type, year, quarter, count):
    load_dotenv()
    url = os.getenv("FiNANCE_URL")
    jwt_token = os.getenv("TOKEN")

    full_url = f"{url}/{symbol}/{report_type}/{year}/{quarter}/{count}/vi-vn"

    headers = {"JWTToken": f"{jwt_token}", "Content-Type": "application/json"}

    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data is not None:
              save_2_db(data, symbol, report_type)
            else:  
               logger.error(f"Can not fetch {REPORT_TYPE.get(report_type)} {year}/{quarter} for {symbol}")  
        else:
            logger.error(f"Error: Received response code {response.status_code}")
            logger.error(response.text)
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None


def _save_report(session, symbol, report_type, item, name, parent_id):
    if item.get("Level")  > 1  and  parent_id is None:
        logger.error(item.get("Name"), item.get("ParentID"))
    stmt = (
        insert(Report)
        .values(
            symbol_ticker=symbol,
            type=report_type,
            lever=item.get("Level"),
            parent_id=parent_id,
            name=name,
            display_name=DISPLAY_NAME.get(name, name),)
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
    children_item = update_data_and_get_child(data,item_id)
    if len(children_item) != 0: 
        for child in children_item:
            if child.get("Name") in ["- Nguyên giá", "- Giá trị hao mòn lũy kế"]:
                child["Name"] = child["Name"] + " " + "(" + DISPLAY_NAME.get(parent_name,parent_name).lower() + ")"
    return children_item

def save_finance_report(session, data, symbol, report_type, parent_id=None,children_item = None):
    items = children_item if children_item is not None else data

    for item in items:
        report_id = _save_report(
            session,
            symbol,
            report_type,
            item,
            item.get("Name", None),
            parent_id=parent_id,
        )
        if item.get("Values"):
            _save_data_entries(session, report_id, item.get("Values", []))
        children_item = _get_children_item(item, data)
   
        save_finance_report(
            session,data, symbol, report_type, parent_id=report_id,children_item = children_item
        )


def save_2_db(data, symbol, report_type):
    with ScopedSession() as session:
        save_finance_report(session, data, symbol, report_type)

def get_all_symbol():
    with ScopedSession() as session:
        stmt = select(Symbol.ticker)
        all_symbol = session.execute(stmt).scalars().all()
    return all_symbol    


# count = 15 
count = 60
start_year = 2024
start_quarter = 2



def fetch_all_data():
    all_symbol = get_all_symbol()
    logger.info("get list of symbol")

    start_index = all_symbol.index("ACV")

    for symbol in all_symbol[start_index:]:
        logger.warning(f'get Finance_report : {symbol}')
        for report_type in [1, 2, 3]:
            logger.info(f'get {REPORT_TYPE.get(report_type)} {symbol} ')
            fetch_financial_reports(
                symbol, report_type, start_year, start_quarter, count
            )
        logger.warning(f'get Finance_report Done!: {symbol}')    

fetch_all_data()

