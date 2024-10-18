from dotenv import load_dotenv
from common.db import ScopedSession
from sqlalchemy import select
from functools import lru_cache
from models import Symbol
import requests
import random
import time
from loguru import logger
from fake_useragent import UserAgent
import os


load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)  # from parrent directory
token = f"Bearer {os.getenv('TOKEN_REST2')}"


class Base:
    def __init__(self, base_url=None, auth_token=token):
        self.base_url = base_url
        self.headers = {
            "User-Agent": UserAgent().random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Authorization": auth_token,
            "Origin": "https://fireant.vn",
            "Referer": "https://fireant.vn/",
        }

    def random_delay(self, min_seconds=1, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def fetch_posts(self, params={}, max_retries=1):
        for attempt in range(max_retries):
            try:
                self.random_delay()
                response = requests.get(
                    self.base_url, params=params, headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Max retries reached.")
                    return None
                self.random_delay(5, 10)

    @lru_cache(maxsize=1)
    def get_all_symbols(self):
        with ScopedSession() as session:
            return session.execute(select(Symbol.ticker)).scalars().all()
