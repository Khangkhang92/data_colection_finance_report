from dotenv import load_dotenv
import os
import requests
import random
import time
import argparse
from loguru import logger
from fake_useragent import UserAgent
from models import Post, PostGroup, PostSource, TaggedSymbol, Symbol
from common.db import ScopedSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from functools import lru_cache
from pathlib import Path
from getdata.base import Base

load_dotenv()


# API endpoint and headers
BASE_URL = os.getenv("POST")
HEADERS = {
    "User-Agent": UserAgent().random,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Authorization": f"Bearer {os.getenv('TOKEN_REST2')}",
    "Origin": "https://fireant.vn",
    "Referer": "https://fireant.vn/",
}


# Function to add a random delay
def random_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))


# Function to make API calls with retries and pagination
def fetch_posts(params, max_retries=1):
    for attempt in range(max_retries):
        try:
            random_delay()
            response = requests.get(BASE_URL, params=params, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached.")
                return None
            random_delay(5, 10)


@lru_cache(maxsize=None)
def get_existing_symbols(db_session):
    return set(db_session.execute(select(Symbol.ticker)).scalars().all())


def save_to_database(data):
    with ScopedSession() as db_session:
        for post_data in data:
            # Fetch or create PostGroup
            post_group = None
            if post_data["postGroup"]:
                stmt = insert(PostGroup).values(
                    **PostGroup.from_json(post_data["postGroup"])
                )
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["fireant_post_group_id"]
                )
                result = db_session.execute(stmt)
                if result.rowcount > 0:
                    post_group = db_session.execute(
                        select(PostGroup).where(
                            PostGroup.fireant_post_group_id
                            == post_data["postGroup"]["postGroupID"]
                        )
                    ).scalar_one()
                else:
                    post_group = db_session.execute(
                        select(PostGroup).where(
                            PostGroup.fireant_post_group_id
                            == post_data["postGroup"]["postGroupID"]
                        )
                    ).scalar_one_or_none()

            # Fetch or create PostSource
            post_source = None
            if post_data["postSource"]:
                stmt = insert(PostSource).values(
                    **PostSource.from_json(post_data["postSource"])
                )
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["fireant_post_source_id"]
                )
                result = db_session.execute(stmt)
                if result.rowcount > 0:
                    post_source = db_session.execute(
                        select(PostSource).where(
                            PostSource.fireant_post_source_id
                            == post_data["postSource"]["postSourceID"]
                        )
                    ).scalar_one()
                else:
                    post_source = db_session.execute(
                        select(PostSource).where(
                            PostSource.fireant_post_source_id
                            == post_data["postSource"]["postSourceID"]
                        )
                    ).scalar_one_or_none()

            # Upsert Post
            post_dict = Post.from_json(post_data)
            post_dict["post_group_id"] = (
                post_group.post_group_id if post_group else None
            )
            post_dict["post_source_id"] = (
                post_source.post_source_id if post_source else None
            )

            stmt = insert(Post).values(**post_dict)
            stmt = stmt.on_conflict_do_update(
                index_elements=["fireant_post_id"], set_=post_dict
            )
            result = db_session.execute(stmt)

            # Get the post_id
            post_id = db_session.execute(
                select(Post.post_id).where(
                    Post.fireant_post_id == post_dict["fireant_post_id"]
                )
            ).scalar_one()

            # Bulk insert TaggedSymbols with error handling
            try:
                existing_symbols = get_existing_symbols(db_session)
                tagged_symbols = [
                    TaggedSymbol(post_id=post_id, symbol_ticker=tagger["symbol"])
                    for tagger in post_data.get("taggedSymbols", [])
                    if tagger["symbol"] in existing_symbols
                ]
                if tagged_symbols:
                    db_session.add_all(tagged_symbols)
                for tagger in post_data.get("taggedSymbols", []):
                    if tagger["symbol"] not in existing_symbols:
                        logger.warning(
                            f"Symbol {tagger['symbol']} not found in the database. Skipping."
                        )
            except Exception as e:
                logger.error(
                    f"Error creating TaggedSymbols for post {post_id}: {str(e)}"
                )
                tagged_symbols = None

        db_session.commit()
        logger.success(f"Committed {len(data)} posts to the database")


def process_batch(params):
    data = fetch_posts(params)
    if data:
        # Save to database
        save_to_database(data)
        return len(data)
    return 0


def make_api_calls(total_posts, post_type, posts_per_call=1, **kwargs):
    params = {"type": post_type, "offset": 0, "limit": posts_per_call, **kwargs}
    total_retrieved = 0

    while total_retrieved < total_posts:
        batch_count = process_batch(params)
        total_retrieved += batch_count
        logger.success(
            f"Retrieved and saved {batch_count} posts. Total: {total_retrieved}"
        )

        if batch_count < posts_per_call:
            logger.info("No more posts available.")
            break

        if total_retrieved >= total_posts:
            break

        params["offset"] += posts_per_call

    return total_retrieved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch posts from the API")
    parser.add_argument(
        "--total",
        type=int,
        default=1000,
        help="Total number of posts to fetch",  # Total number of posts to fetch
    )
    parser.add_argument("--type", type=int, default=1, help="Type of posts to fetch")
    parser.add_argument(
        "--step", type=int, default=100, help="Number of posts per API call"
    )

    parser.add_argument(
        "--additional", nargs="*", help="Additional parameters in the format key=value"
    )
    args = parser.parse_args()

    additional_params = dict(param.split("=") for param in args.additional or [])

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure logger to write to file
    logger.add(
        logs_dir / "news.log", rotation="1 day", retention="7 days", level="ERROR"
    )

    # Make the API calls
    total_retrieved = make_api_calls(
        args.total, args.type, args.step, **additional_params
    )

    if total_retrieved > 0:
        logger.success(f"Successfully retrieved and saved {total_retrieved} posts.")
    else:
        logger.error("Failed to retrieve and save data.")


def clear_symbol_cache():
    get_existing_symbols.cache_clear()
