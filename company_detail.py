from models import MajorHolder, Subsidiaries
from common.db import ScopedSession
import os
from loguru import logger
from getdata.base import Base


def get_holder(symbol):
    HOLDER_URL = os.getenv("HOLDER")
    if not HOLDER_URL:
        logger.error("HOLDER environment variable is not set.")
        return
    FULL_URL = f"{HOLDER_URL}/{symbol}/holders"

    try:
        base_call_api = Base(FULL_URL)
        list_holder = base_call_api.fetch_posts()
    except Exception as e:
        logger.error(f"Failed to fetch holders for {symbol}: {e}")
        return

    major_holder_list = []

    for holder in list_holder:
        try:
            holder["is_organization"] = holder.pop("isOrganization", False)
            holder["is_foreigner"] = holder.pop("isForeigner", False)
            holder["is_foundation"] = holder.pop("isFounder", False)
            holder["symbol_ticker"] = symbol
            holder.pop("majorHolderID")
            holder.pop("individualHolderID")
            holder.pop("institutionHolderID")
            holder.pop("institutionHolderSymbol")
            holder.pop("institutionHolderExchange")
            major_holder_list.append(MajorHolder(**holder))
        except KeyError as e:
            logger.warning(f"Missing expected key in holder data: {e}")

    try:
        with ScopedSession() as session:
            session.add_all(major_holder_list)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to update database for {symbol}: {e}")


def get_subsidiaries(symbol, all_symbols):
    SUBSIDIARIES = os.getenv("SUBSIDIARIES")
    if not SUBSIDIARIES:
        logger.error("SUBSIDIARIES environment variable is not set.")
        return
    FULL_URL = f"{SUBSIDIARIES}/{symbol}/subsidiaries"

    try:
        base_call_api = Base(FULL_URL)
        list_subsidiaries = base_call_api.fetch_posts()
    except Exception as e:
        logger.error(f"Failed to fetch holders for {symbol}: {e}")
        return

    major_subsidiaries_list = []
    if len(major_subsidiaries_list) == 0:
        return

    for subsidiaries in list_subsidiaries:
        try:
            subsidiaries.pop("institutionID", False)
            subsidiaries["symbol_ticker"] = symbol
            subsidiaries["company_name"] = subsidiaries.pop("companyName", False)
            subsidiaries["short_name"] = subsidiaries.pop("shortName", False)
            subsidiaries["international_name"] = subsidiaries.pop(
                "internationalName", False
            )
            subsidiaries["company_profile"] = subsidiaries.pop("companyProfile", False)
            subsidiaries["is_listed"] = subsidiaries.pop("isListed", False)
            subsidiaries["charter_capital"] = subsidiaries.pop("charterCapital", False)
            subsidiaries["sub_symbol"] = subsidiaries.pop("symbol", False)
            major_subsidiaries_list.append(Subsidiaries(**subsidiaries))
        except KeyError as e:
            logger.warning(f"Missing expected key in subsidiaries data: {e}")

    try:
        with ScopedSession() as session:
            session.add_all(major_subsidiaries_list)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to update database for {symbol}: {e}")


base = Base()
all_symbols = base.get_all_symbols()
with ScopedSession() as session:
    # session.query(MajorHolder).delete()
    session.query(Subsidiaries).delete()
    session.commit()

for symbol in all_symbols:
    # get_holder(symbol)
    # logger.info(f"save holder for {symbol}")
    get_subsidiaries(symbol, all_symbols)
    logger.info(f"save subsidiaries for {symbol}")
