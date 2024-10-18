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

# Add this near the top of the file, after other imports
colorama.init(autoreset=True)

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logger to write to file
logger.add(
    logs_dir / "realtime_error.log", rotation="1 day", retention="7 days", level="ERROR"
)

load_dotenv()


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


async def process_update_quote(quote_data_list, session):
    for quote_data in quote_data_list[0]:
        symbol = await session.execute(
            select(Symbol).filter_by(ticker=quote_data["Symbol"])
        )
        symbol = symbol.scalar_one_or_none()

        if symbol is None:
            logger.warning(f"Symbol not found: {quote_data['Symbol']}")
            continue

        update_quote = await session.execute(
            select(UpdateQuote).filter_by(symbol_ticker=symbol.ticker)
        )
        update_quote = update_quote.scalar_one_or_none()

        if update_quote is None:
            update_quote = UpdateQuote(symbol_ticker=symbol.ticker)
            session.add(update_quote)

        filtered_data = {
            UPDATE_QUOTE_MAPPING.get(k, k): v
            for k, v in quote_data.items()
            if UPDATE_QUOTE_MAPPING.get(k, k) in UpdateQuote.__table__.columns
        }

        # Convert date string to date and datetime objects
        if "date" in filtered_data and filtered_data["date"] is not None:
            dt = datetime.datetime.fromisoformat(
                filtered_data["date"].replace("Z", "+00:00")
            )
            filtered_data["date"] = dt.date()
            filtered_data["datetime"] = dt

        for key, value in filtered_data.items():
            setattr(update_quote, key, value)

        logger.info(
            f"{Fore.GREEN}Realtime data : {Fore.YELLOW}{update_quote.symbol_ticker}{Style.RESET_ALL}"
        )
        await session.flush()


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
                            await asyncio.wait_for(pong, timeout=10)
                            logger.info(
                                f"{Fore.GREEN}Connection is still alive{Style.RESET_ALL}"
                            )
                        except:
                            logger.error(
                                f"{Fore.RED}Ping failed. Reconnecting...{Style.RESET_ALL}"
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
