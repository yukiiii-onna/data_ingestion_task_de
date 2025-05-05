import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from ETLUserMetrics.pr_utils.utils import get_logger
from ETLUserMetrics.config.pipeline_config import (
    API_BASE_URL,
    GENDERS,
    RECORDS_PER_BATCH,
    BATCHES_PER_GENDER,
    API_TIMEOUT,
    BIRTHDAY_START_DATE,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS
)

# Logger setup for tracking progress and errors
logger = logging.getLogger(__name__)

# Create a single requests session for efficiency (reuses TCP connections)
session = requests.Session()
HEADERS = {
    "User-Agent": "faker-api-client/1.0"  # Identifies your script to the server
}


def fetch_batch(gender: str, batch_index: int) -> List[Dict]:
    """
    Fetches one batch of user data from the API with retry logic.

    Each batch contains a fixed number of users (RECORDS_PER_BATCH) for a given gender.
    Retries are applied using exponential backoff if the request fails.

    Args:
        gender (str): Gender of users to fetch ("male" or "female").
        batch_index (int): Index of the batch (used for logging/debugging).

    Returns:
        List[Dict]: A list of user records as dictionaries. Empty list if all retries fail.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        start = time.time()
        try:
            # Send GET request with query parameters and headers
            response = requests.get(
                API_BASE_URL,
                params={
                    "_quantity": RECORDS_PER_BATCH,
                    "_gender": gender,
                    "_birthday_start": BIRTHDAY_START_DATE
                },
                timeout=API_TIMEOUT,
                headers=HEADERS,
            )

            duration = round(time.time() - start, 2)
            logger.info(f"[{gender.upper()}-{batch_index}] Request URL: {response.url}")

            # Check for successful response
            if response.status_code == 200:
                logger.info(f"[{gender.upper()}-{batch_index}] Completed in {duration}s")
                return response.json().get("data", [])
            else:
                logger.warning(
                    f"[{gender.upper()}-{batch_index}] Attempt {attempt + 1} failed: "
                    f"Status {response.status_code}"
                )

        except requests.exceptions.Timeout:
            logger.error(f"[{gender.upper()}-{batch_index}] Attempt {attempt + 1} timeout.")

        except requests.exceptions.RequestException as e:
            logger.error(f"[{gender.upper()}-{batch_index}] Attempt {attempt + 1} request error: {e}")

        # Wait before retrying (exponential backoff)
        backoff = RETRY_DELAY_SECONDS * (2 ** attempt)
        time.sleep(backoff)
        attempt += 1

    logger.error(f"[{gender.upper()}-{batch_index}] All {MAX_RETRIES} retries failed.")
    return []


def fetch_users_for_gender(gender: str) -> List[Dict]:
    """
    Fetches all user batches for a single gender sequentially.

    Args:
        gender (str): Gender to fetch ("male" or "female").

    Returns:
        List[Dict]: List of user records for the given gender.
    """
    logger.info(f"Fetching {BATCHES_PER_GENDER} batches for gender: {gender}")
    gender_start = time.time()

    all_users = []
    for i in range(BATCHES_PER_GENDER):
        batch = fetch_batch(gender, i)
        all_users.extend(batch)

    gender_duration = round(time.time() - gender_start, 2)
    logger.info(f"Finished fetching {len(all_users)} users for {gender} in {gender_duration}s")
    return all_users


def fetch_all_users_parallel() -> List[Dict]:
    """
    Fetches users for all genders in parallel using ThreadPoolExecutor.

    Executes `fetch_users_for_gender()` concurrently for each gender.
    Collects and combines results into a single list.

    Returns:
        List[Dict]: Combined list of all user records fetched.
    """
    logger.info("Starting parallel user fetch...")
    total_start = time.time()

    # Create a thread pool with one worker per gender
    with ThreadPoolExecutor(max_workers=len(GENDERS)) as executor:
        # Submit parallel tasks and map futures to genders
        futures = {
            executor.submit(fetch_users_for_gender, gender): gender
            for gender in GENDERS
        }

        results = []
        for future in as_completed(futures):
            gender = futures[future]
            try:
                results.extend(future.result())
            except Exception as e:
                logger.error(f"Failed to fetch users for gender: {gender}. Error: {e}")

    total_duration = round(time.time() - total_start, 2)
    logger.info(f"Total users fetched: {len(results)} in {total_duration}s")
    return results
