from sqlalchemy.dialects.postgresql import insert
from models import  Report, Data
from common.db import ScopedSession
import os
from loguru import logger
from const import DISPLAY_NAME, REPORT_TYPE
from getdata.base import Base


logger.add("logs.log", rotation="1 week", retention="1 month", level="WARNING")


FiNANCE_URL2 = os.getenv("FiNANCE_URL2")
base_call_api = Base(FiNANCE_URL2)


def _save_report(session, symbol, report_type, item, name, parent_id):
    if item.get("level") > 1 and parent_id is None:
        logger.error(item.get("name"), item.get("parentID"))
    stmt = (
        insert(Report).values(
            symbol_ticker=symbol,
            type=report_type,
            lever=item.get("level"),
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


def update_data_and_get_child(data, item_id):
    children = []
    new_data = []

    for item in data:
        if item.get("parentID") == item_id:
            children.append(item)
        else:
            new_data.append(item)
    data[:] = new_data # update data
    return children


def _get_children_item(item, data):
    item_id = item.get("id")
    parent_name = item.get("name")
    children_item = update_data_and_get_child(data, item_id)
    if len(children_item) != 0:
        for child in children_item:
            if child.get("name") in ["- Nguyên giá", "- Giá trị hao mòn lũy kế"]:
                child["name"] = (
                    child["name"]
                    + " "
                    + "("
                    + DISPLAY_NAME.get(parent_name, parent_name).lower()
                    + ")"
                )
    return children_item


def _save_data_entries(session, report_id, values):
    for value in values:
        if value.get("value", None) is None:
            continue
        stmt = (
            insert(Data)
            .values(
                report_id=report_id,
                value=value.get("value", None),
                year=value.get("year", None),
                quarter=value.get("quarter", None),
            )
            .on_conflict_do_update(
                index_elements=["report_id", "quarter", "year"],
                set_={"value": value.get("value")},
            )
        )
        session.execute(stmt)
    session.commit()


def save_finance_report(
    session, data, symbol, report_type, parent_id=None, children_item=None
):
    items = children_item if children_item is not None else data
    for item in items:
        report_id = _save_report(
            session, symbol, report_type, item, item.get("name"), parent_id
        )
        if item.get("values"):
            _save_data_entries(session, report_id, item.get("values", []))
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

all_symbol = base_call_api.get_all_symbols()
logger.info("Retrieved list of symbols")
start_index = all_symbol.index("A32")
symbols_to_fetch = all_symbol[start_index:]
for symbol in symbols_to_fetch:
    for report_type in (1,2):
        logger.info(f"Fetching {REPORT_TYPE.get(report_type)} for {symbol}")
        params = {
            "type" : report_type,
            "year" : 2024,
            "quarter"  : 3,
            "limit" : 1
        }
        base_call_api.base_url = f"{FiNANCE_URL2}/{symbol}/full-financial-reports"
        data_list = base_call_api.fetch_posts(params)
        if data_list:
          save_2_db(data_list, symbol, report_type)