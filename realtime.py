import os
import asyncio
import websockets
import json
from loguru import logger
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
SOCKET = os.getenv("SOCKET")
CONNECTION_TOKEN = os.getenv("CONNECTION_TOKEN")
TOKEN = os.getenv("TOKEN")

fullurl = SOCKET + "&connectionToken=" + CONNECTION_TOKEN + "&Token=" + TOKEN

data_folder = "markets_data"
os.makedirs(data_folder, exist_ok=True)

# Use a defaultdict to map methods to their respective files
method_to_file = defaultdict(
    lambda: "unknown.json",
    {
        "updateQuote": "updateQuote.json",
        "updateMarket": "updateMarket.json",
        "updateIntradayQuote": "updateIntradayQuote.json",
        "updateIntradayMarketStatistic": "updateIntradayMarketStatistic.json",
    },
)


async def receive_data_from_websocket(uri):
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            await process_message(message)


async def process_message(message):
    data = json.loads(message)
    if "M" in data and data["M"]:
        method = data["M"][0]["M"]
        filename = os.path.join(data_folder, method_to_file[method])
        await append_to_json_file(filename, data)
        logger.info(f"Processed message: {method}")
    else:
        logger.warning("Received message with unexpected format")


async def append_to_json_file(filename, new_data):
    async with asyncio.Lock():
        try:
            with open(filename, "rb+") as file:
                file.seek(0, 2)
                if file.tell() == 0:
                    file.write(json.dumps([new_data], indent=2).encode())
                else:
                    file.seek(-1, 2)
                    file.truncate()
                    file.write(b",\n")
                    file.write(json.dumps(new_data, indent=2).encode())
                    file.write(b"\n]")
        except FileNotFoundError:
            with open(filename, "wb") as file:
                file.write(json.dumps([new_data], indent=2).encode())


asyncio.run(receive_data_from_websocket(fullurl))
