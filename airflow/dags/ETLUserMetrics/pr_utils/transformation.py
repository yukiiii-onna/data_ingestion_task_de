import pandas as pd
from datetime import datetime
from pathlib import Path
import duckdb

from ETLUserMetrics.config.pipeline_config import (
    RAW_PATH,
    DUCKDB_PATH,
    PARQUET_FILENAME,
    FINAL_USER_COLUMNS,
    ANONYMIZED_TABLE_NAME,
    INTERNAL_SQL_DIR,
    UNIQUE_SQL_FILENAME,
)
from ETLUserMetrics.pr_utils.utils import run_sql_query
from ETLUserMetrics.pr_utils.utils import get_logger

logger = get_logger(__name__)


def get_expected_parquet_path(execution_date: str) -> Path:
    dt = datetime.strptime(execution_date, "%Y-%m-%d")
    return Path(RAW_PATH) / f"{dt.year}" / f"{dt.month:02}" / f"{dt.day:02}" / PARQUET_FILENAME

def calculate_age_group(birthday_str):
    try:
        birth_year = datetime.strptime(birthday_str, "%Y-%m-%d").year
        age = datetime.now().year - birth_year
        if age >= 90:
            return "[90+]"
        lower = (age // 10) * 10
        upper = lower + 10
        return f"[{lower}-{upper}]"
    except Exception:
        logger.warning(f"Invalid birthday format: {birthday_str}")
        return "unknown"



def extract_email_domain(email):
    try:
        return email.split("@")[1].lower()
    except Exception:
        return "unknown"


def transform_user_data(df: pd.DataFrame, execution_date: str) -> pd.DataFrame:
    df = df.copy()
    if "birthday" in df.columns:
        df["age_group"] = df["birthday"].apply(calculate_age_group)
    else:
        df["age_group"] = "unknown"
    df["email"] = df["email"].apply(extract_email_domain)
    df["ingestion_date"] = execution_date
    df["faker_id"] = range(1, len(df) + 1)

    df = df[FINAL_USER_COLUMNS]
    logger.info(f"Transformed DataFrame with shape: {df.shape}")
    return df


def insert_transformed_data(df: pd.DataFrame, execution_date: str, table_name: str = ANONYMIZED_TABLE_NAME):
    with duckdb.connect(DUCKDB_PATH) as con:
        con.register("df", df)
        
        # Assuming ingestion_date is a standard
        con.execute(f"DELETE FROM {table_name} WHERE ingestion_date = ?", (execution_date,))
        con.execute(f"INSERT INTO {table_name} SELECT * FROM df")

        total = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    unique_df = run_sql_query(UNIQUE_SQL_FILENAME, sql_dir=INTERNAL_SQL_DIR)
    unique = unique_df["unique_count"].iloc[0]

    logger.info(f"Inserted {len(df)} records into '{table_name}'.")
    logger.info(f"Total in DuckDB: {total} | Unique email providers: {unique}")


def run_transformation_pipeline(execution_date: str):
    parquet_path = get_expected_parquet_path(execution_date)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    logger.info(f"Loaded {len(df)} records from {parquet_path}")

    transformed = transform_user_data(df, execution_date)
    logger.info(f"Transformed preview:\n{transformed.head()}")

    insert_transformed_data(transformed, execution_date)
