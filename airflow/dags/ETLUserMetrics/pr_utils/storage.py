from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb
import hashlib
import json

from ETLUserMetrics.config.pipeline_config import (
    DUCKDB_PATH,
    PARQUET_FILENAME,
    ANONYMIZED_TABLE_NAME,
    METADATA_TABLE_NAME,
    METADATA_UNIQUE_COLUMNS,
)
from ETLUserMetrics.pr_utils.utils import get_logger

logger = get_logger(__name__)

# Load SQL initialization script for DuckDB tables
SQL_FILE_PATH = Path(__file__).parents[1] / "sql" / "internal" / "init_internal_tables.sql"
init_internal_tables = SQL_FILE_PATH.read_text()


def save_parquet(df: pd.DataFrame, base_path: str, execution_date: str = None) -> Path:
    """
    Saves a DataFrame as a compressed Parquet file to a date-partitioned path.

    - If execution_date is provided, it's used for partitioning.
    - If not, the current UTC datetime is used.
    - Data is saved with Snappy compression.

    Args:
        df (pd.DataFrame): Data to save.
        base_path (str): Root directory to store the partitioned Parquet file.
        execution_date (str, optional): Ingestion date string in 'YYYY-MM-DD' format.

    Returns:
        Path: Full path to the saved Parquet file.

    Raises:
        FileNotFoundError: If saving fails.
    """
    if execution_date:
        dt = datetime.strptime(execution_date, "%Y-%m-%d")
    else:
        dt = datetime.utcnow()

    path = Path(base_path) / f"{dt.year}" / f"{dt.month:02}" / f"{dt.day:02}"
    path.mkdir(parents=True, exist_ok=True)
    output_path = path / PARQUET_FILENAME

    df.to_parquet(output_path, index=False, compression="snappy")

    if not output_path.exists():
        raise FileNotFoundError(f"Parquet save failed: {output_path}")
    if df.empty:
        logger.warning("Saved Parquet is empty. Check upstream logic.")

    logger.info(f"Saved Parquet to: {output_path}")
    return output_path


def insert_into_duckdb(df: pd.DataFrame, execution_date: str, db_path: str = DUCKDB_PATH):
    """
    Inserts anonymized data into DuckDB.

    - Creates necessary tables if not already present.
    - Adds 'ingestion_date' column to the data.
    - Inserts data into the anonymized user table.
    - Logs row counts and unique value counts for validation.

    Args:
        df (pd.DataFrame): Anonymized user data.
        execution_date (str): Ingestion date string in 'YYYY-MM-DD' format.
        db_path (str): Path to the DuckDB file.
    """
    with duckdb.connect(db_path) as con:
        con.execute(init_internal_tables)

        df["ingestion_date"] = datetime.strptime(execution_date, "%Y-%m-%d").date()
        con.register("df", df)

        insert_sql = f"INSERT INTO {ANONYMIZED_TABLE_NAME} SELECT * FROM df"
        con.execute(insert_sql)

        total_count = con.execute(f"SELECT COUNT(*) FROM {ANONYMIZED_TABLE_NAME}").fetchone()[0]

        distinct_cols = ", ".join(METADATA_UNIQUE_COLUMNS)
        unique_sql = f"""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT {distinct_cols}
                FROM {ANONYMIZED_TABLE_NAME}
            )
        """
        unique_count = con.execute(unique_sql).fetchone()[0]

    logger.info(f"Inserted {len(df)} records into DuckDB.")
    logger.info(f"Total records in '{ANONYMIZED_TABLE_NAME}': {total_count}")
    logger.info(f"Unique records (by {distinct_cols}): {unique_count}")


def compute_schema_signature(df: pd.DataFrame) -> str:
    """
    Generates a SHA-256 hash of the column names for schema tracking.

    - Sorts column names alphabetically before hashing.
    - Used for detecting schema drift over time.

    Args:
        df (pd.DataFrame): DataFrame for which to compute the signature.

    Returns:
        str: SHA-256 hex digest representing the schema.
    """
    cols = sorted(df.columns.tolist())
    joined = ",".join(cols)
    return hashlib.sha256(joined.encode()).hexdigest()


def log_metadata(df: pd.DataFrame, parquet_path: Path, db_path: str = DUCKDB_PATH):
    """
    Logs ingestion metadata to DuckDB.

    Stores metadata such as:
    - ingestion time
    - record count
    - schema (columns)
    - schema signature (hash)
    - parquet file path

    Args:
        df (pd.DataFrame): Data that was ingested.
        parquet_path (Path): Path to the saved Parquet file.
        db_path (str): Path to the DuckDB file.
    """
    columns = df.columns.tolist()
    schema_signature = compute_schema_signature(df)

    with duckdb.connect(db_path) as con:
        con.execute(
            f"""
            INSERT INTO {METADATA_TABLE_NAME} (
                ingestion_time, records_inserted, filepath,
                column_count, column_list, schema_signature
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow(),
                len(df),
                str(parquet_path),
                len(columns),
                json.dumps(columns),
                schema_signature
            )
        )
    logger.info(f"Metadata logged: {len(df)} rows, {len(columns)} columns.")


def cleanup_metadata_log(days: int = 30, db_path: str = DUCKDB_PATH):
    """
    Cleans up old metadata logs from DuckDB based on retention window.

    Deletes records in the metadata table older than `days` days.

    Args:
        days (int): Number of days to retain metadata.
        db_path (str): Path to the DuckDB file.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    with duckdb.connect(db_path) as con:
        con.execute(f"""
            DELETE FROM {METADATA_TABLE_NAME}
            WHERE ingestion_time < ?
        """, (cutoff,))

    logger.info(f"Cleaned metadata entries older than {cutoff}")
