from models import MarketMention
from common.db import ScopedSession
import os
from dotenv import load_dotenv
from getdata.base import Base
from datetime import date
from loguru import logger

periods = ["today", "weekly", "monthly"]

load_dotenv()
MARKET_MENTION_URL = os.getenv("MARKET_MENTION")
base_call_api = Base(MARKET_MENTION_URL)
today = date.today()

base = Base()
all_symbols = base.get_all_symbols()

with ScopedSession() as session:
    for period in periods:
        logger.info(f"get market mention {period}")
        market_mention_list = []
        FULL_URL = f"{MARKET_MENTION_URL}/{period}"
        base_call_api.base_url = FULL_URL
        list_symbol = base_call_api.fetch_posts({"limit": 3000})
        market_mention_lookup = {}
        market_mentions = (
            session.query(MarketMention).filter(MarketMention.date == today).all()
        )
        if market_mentions:
            market_mention_lookup = {
                mention.symbol_ticker: mention for mention in market_mentions
            }

        for symbol in list_symbol:
            symbol_to_find = symbol["symbol"]
            if symbol_to_find in all_symbols:
                market_mention = market_mention_lookup.get(symbol_to_find)
            else:
                continue

            if market_mention:
                if period == "today":
                    market_mention.day = symbol["points"]
                    market_mention.day_color = symbol["color"]
                if period == "weekly":
                    market_mention.week = symbol["points"]
                    market_mention.week_color = symbol["color"]
                if period == "monthly":
                    market_mention.month = symbol["points"]
                    market_mention.month_color = symbol["color"]
                market_mention.date = today
            else:
                market_mention = MarketMention(symbol_ticker=symbol_to_find, date=today)
                if period == "today":
                    market_mention.day = symbol["points"]
                    market_mention.day_color = symbol["color"]
                if period == "weekly":
                    market_mention.week = symbol["points"]
                    market_mention.week_color = symbol["color"]
                if period == "monthly":
                    market_mention.month = symbol["points"]
                    market_mention.month_color = symbol["color"]
            market_mention_list.append(market_mention)

        session.add_all(market_mention_list)
        session.commit()
        logger.success(f"{period} is ok")
