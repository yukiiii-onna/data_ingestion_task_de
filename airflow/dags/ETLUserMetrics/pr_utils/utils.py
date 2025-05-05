from datetime import datetime
import duckdb
from pathlib import Path
import logging
import sys

from ETLUserMetrics.config.pipeline_config import DUCKDB_PATH

# Default path for SQL files used in reporting
DEFAULT_SQL_DIR = Path(__file__).parents[2] / "sql" / "reporting"


def run_sql_query(sql_filename: str, sql_dir: Path = DEFAULT_SQL_DIR):
    """
    Executes a SQL query from a file using DuckDB and returns the result as a DataFrame.

    - Looks for a SQL file in the provided `sql_dir`.
    - Executes the query using DuckDB.
    - Prints and returns the result as a pandas DataFrame.

    Args:
        sql_filename (str): Filename of the .sql file to execute (e.g., 'top_gmail_countries').
        sql_dir (Path, optional): Path to the folder containing SQL files.
                                  Defaults to the 'sql/reporting/' directory.

    Returns:
        pd.DataFrame: Result of the SQL query.

    Raises:
        FileNotFoundError: If the SQL file does not exist.
    """
    if not sql_filename.endswith(".sql"):
        sql_filename += ".sql"

    path = sql_dir / sql_filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")

    query = path.read_text()

    with duckdb.connect(DUCKDB_PATH) as con:
        result = con.execute(query).fetchdf()
        print(f"Query {sql_filename} executed successfully from {sql_dir}.")
        print(result.head())
        return result


def get_logger(name: str) -> logging.Logger:
    """
    Initializes and returns a logger with a consistent format and INFO level.

    This is used across the project to ensure uniform logging style.

    Args:
        name (str): Name of the logger, typically `__name__`.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    return logging.getLogger(name)
