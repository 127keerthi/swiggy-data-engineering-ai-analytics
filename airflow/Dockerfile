FROM apache/airflow:latest

USER airflow

# ============================================================
# Python dependencies for Swiggy Data Engineering Pipeline
# ============================================================

RUN pip install --no-cache-dir \
    textblob==0.20.1 \
    dbt-snowflake==1.12.0