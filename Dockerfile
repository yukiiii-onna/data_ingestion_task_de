FROM python:3.10-slim

ARG AIRFLOW_VERSION=2.8.2
ARG PYTHON_VERSION=3.10
ARG CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Install build tools (needed for psutil and others)
RUN apt-get update && \
    apt-get install -y gcc build-essential libssl-dev libffi-dev python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
RUN pip install --no-cache-dir -r requirements.txt --constraint "${CONSTRAINT_URL}"

COPY . .

# Install DuckDB CLI for ARM64 (Mac M1/M2)
RUN apt-get update && \
    apt-get install -y unzip curl && \
    curl -L https://github.com/duckdb/duckdb/releases/download/v0.10.0/duckdb_cli-linux-aarch64.zip -o duckdb.zip && \
    unzip duckdb.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/duckdb && \
    rm duckdb.zip


# CMD ["bash", "-c", "airflow db init && airflow scheduler & airflow webserver"]
