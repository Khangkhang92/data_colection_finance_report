import os
import asyncio
import websockets
import json
from loguru import logger
from dotenv import load_dotenv
from models import Symbol, UpdateQuote
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import datetime
from const import UPDATE_QUOTE_MAPPING

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
    
    if (9 <= now.hour < 11) or (now.hour == 11 and now.minute <= 30) or (13 <= now.hour < 15):
        return True
    
    return False

async def process_update_quote(quote_data_list, session):
    for quote_data in quote_data_list[0]:
        symbol = await session.execute(select(Symbol).filter_by(ticker=quote_data["Symbol"]))
        symbol = symbol.scalar_one_or_none()
        
        if symbol is None:
            logger.warning(f"Symbol not found: {quote_data['Symbol']}")
            continue
        
        update_quote = await session.execute(select(UpdateQuote).filter_by(symbol_ticker=symbol.ticker))
        update_quote = update_quote.scalar_one_or_none()
        
        if update_quote is None:
            update_quote = UpdateQuote(symbol_ticker=symbol.ticker)
            session.add(update_quote)
        
        filtered_data = {UPDATE_QUOTE_MAPPING.get(k, k): v for k, v in quote_data.items() if UPDATE_QUOTE_MAPPING.get(k, k) in UpdateQuote.__table__.columns}
        
        # Convert date string to date object
        if 'date' in filtered_data and filtered_data['date'] is not None:
            filtered_data['date'] = datetime.datetime.fromisoformat(filtered_data['date'].replace('Z', '+00:00')).date()
        
        for key, value in filtered_data.items():
            setattr(update_quote, key, value)
        
        print(update_quote.__dict__)
        await session.flush()

async def process_message(message, session):
    data = json.loads(message)
    if "M" in data and data["M"]:
        method = data["M"][0]["M"]
        if method == "updateQuote":
            await process_update_quote(data["M"][0]["A"], session)  # Pass the entire list
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
    async with websockets.connect(FULLURL) as websocket:
        while is_trading_time():
            message = await websocket.recv()
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    await process_message(message, session)
        
        logger.info("Outside trading hours. Stopping script.")

if __name__ == "__main__":
    if is_trading_time():
        asyncio.run(receive_data_from_websocket())
    else:
        logger.info("Not within trading hours. Script will not run.")
