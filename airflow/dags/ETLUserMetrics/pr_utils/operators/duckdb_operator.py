from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import duckdb
from pathlib import Path
from ETLUserMetrics.config.pipeline_config import DUCKDB_PATH


class DuckDBExecuteQueryOperator(BaseOperator):
    @apply_defaults
    def __init__(self, sql_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sql_path = sql_path

    def execute(self, context):
        sql_file = Path(self.sql_path)
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_path}")

        with open(sql_file, "r") as f:
            sql = f.read()

        conn = duckdb.connect(DUCKDB_PATH)
        conn.execute(sql)
        self.log.info(f"Executed DuckDB SQL: {self.sql_path}")
