import os
from pathlib import Path

# Paths (injected via .env or fallback defaults)
RAW_PATH = os.getenv("RAW_PATH", "/app/data_lake/raw")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/app/db/my_duck.db")

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://fakerapi.it/api/v2/persons")
BIRTHDAY_START_DATE = os.getenv("BIRTHDAY_START_DATE", "1960-01-01")

# Retry and Timeout Settings (ensure they are integers)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "2"))

# Core fetch settings (keep hardcoded as logic-level constants)
GENDERS = ["male", "female"]
RECORDS_PER_BATCH = 1000
BATCHES_PER_GENDER = 15

# SQL folder paths
BASE_DIR = Path(__file__).parents[1]
BASE_SQL_DIR = BASE_DIR / "sql"
INTERNAL_SQL_DIR = BASE_SQL_DIR / "internal"
REPORTING_SQL_DIR = BASE_SQL_DIR / "reporting"
DEFAULT_SQL_DIR = REPORTING_SQL_DIR

# Metadata logging
METADATA_TABLE_NAME = "metadata_log"
METADATA_UNIQUE_COLUMNS = ["country", "city", "age_group", "email_provider", "email"]

# Storage settings
PARQUET_FILENAME = "persons.parquet"
ANONYMIZED_TABLE_NAME = "persons_anonymized"

# Columns used in final DuckDB insert
FINAL_USER_COLUMNS = [
    "faker_id", "email", "age_group",
    "gender", "city", "country",
    "country_code", "ingestion_date"
]

# Validation / Reporting
UNIQUE_SQL_FILENAME = "unique_email_provider_count.sql"
