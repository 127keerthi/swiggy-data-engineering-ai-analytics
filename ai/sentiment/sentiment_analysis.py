import os
import getpass
import pandas as pd
import snowflake.connector
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ============================================================
# SWIGGY AI SENTIMENT ANALYSIS
# ============================================================

print("=" * 70)
print("SWIGGY AI SENTIMENT ANALYSIS")
print("=" * 70)


# ============================================================
# 1. SNOWFLAKE LOGIN
# ============================================================

print("\nConnecting to Snowflake...")

ACCOUNT = "TBMPXKR-PE66235"
DATABASE = "SWIGGY"
SCHEMA = "AI"
ROLE = "DBT_ROLE"
WAREHOUSE = "SWIGGY_WH"

# Use environment variable if available.
# Otherwise ask securely for the password.
USERNAME = os.getenv("SNOWFLAKE_USER")

if not USERNAME:
    USERNAME = input("Enter your Snowflake username: ").strip()

PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

if not PASSWORD:
    PASSWORD = getpass.getpass("Enter your Snowflake password: ")


try:
    conn = snowflake.connector.connect(
        account=ACCOUNT,
        user=USERNAME,
        password=PASSWORD,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE
    )

    print("Snowflake connection successful!")

except Exception as e:
    print("\nSnowflake connection failed.")
    print("Error:", e)
    print("\nCheck:")
    print("1. Username is correct")
    print("2. Password is correct")
    print("3. Account is TBMPXKR-PE66235")
    print("4. The Snowflake user can log in using password authentication")
    raise SystemExit(1)


# ============================================================
# 2. CREATE AI SCHEMA
# ============================================================

cursor = conn.cursor()

cursor.execute("""
    CREATE SCHEMA IF NOT EXISTS SWIGGY.AI
""")

print("AI schema verified.")


# ============================================================
# 3. LOAD REVIEWS FROM MARTS
# ============================================================

print("\nLoading reviews from Snowflake...")

query = """
SELECT
    review_id,
    order_id,
    user_id,
    restaurant_id,
    rating,
    comment,
    review_date
FROM SWIGGY.MARTS.FCT_REVIEWS
WHERE comment IS NOT NULL
"""

try:

    cursor.execute(query)

    rows = cursor.fetchall()

    columns = [col[0].lower() for col in cursor.description]

    df = pd.DataFrame(rows, columns=columns)

    print(f"Reviews loaded: {len(df):,}")

except Exception as e:

    print("\nFailed to load reviews.")
    print("Error:", e)

    cursor.close()
    conn.close()

    raise SystemExit(1)


# ============================================================
# 4. VALIDATE DATA
# ============================================================

print("\nAvailable columns:")

for column in df.columns:
    print(" -", column)


if "comment" not in df.columns:

    print("\nERROR: comment column was not found.")

    print("\nColumns returned from Snowflake:")
    print(df.columns.tolist())

    cursor.close()
    conn.close()

    raise SystemExit(1)


# Convert comments to safe strings

df["comment"] = df["comment"].fillna("").astype(str)

# Remove empty comments

df = df[df["comment"].str.strip() != ""].copy()

print(f"Reviews with valid comments: {len(df):,}")


# ============================================================
# 5. INITIALIZE VADER
# ============================================================

print("\nInitializing VADER sentiment analyzer...")

analyzer = SentimentIntensityAnalyzer()


# ============================================================
# 6. SENTIMENT FUNCTION
# ============================================================

def get_sentiment(text):

    try:

        scores = analyzer.polarity_scores(text)

        compound = scores["compound"]

        if compound >= 0.05:
            sentiment = "Positive"

        elif compound <= -0.05:
            sentiment = "Negative"

        else:
            sentiment = "Neutral"

        return sentiment

    except Exception:

        return "Neutral"


# ============================================================
# 7. CALCULATE SENTIMENT
# ============================================================

print("\nRunning sentiment analysis...")

df["sentiment"] = df["comment"].apply(get_sentiment)


# ============================================================
# 8. CALCULATE SENTIMENT SCORE
# ============================================================

print("Calculating sentiment scores...")

def get_compound_score(text):

    try:

        return analyzer.polarity_scores(text)["compound"]

    except Exception:

        return 0.0


df["sentiment_score"] = df["comment"].apply(get_compound_score)


# ============================================================
# 9. SHOW RESULTS
# ============================================================

print("\n" + "=" * 70)
print("SENTIMENT ANALYSIS COMPLETED")
print("=" * 70)

print("\nSentiment distribution:")

print(
    df["sentiment"]
    .value_counts()
    .to_string()
)


print("\nSample results:")

print(
    df[
        [
            "review_id",
            "restaurant_id",
            "rating",
            "comment",
            "sentiment",
            "sentiment_score"
        ]
    ].head(10).to_string(index=False)
)


# ============================================================
# 10. CREATE AI TABLE
# ============================================================

print("\nCreating SWIGGY.AI.REVIEW_SENTIMENT table...")

create_table_sql = """

CREATE OR REPLACE TABLE SWIGGY.AI.REVIEW_SENTIMENT (

    review_id VARCHAR,

    order_id VARCHAR,

    user_id VARCHAR,

    restaurant_id VARCHAR,

    rating NUMBER(3,2),

    comment VARCHAR,

    review_date DATE,

    sentiment VARCHAR,

    sentiment_score FLOAT

)

"""

cursor.execute(create_table_sql)

print("AI table created.")


# ============================================================
# 11. PREPARE DATA FOR SNOWFLAKE
# ============================================================

print("\nPreparing sentiment results for Snowflake...")

output_df = df[
    [
        "review_id",
        "order_id",
        "user_id",
        "restaurant_id",
        "rating",
        "comment",
        "review_date",
        "sentiment",
        "sentiment_score"
    ]
].copy()


# ============================================================
# 12. INSERT DATA IN BATCHES
# ============================================================

insert_sql = """

INSERT INTO SWIGGY.AI.REVIEW_SENTIMENT
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

print("Uploading sentiment results...")

batch_size = 5000

total_rows = len(output_df)

for start in range(0, total_rows, batch_size):

    batch = output_df.iloc[start:start + batch_size]

    data = []

    for _, row in batch.iterrows():

        data.append(
            (
                row["review_id"],
                row["order_id"],
                row["user_id"],
                row["restaurant_id"],
                row["rating"],
                row["comment"],
                row["review_date"],
                row["sentiment"],
                float(row["sentiment_score"])
            )
        )

    cursor.executemany(insert_sql, data)

    print(
        f"Uploaded {min(start + batch_size, total_rows):,}"
        f" / {total_rows:,}"
    )


# ============================================================
# 13. COMMIT
# ============================================================

conn.commit()

print("\nData successfully stored in Snowflake!")


# ============================================================
# 14. VALIDATE SNOWFLAKE TABLE
# ============================================================

print("\nValidating AI table...")

cursor.execute("""
    SELECT COUNT(*)
    FROM SWIGGY.AI.REVIEW_SENTIMENT
""")

count = cursor.fetchone()[0]

print(f"Rows in REVIEW_SENTIMENT: {count:,}")


# ============================================================
# 15. SENTIMENT SUMMARY
# ============================================================

print("\nSentiment summary from Snowflake:")

cursor.execute("""
    SELECT
        sentiment,
        COUNT(*) AS review_count
    FROM SWIGGY.AI.REVIEW_SENTIMENT
    GROUP BY sentiment
    ORDER BY review_count DESC
""")

summary = cursor.fetchall()

for sentiment, review_count in summary:

    print(
        f"{sentiment}: {review_count:,}"
    )


# ============================================================
# 16. CLOSE CONNECTION
# ============================================================

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("SWIGGY AI SENTIMENT PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)