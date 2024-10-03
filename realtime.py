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

colorama.init(autoreset=True)


logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

logger.add(
    logs_dir / "realtime_error.log", rotation="1 day", retention="7 days", level="ERROR"
)

load_dotenv()

# redis_client = redis.Redis.from_url(os.getenv("REDIS"))
redis_client = redis.Redis(host="localhost", port=6379, db=0)


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

    morning_start = parse_time("MORNING_START", "8:55")
    morning_end = parse_time("MORNING_END", "11:31")
    afternoon_start = parse_time("AFTERNOON_START", "12:40")
    afternoon_end = parse_time("AFTERNOON_END", "15:05")

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
    for quote_data in quote_data_list[0]:
        symbol = await get_symbol(quote_data["Symbol"], session)
        if symbol is None:
            logger.warning(f"Symbol not found: {quote_data['Symbol']}")
            continue

        # Prepare new data to completely overwrite the existing data
        new_data = {
            UPDATE_QUOTE_MAPPING.get(k, k): v
            for k, v in quote_data.items()
            if UPDATE_QUOTE_MAPPING.get(k, k) in UpdateQuote.__table__.columns
        }

        # Update datetime and date fields
        if "date" in new_data:
            new_data["datetime"] = (
                datetime.datetime.fromisoformat(new_data["date"][:-1])
                + datetime.timedelta(hours=7)
            ).isoformat()
            new_data["date"] = new_data["date"].split("T")[0]

        # Store the new quote data in Redis as a hash
        redis_key = f"{symbol.ticker}"
        list_key = f"{symbol.ticker}:list"
        stream_key = f"{symbol.ticker}:stream"  # Define the stream key

        lua_script = """
            local hash_key = KEYS[1]
            local list_key = KEYS[2]
            local stream_key = KEYS[3]
            
            local hash_data = redis.call('HGETALL', hash_key)
            local json_data = cjson.encode(hash_data)
            
            -- Push to list
            redis.call('RPUSH', list_key, json_data)
            
            -- Push to stream
            redis.call('XADD', stream_key, '*', 'data', json_data)
            
            return json_data
        """

        redis_client.eval(lua_script, 3, redis_key, list_key, stream_key)

        logger.info(
            f"{Fore.GREEN}Realtime data : {Fore.YELLOW}{symbol.ticker}{Style.RESET_ALL}"
        )


async def get_all_data_for_symbol(redis, symbol):
    list_key = f"price_history:{symbol.ticker}"

    # Retrieve all data from the list
    all_data = await redis.lrange(list_key, 0, -1)

    # Deserialize from JSON if needed
    all_data = [json.loads(data) for data in all_data]

    return all_data


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
