from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


# ============================================================
# FIXED CONTAINER PATHS
# ============================================================

DBT_PROJECT_DIR = "/opt/airflow/swiggy_dbt"
DBT_PROFILES_DIR = "/home/airflow/.dbt"
SENTIMENT_SCRIPT = "/opt/airflow/ai/review_sentiment.py"


# ============================================================
# DEFAULT SETTINGS
# ============================================================

default_args = {
    "owner": "swiggy-data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


# ============================================================
# SENTIMENT VALIDATION
# ============================================================

def validate_sentiment():

    import snowflake.connector

    required_variables = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
    ]

    missing = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing:
        raise RuntimeError(
            "Missing Airflow environment variables: "
            + ", ".join(missing)
        )

    connection = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.getenv(
            "SNOWFLAKE_WAREHOUSE",
            "SWIGGY_WH"
        ),
        database="SWIGGY",
        schema="AI",
        role=os.getenv(
            "SNOWFLAKE_ROLE",
            "DBT_ROLE"
        ),
    )

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COUNT(*) AS TOTAL_REVIEWS,
                COUNT_IF(SENTIMENT = 'Positive') AS POSITIVE_REVIEWS,
                COUNT_IF(SENTIMENT = 'Negative') AS NEGATIVE_REVIEWS,
                COUNT_IF(SENTIMENT = 'Neutral') AS NEUTRAL_REVIEWS
            FROM SWIGGY.AI.REVIEW_SENTIMENT
            """
        )

        total, positive, negative, neutral = cursor.fetchone()

        print("========================================")
        print("SENTIMENT VALIDATION")
        print("========================================")
        print(f"TOTAL REVIEWS    : {total}")
        print(f"POSITIVE REVIEWS : {positive}")
        print(f"NEGATIVE REVIEWS : {negative}")
        print(f"NEUTRAL REVIEWS  : {neutral}")
        print("========================================")

        if total == 0:
            raise RuntimeError(
                "REVIEW_SENTIMENT table is empty."
            )

        classified = (
            (positive or 0)
            + (negative or 0)
            + (neutral or 0)
        )

        if classified != total:
            raise RuntimeError(
                f"Sentiment count mismatch. "
                f"Total={total}, Classified={classified}"
            )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM SWIGGY.AI.REVIEW_SENTIMENT
            WHERE SENTIMENT IS NULL
               OR SENTIMENT NOT IN (
                   'Positive',
                   'Negative',
                   'Neutral'
               )
            """
        )

        invalid = cursor.fetchone()[0]

        if invalid > 0:
            raise RuntimeError(
                f"Found {invalid} invalid sentiment records."
            )

        print("SENTIMENT VALIDATION SUCCESSFUL")

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DAG
# ============================================================

with DAG(
    dag_id="swiggy_pipeline",

    description=(
        "Swiggy end-to-end data engineering pipeline "
        "using Snowflake, dbt and local NLP sentiment"
    ),

    start_date=datetime(2026, 1, 1),

    schedule=None,

    catchup=False,

    max_active_runs=1,

    default_args=default_args,

    tags=[
        "swiggy",
        "snowflake",
        "dbt",
        "sentiment",
        "data-engineering",
    ],
) as dag:

    # ========================================================
    # 1. ENVIRONMENT CHECK
    # ========================================================

    check_environment = BashOperator(
        task_id="check_environment",

        bash_command=f"""
set -e

echo "========================================"
echo "SWIGGY ENVIRONMENT CHECK"
echo "========================================"

echo "DBT PROJECT:"
echo "{DBT_PROJECT_DIR}"

echo "DBT PROFILES:"
echo "{DBT_PROFILES_DIR}"

echo "SENTIMENT SCRIPT:"
echo "{SENTIMENT_SCRIPT}"

echo ""
echo "Checking required files..."

test -d "{DBT_PROJECT_DIR}"

test -f "{DBT_PROJECT_DIR}/dbt_project.yml"

test -f "{DBT_PROFILES_DIR}/profiles.yml"

test -f "{SENTIMENT_SCRIPT}"

echo "Required files found."

echo ""
echo "Python:"
python --version

echo ""
echo "dbt:"
dbt --version

echo ""
echo "TextBlob:"
python -c "from textblob import TextBlob; print(TextBlob('test').sentiment)"

echo ""
echo "Environment check successful."
""",
    )

    # ========================================================
    # 2. DBT DEBUG
    # ========================================================

    dbt_debug = BashOperator(
        task_id="dbt_debug",

        bash_command=f"""
set -e

cd "{DBT_PROJECT_DIR}"

dbt debug \
--profiles-dir "{DBT_PROFILES_DIR}"
""",
    )

    # ========================================================
    # 3. DBT STAGING
    # ========================================================

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",

        bash_command=f"""
set -e

cd "{DBT_PROJECT_DIR}"

dbt run \
--select staging \
--profiles-dir "{DBT_PROFILES_DIR}"
""",
    )

    # ========================================================
    # 4. TEST STAGING
    # ========================================================

    dbt_test_staging = BashOperator(
        task_id="dbt_test_staging",

        bash_command=f"""
set -e

cd "{DBT_PROJECT_DIR}"

dbt test \
--select staging \
--profiles-dir "{DBT_PROFILES_DIR}"
""",
    )

    # ========================================================
    # 5. DBT MARTS
    # ========================================================

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",

        bash_command=f"""
set -e

cd "{DBT_PROJECT_DIR}"

dbt run \
--select marts \
--profiles-dir "{DBT_PROFILES_DIR}"
""",
    )

    # ========================================================
    # 6. TEST MARTS
    # ========================================================

    dbt_test_marts = BashOperator(
        task_id="dbt_test_marts",

        bash_command=f"""
set -e

cd "{DBT_PROJECT_DIR}"

dbt test \
--select marts \
--profiles-dir "{DBT_PROFILES_DIR}"
""",
    )

    # ========================================================
    # 7. LOCAL TEXTBLOB SENTIMENT
    # ========================================================

    review_sentiment = BashOperator(
        task_id="review_sentiment",

        bash_command=f"""
set -e

echo "========================================"
echo "LOCAL REVIEW SENTIMENT"
echo "========================================"

test -f "{SENTIMENT_SCRIPT}"

python "{SENTIMENT_SCRIPT}"
""",
    )

    # ========================================================
    # 8. VALIDATE SENTIMENT
    # ========================================================

    validate_sentiment_task = PythonOperator(
        task_id="validate_sentiment",

        python_callable=validate_sentiment,
    )

    # ========================================================
    # 9. PIPELINE COMPLETE
    # ========================================================

    pipeline_complete = BashOperator(
        task_id="pipeline_complete",

        bash_command="""
echo "========================================"
echo "SWIGGY PIPELINE COMPLETE"
echo "========================================"

echo ""
echo "LOCAL CSV DATA"
echo "      ↓"
echo "SNOWFLAKE RAW"
echo "      ↓"
echo "DBT STAGING"
echo "      ↓"
echo "STAGING TESTS"
echo "      ↓"
echo "DBT MARTS"
echo "      ↓"
echo "MARTS TESTS"
echo "      ↓"
echo "LOCAL TEXTBLOB SENTIMENT"
echo "      ↓"
echo "SENTIMENT VALIDATION"
echo "      ↓"
echo "PIPELINE COMPLETE"

echo ""
echo "All pipeline stages completed successfully."
""",
    )

    # ========================================================
    # DEPENDENCIES
    # ========================================================

    (
        check_environment
        >> dbt_debug
        >> dbt_run_staging
        >> dbt_test_staging
        >> dbt_run_marts
        >> dbt_test_marts
        >> review_sentiment
        >> validate_sentiment_task
        >> pipeline_complete
    )