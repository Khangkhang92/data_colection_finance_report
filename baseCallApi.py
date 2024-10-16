from dotenv import load_dotenv

import requests
import random
import time
from loguru import logger
from fake_useragent import UserAgent


load_dotenv()


class BaseCallAPI:
    def __init__(self, base_url, auth_token):
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
        """Pause execution for a random duration."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def fetch_posts(self, params={}, max_retries=1):
        """Fetch posts from the API with retries."""
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


     
