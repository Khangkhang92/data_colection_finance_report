import os
import asyncio
import websockets
import json
from loguru import logger
from dotenv import load_dotenv
from models import Symbol, UpdateQuote
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import datetime
from const import UPDATE_QUOTE_MAPPING
import colorama
from colorama import Fore, Style
from pathlib import Path
from functools import lru_cache  
import redis  

redis_client = redis.Redis.from_url("redis://localhost:6379/0")
colorama.init(autoreset=True)


logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

logger.add(
    logs_dir / "realtime_error.log", rotation="1 day", retention="7 days", level="ERROR"
)

load_dotenv()


class UpdateQuoteData:
    def __init__(
        self,
        symbol_ticker=None,
        price_current=None,
        price_last=None,
        price_high=None,
        price_low=None,
        price_open=None,
        price_close=None,
        price_average=None,
        price_change=None,
        price_percent_change=None,
        volume=None,
        total_active_buy_volume=None,
        total_active_sell_volume=None,
        buy_foreign_quantity=None,
        buy_foreign_value=None,
        sell_foreign_quantity=None,
        sell_foreign_value=None,
        current_foreign_room=None,
        total_volume=None,
        total_value=None,
        date=None,
        price_bid1=None,
        quantity_bid1=None,
        price_bid2=None,
        quantity_bid2=None,
        price_bid3=None,
        quantity_bid3=None,
        price_ask1=None,
        quantity_ask1=None,
        price_ask2=None,
        quantity_ask2=None,
        price_ask3=None,
        quantity_ask3=None,
        datetime=None,
    ):  
        self.symbol_ticker = symbol_ticker
        self.price_current = price_current
        self.price_last = price_last
        self.price_high = price_high
        self.price_low = price_low
        self.price_open = price_open
        self.price_close = price_close
        self.price_average = price_average
        self.price_change = price_change
        self.price_percent_change = price_percent_change
        self.volume = volume
        self.total_active_buy_volume = total_active_buy_volume
        self.total_active_sell_volume = total_active_sell_volume
        self.buy_foreign_quantity = buy_foreign_quantity
        self.buy_foreign_value = buy_foreign_value
        self.sell_foreign_quantity = sell_foreign_quantity
        self.sell_foreign_value = sell_foreign_value
        self.current_foreign_room = current_foreign_room
        self.total_volume = total_volume
        self.total_value = total_value
        self.price_bid1 = price_bid1
        self.quantity_bid1 = quantity_bid1
        self.price_bid2 = price_bid2
        self.quantity_bid2 = quantity_bid2
        self.price_bid3 = price_bid3
        self.quantity_bid3 = quantity_bid3
        self.price_ask1 = price_ask1
        self.quantity_ask1 = quantity_ask1
        self.price_ask2 = price_ask2
        self.quantity_ask2 = quantity_ask2
        self.price_ask3 = price_ask3
        self.quantity_ask3 = quantity_ask3
        self.date = date
        self.datetime = datetime
        

def get_url():
    user = os.getenv("USERDB")
    password = os.getenv("PASSWORD")
    server = os.getenv("SERVER")
    port = os.getenv("PORT")
    db = os.getenv("DB")
    db_url = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"
    print(db_url)
    return db_url


# Constants
SOCKET = os.getenv("SOCKET")
CONNECTION_TOKEN = os.getenv("CONNECTION_TOKEN")
TOKEN = os.getenv("TOKEN")
FULLURL = f"{SOCKET}&connectionToken={CONNECTION_TOKEN}&Token={TOKEN}"

# Create a global async session factory
engine = create_async_engine(get_url())
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def is_trading_time():
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False

    def parse_time(env_var, default):
        time_str = os.getenv(env_var, default)
        hour, minute = map(int, time_str.split(":"))
        return hour, minute

    morning_start = parse_time("MORNING_START", "9:00")
    morning_end = parse_time("MORNING_END", "11:30")
    afternoon_start = parse_time("AFTERNOON_START", "13:00")
    afternoon_end = parse_time("AFTERNOON_END", "15:00")

    current_time = now.hour * 60 + now.minute
    morning_start_minutes = morning_start[0] * 60 + morning_start[1]
    morning_end_minutes = morning_end[0] * 60 + morning_end[1]
    afternoon_start_minutes = afternoon_start[0] * 60 + afternoon_start[1]
    afternoon_end_minutes = afternoon_end[0] * 60 + afternoon_end[1]

    if (morning_start_minutes <= current_time < morning_end_minutes) or (
        afternoon_start_minutes <= current_time < afternoon_end_minutes
    ):
        return True

    return False


@lru_cache(maxsize=None)
async def get_symbol(ticker, session):
    result = await session.execute(select(Symbol).filter_by(ticker=ticker))
    return result.scalar_one_or_none()


async def process_update_quote(quote_data_list, session):
    all_quotes_dict = {}

    for quote_data in quote_data_list[0]:
        symbol = await get_symbol(quote_data["Symbol"], session)
        if symbol is None:
            logger.warning(f"Symbol not found: {quote_data['Symbol']}")
            continue

        if symbol.ticker not in all_quotes_dict:
            update_quote = UpdateQuoteData(symbol_ticker=symbol.ticker)

            filtered_data = {
                UPDATE_QUOTE_MAPPING.get(k, k): v
                for k, v in quote_data.items()
                if UPDATE_QUOTE_MAPPING.get(k, k) in UpdateQuote.__table__.columns
            }

            # Update the in-memory object
            for key, value in filtered_data.items():
                setattr(update_quote, key, value)

            logger.info(
                f"{Fore.GREEN}Realtime data : {Fore.YELLOW}{update_quote.symbol_ticker}{Style.RESET_ALL}"
            )
            # update_quote.symbol = symbol.ticker
            update_quote.datetime = (
                datetime.datetime.fromisoformat(update_quote.date[:-1])
                + datetime.timedelta(hours=7)
            ).isoformat()
            update_quote.date = update_quote.date.split("T")[0]
            all_quotes_dict[symbol.ticker] = update_quote
            print(all_quotes_dict[symbol.ticker].__dict__)
            # Prepare the data to save
            quote_data = all_quotes_dict[symbol.ticker].__dict__
            quote_data = {k: v if v is not None else "null" for k, v in all_quotes_dict[symbol.ticker].__dict__.items()}  # Convert None to "null"
            stream_key = "quote_stream"  # Define the stream key
            redis_client.xadd(stream_key, quote_data, id='*')  # '*' generates a unique ID

async def process_message(message, session):
    data = json.loads(message)
    if "M" in data and data["M"]:
        method = data["M"][0]["M"]
        if method == "updateQuote":
            await process_update_quote(
                data["M"][0]["A"], session
            )  # Pass the entire list
        else:
            logger.info(f"Skipped unknown method: {method}")
    elif "C" in data and "S" in data and "M" in data and not data["M"]:
        # Skip connection update messages
        return
    elif "C" in data:
        logger.info(f"Received connection message: {data['C']}")
    else:
        logger.info(f"Skipped message: {data}")


async def receive_data_from_websocket():
    while True:  # Outer loop for reconnection
        try:
            async with websockets.connect(FULLURL) as websocket:
                logger.info(f"{Fore.GREEN}Connected to websocket{Style.RESET_ALL}")
                while is_trading_time():
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(), timeout=30
                        )  # 30-second timeout
                        async with AsyncSessionFactory() as session:
                            async with session.begin():
                                await process_message(message, session)
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"{Fore.YELLOW}No data received for 30 seconds. Checking connection...{Style.RESET_ALL}"
                        )
                        try:
                            pong = await websocket.ping()
                            await asyncio.wait_for(
                                pong, timeout=10
                            )  # Ensure pong is awaited only once
                            logger.info(
                                f"{Fore.GREEN}Connection is still alive{Style.RESET_ALL}"
                            )
                        except Exception as ping_error:  # Catch specific exceptions
                            logger.error(
                                f"{Fore.RED}Ping failed: {ping_error}. Reconnecting...{Style.RESET_ALL}"
                            )
                            break  # Exit inner loop to reconnect

                logger.info(
                    f"{Fore.YELLOW}Outside trading hours. Stopping script.{Style.RESET_ALL}"
                )
                return  # Exit the function when outside trading hours

        except websockets.exceptions.ConnectionClosed:
            logger.error(
                f"{Fore.RED}WebSocket connection closed. Attempting to reconnect...{Style.RESET_ALL}"
            )
        except Exception as e:
            logger.error(
                f"{Fore.RED}An error occurred: {e}. Attempting to reconnect...{Style.RESET_ALL}"
            )

        await asyncio.sleep(5)  # Wait for 5 seconds before attempting to reconnect


if __name__ == "__main__":
    if is_trading_time():
        asyncio.run(receive_data_from_websocket())
    else:
        logger.info("Not within trading hours. Script will not run.")
