import pandas as pd
from datetime import datetime

from ETLUserMetrics.config.anonymization_config import ANONYMIZATION_CONFIG, NESTED_FIELDS
from ETLUserMetrics.pr_utils.utils import get_logger

# Initialize logger for the current module
logger = get_logger(__name__)


def get_value_from_user_record(user: dict, field: str):
    """
    Retrieves a value from a user record.

    Looks for the field in the top-level user dictionary.
    If not found, it tries to find the field inside the 'address' sub-dictionary.
    
    Args:
        user (dict): A user record with possible nested fields.
        field (str): The field name to retrieve.

    Returns:
        The value of the field if found, else None.
    """
    if field in user:
        return user[field]
    elif field in user.get("address", {}): 
        return user["address"].get(field) 
    return None


def anonymize_users(users: list[dict], config: dict = ANONYMIZATION_CONFIG) -> pd.DataFrame:
    """
    Anonymizes a list of user dictionaries based on a given configuration.

    - Flattens nested user fields (e.g., address).
    - Applies anonymization functions from config to selected fields.
    - Logs progress and errors encountered during anonymization.

    Args:
        users (list[dict]): List of user records from the API.
        config (dict): A dictionary of field-to-function mappings for anonymization.

    Returns:
        pd.DataFrame: A DataFrame containing the anonymized user data.
    """
    logger.info(f"Starting anonymization for {len(users)} user records...")
    anonymized = []

    for idx, user in enumerate(users):
        row = {}

        # Create a shallow copy of user
        flat_user = dict(user)

        # Merge nested fields (e.g., address) into top-level dict
        for nested in NESTED_FIELDS:
            flat_user.update(user.get(nested, {}))

        for field, value in flat_user.items():
            # If the field has an anonymization rule
            if field in config:
                try:
                    row[field] = config[field](value)  # Apply anonymization
                except Exception as e:
                    logger.error(f"Error anonymizing field '{field}' in user index {idx}: {e}")
                    row[field] = None
            else:
                # Keep the original value if no anonymization is defined
                row[field] = value

        anonymized.append(row)

    logger.info(f"Anonymization complete. Total records processed: {len(anonymized)}")
    return pd.DataFrame(anonymized)
