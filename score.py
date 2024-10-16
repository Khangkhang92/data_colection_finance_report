from baseCallApi import BaseCallAPI
from base import Base
from dotenv import load_dotenv
import os
import redis
import json
from loguru import logger

load_dotenv()
SCORE_URL = os.getenv("SCORE_URL")
TOKEN = os.getenv("TOKEN_REST2")
token = f"Bearer {TOKEN}"
redis_client = redis.Redis(host="127.0.0.1", port="6379", db=1)

quater_params = {
    "type": "Q",
    "count": 60
}

year_params = {
    "type": "Y",
    "count": 15
}

base = Base()
all_symbols = base.get_all_symbols()

baseCallAPI = BaseCallAPI(SCORE_URL,token)
baseCallAPI.headers.update({
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
    })

for symbol in all_symbols:
    FULL_URL = f"{SCORE_URL}/{symbol}/financial-data"
    baseCallAPI.base_url = FULL_URL
    # redis_client.flushdb()
    try:
        quater_data = baseCallAPI.fetch_posts(quater_params)   
        year_data = baseCallAPI.fetch_posts(year_params)
        for item in quater_data:
            redis_client.rpush(f"{symbol}:quarter", json.dumps(item, ensure_ascii=False))
        for item in year_data:
            redis_client.rpush(f"{symbol}:year", json.dumps(item, ensure_ascii=False))

        logger.info(f"Saved {symbol} to Redis.")
        
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
