import os

import pandas as pd
import snowflake.connector
from textblob import TextBlob


# ============================================================
# SNOWFLAKE CONFIGURATION
# ============================================================

ACCOUNT = os.getenv(
    "SNOWFLAKE_ACCOUNT",
    "TBMPXKR-PE66235"
)

USER = os.getenv(
    "SNOWFLAKE_USER",
    "KITTUCHOWDHARY8"
)

PASSWORD = os.getenv(
    "SNOWFLAKE_PASSWORD"
)

WAREHOUSE = os.getenv(
    "SNOWFLAKE_WAREHOUSE",
    "SWIGGY_WH"
)

ROLE = os.getenv(
    "SNOWFLAKE_ROLE",
    "DBT_ROLE"
)


# ============================================================
# TABLES
# ============================================================

SOURCE_TABLE = "SWIGGY.MARTS.FCT_REVIEWS"

TARGET_TABLE = "SWIGGY.AI.REVIEW_SENTIMENT"

BATCH_SIZE = 5000


# ============================================================
# SENTIMENT FUNCTION
# ============================================================

def get_sentiment(text):

    score = float(
        TextBlob(str(text))
        .sentiment
        .polarity
    )

    if score > 0.10:

        return "Positive", score

    elif score < -0.10:

        return "Negative", score

    else:

        return "Neutral", score


# ============================================================
# MAIN
# ============================================================

def main():

    if not PASSWORD:

        raise RuntimeError(
            "SNOWFLAKE_PASSWORD is not set."
        )

    print("========================================")
    print("SWIGGY LOCAL REVIEW SENTIMENT")
    print("========================================")

    connection = snowflake.connector.connect(

        account=ACCOUNT,

        user=USER,

        password=PASSWORD,

        warehouse=WAREHOUSE,

        database="SWIGGY",

        role=ROLE,
    )

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # LOAD REVIEWS
        # ----------------------------------------------------

        print("Loading reviews...")

        cursor.execute(
            f"""
            SELECT
                REVIEW_ID,
                ORDER_ID,
                USER_ID,
                RESTAURANT_ID,
                RATING,
                COMMENT,
                REVIEW_DATE

            FROM {SOURCE_TABLE}

            WHERE COMMENT IS NOT NULL

              AND TRIM(COMMENT) <> ''
            """
        )

        rows = cursor.fetchall()

        if not rows:

            raise RuntimeError(
                "No review comments found."
            )

        df = pd.DataFrame(

            rows,

            columns=[
                "REVIEW_ID",
                "ORDER_ID",
                "USER_ID",
                "RESTAURANT_ID",
                "RATING",
                "COMMENT",
                "REVIEW_DATE",
            ],
        )

        print(
            f"Loaded reviews: {len(df):,}"
        )

        # ----------------------------------------------------
        # PROCESS SENTIMENT
        # ----------------------------------------------------

        results = []

        for row in df.itertuples(
            index=False
        ):

            sentiment, score = get_sentiment(
                row.COMMENT
            )

            results.append(

                (
                    row.REVIEW_ID,
                    row.ORDER_ID,
                    row.USER_ID,
                    row.RESTAURANT_ID,
                    row.RATING,
                    row.COMMENT,
                    row.REVIEW_DATE,
                    sentiment,
                    score,
                )
            )

        print(
            f"Processed reviews: {len(results):,}"
        )

        sentiment_distribution = pd.Series(

            [
                row[7]
                for row in results
            ]

        ).value_counts()

        print("")
        print(
            "Sentiment distribution:"
        )

        print(
            sentiment_distribution
        )

        # ----------------------------------------------------
        # CLEAR OLD DATA
        # ----------------------------------------------------

        print("")
        print(
            f"Refreshing {TARGET_TABLE}..."
        )

        cursor.execute(
            f"TRUNCATE TABLE {TARGET_TABLE}"
        )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        insert_sql = f"""

            INSERT INTO {TARGET_TABLE}

            (
                REVIEW_ID,
                ORDER_ID,
                USER_ID,
                RESTAURANT_ID,
                RATING,
                COMMENT,
                REVIEW_DATE,
                SENTIMENT,
                SENTIMENT_SCORE
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )

        """

        total_rows = len(results)

        for start in range(
            0,
            total_rows,
            BATCH_SIZE
        ):

            batch = results[
                start:
                start + BATCH_SIZE
            ]

            cursor.executemany(
                insert_sql,
                batch
            )

            completed = min(
                start + BATCH_SIZE,
                total_rows
            )

            print(
                f"Inserted "
                f"{completed:,}/"
                f"{total_rows:,}"
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()

        # ----------------------------------------------------
        # VALIDATE ROW COUNT
        # ----------------------------------------------------

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {TARGET_TABLE}
            """
        )

        snowflake_count = (
            cursor.fetchone()[0]
        )

        if snowflake_count != total_rows:

            raise RuntimeError(

                "Row count mismatch. "

                f"Expected {total_rows:,}, "

                f"found {snowflake_count:,}."
            )

        print("")
        print("========================================")
        print("REVIEW SENTIMENT COMPLETED")
        print("========================================")

        print(
            f"Rows processed : {total_rows:,}"
        )

        print(
            f"Rows written   : {snowflake_count:,}"
        )

        print(
            "Status         : SUCCESS"
        )

        print("========================================")

    finally:

        cursor.close()

        connection.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()