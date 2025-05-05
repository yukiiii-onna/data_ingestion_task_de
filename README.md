```markdown
# Faker API Data Flow

A Dockerized pipeline that ingests synthetic person data from a public API, anonymizes PII, stores it in DuckDB, and generates analytical reports using SQL and Streamlit.

---

## Project Overview

This project simulates a real-world data ingestion pipeline that processes external third-party data securely and efficiently. The pipeline fetches synthetic user data from the [Faker API](https://fakerapi.it/), anonymizes sensitive fields (PII), stores the transformed data in a local DuckDB database, and generates SQL-based reports for analytical insights.

It demonstrates:
- Scalable data ingestion from external APIs
- PII anonymization through masking and generalization
- SQL reporting on anonymized datasets
- Containerized orchestration with Docker and Apache Airflow

This solution was developed as part of a **Senior Data Engineer take-home challenge** and focuses on production-simulated design and code quality.

➡️ For a discussion on **production-ready improvements**, see [Production Readiness](#-production-readiness--improvements).  
➡️ To run this project locally, see [How to Run the Project](#-how-to-run-the-project).

---

## Features

- Ingests 30,000 synthetic user profiles from the Faker API
- Applies **PII masking** before storing raw data into partitioned Parquet files
  - Stored in `data_lake/raw/YYYY/MM/DD/`
  - Masks name, phone, address, coordinates, ZIP code, and email local part
- Applies **data generalization and cleaning** before loading into DuckDB
  - Converts birthdate to 10-year age groups (e.g., [30–40])
  - Extracts email domain and retains anonymized location details
- Loads cleaned data into DuckDB for querying
  - Database stored in a mounted `/db/` volume for persistence
- Generates SQL-based analytical reports:
  - % of German users using Gmail
  - Top 3 countries using Gmail
  - Count of Gmail users over age 60
- Visualizes results with a Streamlit dashboard
- Fully orchestrated with Apache Airflow
- Fully containerized with Docker for consistent local development

---

## Folder Structure

```

faker-api-dataflow/
├── airflow/
│   ├── dags/
│   │   └── ETLUserMetrics/
│   │       ├── config/
│   │       │   ├── anonymization_config.py
│   │       │   └── pipeline_config.py
│   │       ├── pr_utils/
│   │       │   ├── anonymize.py
│   │       │   ├── fetch.py
│   │       │   ├── storage.py
│   │       │   ├── transformation.py
│   │       │   ├── utils.py
│   │       │   └── operators/
│   │       │       └── duckdb_operator.py
│   │       ├── sql/
│   │       │   └── internal/
|   |       |       └──create_tables.sql
|   |       |       └──unique_email_provider_count.sql
|   |       |       └──init_internals_tables.sql                   
│   │       │   └── reporting/
|   |       |       └──germany_gmail_percentage.sql
|   |       |       └──over60_gmail_users.sql
|   |       |       └──top_gmail_countries.sql
│   │       └── etl_user_metrics_dag.py
│   ├── logs/
│   ├── plugins/
│   └── sql/
├── data_lake/
│   └── raw/                               # Partitioned Parquet (YYYY/MM/DD)
├── db/                                    # DuckDB database 
├── gx/                                    # Placeholder for Great Expectations
├── scripts/
├── streamlit_app/
├── tests/
│   └── dags/ETLUserMetrics/
│       ├── test_anonymize.py
│       ├── test_fetch.py
│       └── test_sql_queries.py
├── .env
├── .env.example
├── airflow.db
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md

````

---

## ▶️ How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/faker-api-dataflow.git
cd faker-api-dataflow
````

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

*(This is also handled automatically when you run `make up-all`.)*

### 3. Start the Project

```bash
make up-all
```

* Airflow UI: [http://localhost:8080](http://localhost:8080)
* Streamlit Dashboard: [http://localhost:8501](http://localhost:8501)

### 4. Trigger the DAG

1. Go to the Airflow UI.
2. Enable and trigger the DAG named: `user_metrics_pipeline`

### 5. View Results

* Raw masked data: `data_lake/raw/YYYY/MM/DD/persons.parquet`
* Anonymized + transformed data: `db/faker.duckdb`
* Final reports: Streamlit dashboard

### 6. Run Tests
Build the Docker test image and run all tests using `pytest`:

```bash
make all
```

---

## Data Flow Overview

```
start
  |
  ├──> init_internal_tables
  |
  └──> fetch_and_anonymize
           |
           ├──> cleanup_metadata_log
           |
           └──> transform
                    |
                    ├──> top_gmail_countries
                    ├──> over60_gmail_users
                    └──> germany_gmail_percentage
                             |
                            end
```

---

## Tech Stack

**Language & Frameworks**

* Python 3.10
* Apache Airflow – DAG orchestration
* Streamlit – Interactive reporting dashboard

**Data Handling**

* Pandas – Data manipulation and transformation
* DuckDB – Embedded analytical database
* Parquet – Partitioned data lake storage

**Infrastructure & Tooling**

* Docker & Docker Compose – Containerized setup
* Makefile – Dev automation
* Environment variables – Config management with `.env`

**Testing**

* Pytest – Unit tests for pipeline modules
* Structured test suite under `/tests/`

---

## Example Reports

All reports run via SQL and are visualized in Streamlit.

**1. Germany Gmail Users (%):**

```sql
SELECT 
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM persons_anonymized), 2) AS germany_gmail_percentage
FROM persons_anonymized
WHERE country = 'Germany' AND email = 'gmail.com';
```

**2. Top 3 Gmail Countries:**

```sql
SELECT country, COUNT(*) AS gmail_users
FROM persons_anonymized
WHERE email = 'gmail.com'
GROUP BY country
ORDER BY gmail_users DESC
LIMIT 3;
```

**3. Gmail Users Over 60:**

```sql
SELECT COUNT(*) AS gmail_over_60
FROM persons_anonymized
WHERE email = 'gmail.com' AND age_group IN ('[60-70]', '[70-80]', '[80-90]', '[90+]');
```

---

## 🚀 Production Readiness & Improvements

This project simulates a real-world data pipeline. Below are improvements and production-grade considerations:

### Data Quality & Schema Stability

* Schema drift detection via stored schema signatures (future work)
* Great Expectations integration planned for:

  * Null checks
  * Row count thresholds
  * Domain/value validation
* Formal data contracts for ingestion

### Pipeline Design

* Handle late-arriving data using watermarking or partition repair
* Retain raw data for reprocessing/backfilling
* Support re-runs and backfills gracefully
* Avoid table drops; use migration/versioning

### 🔧 Architecture & Modularity

* Automate everything via Makefile, Docker, Airflow, and future CI/CD

### Observability & Monitoring

* Metadata logging for each run
* Future Slack/email alerting for failures or drift
* Track KPIs: DAG runtime, freshness, volume

### Cloud Readiness

* Cost-aware practices for cloud DBs
* Use partition pruning, materialized views
* Optimize latency for near-real-time pipelines

### Testing & Documentation

* Full unit tests and SQL query validation
* Future: GitHub Actions pipeline

```