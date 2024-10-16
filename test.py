import asyncio
import websockets
import os
from dotenv import load_dotenv

load_dotenv()

temp = os.getenv("TEMP")

first = """{
  "data": {
    "value1": 0x0291,
    "value2": 0x06
  }
}"""

second = """{
  "data": [
    {
      "id": 0,
      "function": "GetSymbol"
    },
    {
      "id": 1,
      "function": "GetFinancialInfos"
    },
    {
      "id": 2,
      "function": "GetServerTimeU"
    },
    {
      "id": 3,
      "function": "SubscribeTrades"
    },
    {
      "id": 4,
      "function": "GetTradingStatistics"
    }
  ]
}"""


async def connect(temp):
    while True:
        try:
            async with websockets.connect(f"wss://tradestation.fireant.vn/quote?access_token={temp}") as websocket:
                await websocket.send('{"protocol":"json","version":1}')
                await websocket.send(first)
                await websocket.send(second)
                response = await websocket.recv()
                print(response)
        except asyncio.TimeoutError:
                print("error")    


asyncio.get_event_loop().run_until_complete(connect(temp))
