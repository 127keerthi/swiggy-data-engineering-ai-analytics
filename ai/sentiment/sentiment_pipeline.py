import os
import getpass
from decimal import Decimal
from datetime import datetime

import snowflake.connector
from textblob import TextBlob


# ============================================================
# SWIGGY SENTIMENT ANALYSIS PIPELINE
# ============================================================

ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "TBMPXKR-PE66235")
USER = os.getenv("SNOWFLAKE_USER")

ROLE = "DBT_ROLE"
WAREHOUSE = "SWIGGY_WH"
DATABASE = "SWIGGY"
SCHEMA = "AI"

SOURCE_TABLE = "SWIGGY.MARTS.FCT_REVIEWS"
TARGET_TABLE = "SWIGGY.AI.REVIEW_SENTIMENT"

BATCH_SIZE = 5000


# ============================================================
# CREDENTIALS
# ============================================================

if not USER:
    USER = input("Enter your Snowflake username: ").strip()

PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

if not PASSWORD:
    PASSWORD = getpass.getpass("Enter your Snowflake password: ")


# ============================================================
# SENTIMENT ANALYSIS
# ============================================================

def analyze_sentiment(comment):

    if comment is None or not str(comment).strip():
        return "NEUTRAL", 0.0

    text = str(comment).strip()

    try:
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0.10:
            sentiment = "POSITIVE"

        elif polarity < -0.10:
            sentiment = "NEGATIVE"

        else:
            sentiment = "NEUTRAL"

        return sentiment, round(float(polarity), 4)

    except Exception:
        return "NEUTRAL", 0.0


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

def create_connection():

    print("\nConnecting to Snowflake...")

    conn = snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        password=PASSWORD,
        role=ROLE,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        paramstyle="qmark"
    )

    print("Snowflake connection successful.")

    return conn


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = datetime.now()

    connection = None
    read_cursor = None
    write_cursor = None

    try:

        # ====================================================
        # CONNECT
        # ====================================================

        connection = create_connection()

        # IMPORTANT:
        # Separate cursors are used for reading and writing.
        read_cursor = connection.cursor()
        write_cursor = connection.cursor()

        # ====================================================
        # CHECK SOURCE TABLE
        # ====================================================

        print("\nChecking source table...")

        read_cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {SOURCE_TABLE}
            """
        )

        source_count = read_cursor.fetchone()[0]

        print(f"Reviews available: {source_count:,}")

        if source_count == 0:
            print("No reviews found.")
            return

        # ====================================================
        # CHECK SOURCE COLUMNS
        # ====================================================

        print("\nChecking source columns...")

        read_cursor.execute(
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
            LIMIT 1
            """
        )

        test_row = read_cursor.fetchone()

        if test_row is None:
            print("Source table contains no rows.")
            return

        print(f"Source columns detected: {len(test_row)}")

        if len(test_row) != 7:

            raise RuntimeError(
                f"Expected 7 columns from {SOURCE_TABLE}, "
                f"but received {len(test_row)} columns."
            )

        print("Source structure verified.")

        # ====================================================
        # CLEAR TARGET TABLE
        # ====================================================

        print("\nClearing previous sentiment results...")

        write_cursor.execute(
            f"""
            TRUNCATE TABLE {TARGET_TABLE}
            """
        )

        connection.commit()

        print("Target table cleared.")

        # ====================================================
        # OPEN REVIEW CURSOR
        # ====================================================

        print("\nReading reviews...")

        read_cursor.execute(
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
            ORDER BY REVIEW_ID
            """
        )

        # ====================================================
        # INSERT SQL
        # ====================================================

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # ====================================================
        # COUNTERS
        # ====================================================

        processed = 0
        positive = 0
        negative = 0
        neutral = 0

        # ====================================================
        # PROCESS REVIEWS
        # ====================================================

        print("\nStarting sentiment analysis...")
        print("-" * 60)

        while True:

            rows = read_cursor.fetchmany(BATCH_SIZE)

            if not rows:
                break

            batch = []

            for row in rows:

                # Safety check
                if len(row) != 7:

                    raise RuntimeError(
                        f"Unexpected row structure. "
                        f"Expected 7 values but received {len(row)}."
                    )

                (
                    review_id,
                    order_id,
                    user_id,
                    restaurant_id,
                    rating,
                    comment,
                    review_date
                ) = row

                # --------------------------------------------
                # SENTIMENT
                # --------------------------------------------

                sentiment, sentiment_score = analyze_sentiment(
                    comment
                )

                # --------------------------------------------
                # RATING
                # --------------------------------------------

                if isinstance(rating, Decimal):
                    rating = float(rating)

                # --------------------------------------------
                # ADD TO BATCH
                # --------------------------------------------

                batch.append(
                    (
                        review_id,
                        order_id,
                        user_id,
                        restaurant_id,
                        rating,
                        comment,
                        review_date,
                        sentiment,
                        sentiment_score
                    )
                )

                # --------------------------------------------
                # COUNTERS
                # --------------------------------------------

                if sentiment == "POSITIVE":
                    positive += 1

                elif sentiment == "NEGATIVE":
                    negative += 1

                else:
                    neutral += 1

                processed += 1

            # =================================================
            # WRITE BATCH
            # =================================================

            write_cursor.executemany(
                insert_sql,
                batch
            )

            connection.commit()

            # =================================================
            # PROGRESS
            # =================================================

            percentage = (
                processed / source_count
            ) * 100

            print(
                f"Processed: {processed:,} / "
                f"{source_count:,} "
                f"({percentage:.2f}%)"
            )

        # ====================================================
        # FINAL COUNT
        # ====================================================

        write_cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {TARGET_TABLE}
            """
        )

        target_count = write_cursor.fetchone()[0]

        # ====================================================
        # FINAL OUTPUT
        # ====================================================

        print("\n")
        print("=" * 65)
        print("SWIGGY SENTIMENT PIPELINE COMPLETED")
        print("=" * 65)

        print(f"Source reviews  : {source_count:,}")
        print(f"Processed       : {processed:,}")
        print(f"Positive        : {positive:,}")
        print(f"Negative        : {negative:,}")
        print(f"Neutral         : {neutral:,}")
        print(f"Target rows     : {target_count:,}")

        # ====================================================
        # SENTIMENT SUMMARY
        # ====================================================

        write_cursor.execute(
            f"""
            SELECT
                SENTIMENT,
                COUNT(*) AS REVIEW_COUNT
            FROM {TARGET_TABLE}
            GROUP BY SENTIMENT
            ORDER BY REVIEW_COUNT DESC
            """
        )

        results = write_cursor.fetchall()

        print("\nSentiment Summary")
        print("-" * 40)

        for sentiment, count in results:

            print(
                f"{sentiment:<12} : {count:,}"
            )

        # ====================================================
        # SAMPLE RESULTS
        # ====================================================

        write_cursor.execute(
            f"""
            SELECT
                REVIEW_ID,
                RATING,
                COMMENT,
                SENTIMENT,
                SENTIMENT_SCORE
            FROM {TARGET_TABLE}
            WHERE COMMENT IS NOT NULL
            LIMIT 10
            """
        )

        sample_results = write_cursor.fetchall()

        print("\nSample Sentiment Results")
        print("-" * 65)

        for row in sample_results:

            review_id, rating, comment, sentiment, score = row

            comment_text = str(comment)

            if len(comment_text) > 80:
                comment_text = comment_text[:80] + "..."

            print(f"\nReview ID : {review_id}")
            print(f"Rating    : {rating}")
            print(f"Comment   : {comment_text}")
            print(f"Sentiment : {sentiment}")
            print(f"Score     : {score}")

        # ====================================================
        # EXECUTION TIME
        # ====================================================

        end_time = datetime.now()
        duration = end_time - start_time

        print("\n" + "=" * 65)
        print(f"Execution time: {duration}")
        print("=" * 65)

    except Exception as error:

        print("\n")
        print("=" * 65)
        print("SWIGGY SENTIMENT PIPELINE FAILED")
        print("=" * 65)

        print(f"Error: {error}")

        if connection:
            connection.rollback()

        raise

    finally:

        if read_cursor:
            read_cursor.close()

        if write_cursor:
            write_cursor.close()

        if connection:
            connection.close()

        print("\nSnowflake connection closed.")


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":
    main()