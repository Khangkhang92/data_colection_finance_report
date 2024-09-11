import os
import asyncio
import websockets
import json
from loguru import logger
from dotenv import load_dotenv
import httpx
import datetime

load_dotenv()

# Constants
SOCKET = os.getenv("SOCKET")
CONNECTION_TOKEN = os.getenv("CONNECTION_TOKEN")
TOKEN = os.getenv("TOKEN")
FULLURL = f"{SOCKET}&connectionToken={CONNECTION_TOKEN}&Token={TOKEN}"
POSTGREST_URL = os.getenv("POSTGREST_URL")

async def is_trading_time():
    now = datetime.datetime.now()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False

    if (
        (9 <= now.hour < 11)
        or (now.hour == 11 and now.minute <= 30)
        or (13 <= now.hour < 15)
    ):
        return True

    return False

async def process_update_quote(quote_data_list):
    async with httpx.AsyncClient() as client:
        for quote_data in quote_data_list[0]:
            # Convert the Date string to datetime object
            date_str = quote_data.get('Date')
            if date_str:
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                quote_data['Date'] = date_obj.isoformat()

            # Call the PostgreSQL function via PostgREST
            response = await client.post(f"{POSTGREST_URL}/rpc/save_update_quote", json=quote_data)
            
            if response.status_code != 200:
                logger.error(f"Error saving data for symbol {quote_data['Symbol']}: {response.text}")
            else:
                logger.info(f"Data saved for symbol {quote_data['Symbol']}")

async def process_message(message):
    data = json.loads(message)
    if "M" in data and data["M"]:
        method = data["M"][0]["M"]
        if method == "updateQuote":
            await process_update_quote(data["M"][0]["A"])
        else:
            logger.info(f"Skipped unknown method: {method}")
    else:
        logger.info("Received message without 'M' key or empty 'M' list")

async def receive_data_from_websocket():
    while True:
        try:
            async with websockets.connect(FULLURL) as websocket:
                logger.info("Connected to WebSocket")
                while await is_trading_time():
                    message = await websocket.recv()
                    await process_message(message)
                logger.info("Outside trading hours. Disconnecting.")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed. Reconnecting...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    logger.info("Starting WebSocket client")
    asyncio.run(receive_data_from_websocket())