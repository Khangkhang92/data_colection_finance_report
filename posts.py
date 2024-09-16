from dotenv import load_dotenv
import os
import requests
import random
import time
import json
import argparse
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent  


load_dotenv()

# API endpoint and headers
BASE_URL = os.getenv('POSTS')
HEADERS = {
    'User-Agent': UserAgent().random,
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Authorization': os.getenv('FIREANT_AUTH_TOKEN'),
    'Origin': 'https://fireant.vn',
    'Referer': 'https://fireant.vn/',
}

# Function to add a random delay
def random_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

# Function to write JSON file
def write_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data written to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {str(e)}")
        return False

# Function to make API calls with retries and pagination
def fetch_posts(params, max_retries=3):
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

def process_batch(params, folder_name):
    data = fetch_posts(params)
    if data:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{folder_name}/posts_{timestamp}_type{params['type']}_offset{params['offset']}_limit{params['limit']}.json"
        write_json(filename, data)
        return len(data)
    return 0

def make_api_calls(total_posts, post_type, posts_per_call=10, max_workers=5, **kwargs):
    folder_name = 'data_posts'
    os.makedirs(folder_name, exist_ok=True)

    params = {'type': post_type, 'offset': 0, 'limit': posts_per_call, **kwargs}
    total_retrieved = 0

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        while total_retrieved < total_posts:
            future = executor.submit(process_batch, params.copy(), folder_name)
            futures.append(future)
            params['offset'] += posts_per_call

        for future in as_completed(futures):
            batch_count = future.result()
            total_retrieved += batch_count
            logger.success(f"Retrieved {batch_count} posts. Total: {total_retrieved}")

            if batch_count < posts_per_call:
                logger.info("No more posts available.")
                break

            if total_retrieved >= total_posts:
                break

    return total_retrieved

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch posts from the API")
    parser.add_argument("--total", type=int, default=100000, help="Total number of posts to fetch")
    parser.add_argument("--type", type=int, default=1, help="Type of posts to fetch")
    parser.add_argument("--step", type=int, default=10, help="Number of posts per API call")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers")
    parser.add_argument("--additional", nargs='*', help="Additional parameters in the format key=value")
    args = parser.parse_args()

    additional_params = dict(param.split('=') for param in args.additional or [])

    # Configure loguru
    logger.add("api_calls.log", rotation="1 day")

    # Make the API calls
    total_retrieved = make_api_calls(args.total, args.type, args.step, args.workers, **additional_params)

    if total_retrieved > 0:
        logger.success(f"Successfully retrieved {total_retrieved} posts.")
    else:
        logger.error("Failed to retrieve data.")
