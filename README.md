```markdown
# Faker API Data Flow

A Dockerized pipeline that ingests synthetic person data from a public API,
anonymizes PII,
stores it in DuckDB, and generates analytical reports using SQL and Streamlit.

---

## Project Overview

This project simulates a real-world data ingestion pipeline that processes external
third-party data securely and efficiently.
The pipeline fetches synthetic user data from the [Faker API](https://fakerapi.it/),
anonymizes sensitive fields (PII), stores the transformed data in a local DuckDB database, and generates SQL-based reports for analytical insights.

It demonstrates:
- Scalable data ingestion from external APIs
- PII anonymization through masking and generalization
- SQL reporting on anonymized datasets
- Containerized orchestration with Docker and Apache Airflow

This solution was developed as part of a ** Data Engineer take-home challenge **
and focuses on production-simulated design and code quality.


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
  - Percentage of German users using Gmail
  - Top 3 countries using Gmail
  - Count of Gmail users over age 60
- Visualizes results with a Streamlit dashboard
- Fully orchestrated with Apache Airflow
- Fully containerized with Docker for consistent local development

---
````


## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/data_ingestion_task_de.git
cd data_ingestion_task_de
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

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
  ROUND(
    100.0 * SUM(CASE WHEN country = 'Germany' AND email like '%gmail%' THEN 1 ELSE 0 END) 
    / COUNT(*), 2
  ) AS germany_gmail_percentage
FROM persons_anonymized;
```

**2. Top 3 Gmail Countries:**

```sql
SELECT
  country,
  COUNT(*) AS gmail_user_count,
  DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS rank
FROM persons_anonymized
WHERE email LIKE '%gmail%'
GROUP BY country
QUALIFY rank <= 3;
```

**3. Gmail Users Over 60:**

```sql
SELECT COUNT(*) AS over_60_gmail_users
FROM persons_anonymized
WHERE email like '%gmail%' AND age_group IN ('[60-70]', '[70-80]', '[80-90]', '[90-100]');
```

---

## 🚀 Production Readiness & Improvements

This project simulates a real-world data pipeline. Below are improvements and production-grade considerations:

### Data Quality & Schema Stability

* Schema drift detection via stored schema signatures (future work)
* Great Expectations integration planned for:
  * Null checks
  * Row count 
  * Domain/value validation
* Formal data contracts for ingestion

### Pipeline Design

* Handle late-arriving
* Retain raw data for reprocessing/backfilling
* Support re-runs and backfills gracefully
* Avoid table drops; use migration/versioning

### Architecture & Modularity

* Automate everything via Makefile, Docker, Airflow, and future CI/CD

### Observability & Monitoring

* Metadata logging for each run
* Future Slack/email alerting for failures or drift
* Track KPIs: DAG runtime, freshness, volume

### Cloud Readiness

* Cost-aware practices for cloud DBs
* Use partition pruning, materialized views

### Testing & Documentation

* Full unit tests and SQL query validation
* Future: GitHub Actions pipeline

```
