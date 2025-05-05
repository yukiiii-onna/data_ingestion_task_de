import streamlit as st
import duckdb
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths
DUCKDB_PATH = Path("/app/db/my_duck.db")
SQL_DIR = Path("/app/airflow/dags/ETLUserMetrics/sql/reporting")

# Load SQL file content
def load_query(file_name):
    full_path = SQL_DIR / file_name
    if not full_path.exists():
        st.warning(f"SQL file not found: {full_path}")
        return ""
    return full_path.read_text()

# Execute SQL query safely
def run_query(name, query):
    try:
        con = duckdb.connect(database=str(DUCKDB_PATH), read_only=True)
        con.execute(query)
        result = con.fetchdf()
        print(f"Result for {name}:\n{result}")
        return name, result
    except Exception as e:
        print(f"Error running query '{name}': {e}")
        return name, None
    finally:
        try:
            con.close()
        except:
            pass

# Define the SQL queries to load and run
sql_files = {
    "percent": "germany_gmail_percentage.sql",
    "top3": "top_gmail_countries.sql",
    "over60": "over60_gmail_users.sql"
}

# Load query text from files
queries = {name: load_query(fname) for name, fname in sql_files.items()}

# Run queries in parallel
results = {}
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(run_query, name, query): name for name, query in queries.items()}
    for future in as_completed(futures):
        name, result = future.result()
        results[name] = result

# Streamlit UI
st.title("User Insights Dashboard")
st.caption("Generated using SQL on DuckDB")

# 1. Germany + Gmail %
st.header("1. Percentage of Users in Germany using Gmail")
df_percent = results.get("percent")
if df_percent is not None and not df_percent.empty:
    val = df_percent.iloc[0, 0]
    st.metric("Germany + Gmail Users", f"{val:.2f}%" if val else "0.00%")
else:
    st.warning("No data returned for Germany + Gmail %")

# 2. Top 3 Gmail countries
st.header("2. Top 3 Countries Using Gmail")
df_top3 = results.get("top3")
if df_top3 is not None and not df_top3.empty:
    st.dataframe(df_top3)
else:
    st.warning("No data returned for top Gmail countries.")

# 3. Gmail users over 60
st.header("3. Gmail Users Over 60 Years Old")
df_over60 = results.get("over60")
if df_over60 is not None and not df_over60.empty:
    val = df_over60.iloc[0, 0]
    st.metric("Users > 60 (Gmail)", int(val) if val else 0)
else:
    st.warning("No data returned for Gmail users over 60.")
