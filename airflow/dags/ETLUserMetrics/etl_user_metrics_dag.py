from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
from pathlib import Path
from datetime import timedelta

from ETLUserMetrics.pr_utils.fetch import fetch_all_users_parallel
from ETLUserMetrics.pr_utils.anonymize import anonymize_users
from ETLUserMetrics.pr_utils.storage import save_parquet, log_metadata, cleanup_metadata_log
from ETLUserMetrics.pr_utils.transformation import run_transformation_pipeline
from ETLUserMetrics.pr_utils.utils import run_sql_query
from ETLUserMetrics.config.pipeline_config import RAW_PATH

from ETLUserMetrics.pr_utils.operators.duckdb_operator import DuckDBExecuteQueryOperator
from airflow.utils.task_group import TaskGroup



# SQL folder for reporting
SQL_REPORTING_DIR = Path(__file__).parent / "sql" / "reporting"

# Define your reporting SQL files (without .sql extension if used as task_id)
REPORTING_SQL_FILES = [
    "germany_gmail_percentage",
    "over60_gmail_users",
    "top_gmail_countries"
]

# -------- TASKS -------- #

def fetch_and_anonymize(execution_date):
    users = fetch_all_users_parallel()
    df = anonymize_users(users)
    parquet_path = save_parquet(df, RAW_PATH, execution_date)
    log_metadata(df, parquet_path)


def transform(execution_date):
    run_transformation_pipeline(execution_date)

def create_reporting_task(task_id: str):
    return PythonOperator(
        task_id=task_id,
        python_callable=run_sql_query,
        op_args=[task_id, SQL_REPORTING_DIR],  # Correct usage
    )

# -------- DAG SETUP -------- #

default_args = {
    'start_date': days_ago(1),
    'retries': 3,                        
    'retry_delay': timedelta(minutes=5),  
    'catchup': False,
}

with DAG(
    dag_id="user_metrics_pipeline",
    default_args=default_args,
    schedule_interval="0 7 * * *",  # daily at 07:00 UTC
    catchup=False,
    description="Fetch, anonymize, transform, and report user metrics",
    tags=["07:00"]
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    fetch_task = PythonOperator(
        task_id="fetch_and_anonymize",
        python_callable=fetch_and_anonymize,
        op_kwargs={"execution_date": "{{ ds }}"}
    )

    cleanup_task = PythonOperator(
        task_id="cleanup_metadata_log",
        python_callable=cleanup_metadata_log
    )

    init_internal_tables = DuckDBExecuteQueryOperator(
    task_id="init_internal_tables",
    sql_path="airflow/dags/ETLUserMetrics/sql/internal/init_internal_tables.sql",
    dag=dag
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform,
        op_kwargs={"execution_date": "{{ ds }}"}
    )

    # # Reporting
    # reporting_tasks = [
    #     create_reporting_task(sql_file) for sql_file in REPORTING_SQL_FILES
    # ]

    # Reporting (wrapped in TaskGroup)
    with TaskGroup("reporting_tasks_group", tooltip="Run reporting SQL queries") as reporting_group:
        reporting_tasks = [
            create_reporting_task(sql_file) for sql_file in REPORTING_SQL_FILES
        ]

    # Flow
    start >> init_internal_tables >> fetch_task >> transform_task >> reporting_group >> cleanup_task >>end

