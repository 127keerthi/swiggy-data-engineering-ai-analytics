# ============================================================
# SWIGGY RAG CHATBOT
# ============================================================
# Project:
# End-to-End SWIGGY Food Delivery Data Engineering + AI
#
# Flow:
# Snowflake AI.REVIEW_SENTIMENT
#          ↓
# Review Text
#          ↓
# Sentence Transformer Embeddings
#          ↓
# FAISS Vector Database
#          ↓
# Similarity Search
#          ↓
# RAG Context
#          ↓
# Answer User Question
# ============================================================

import os
import sys
import pandas as pd
import snowflake.connector
import faiss

from sentence_transformers import SentenceTransformer


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

ACCOUNT = "TBMPXKR-PE66235"

DATABASE = "SWIGGY"
SCHEMA = "AI"
TABLE = "REVIEW_SENTIMENT"

ROLE = "DBT_ROLE"
WAREHOUSE = "SWIGGY_WH"


# ============================================================
# 2. HEADER
# ============================================================

print("=" * 70)
print("SWIGGY RAG CHATBOT")
print("=" * 70)


# ============================================================
# 3. GET SNOWFLAKE CREDENTIALS
# ============================================================

username = input("Enter your Snowflake username: ").strip()
password = input("Enter your Snowflake password: ")


# ============================================================
# 4. CONNECT TO SNOWFLAKE
# ============================================================

print("\nConnecting to Snowflake...")

try:

    conn = snowflake.connector.connect(
        account=ACCOUNT,
        user=username,
        password=password,
        warehouse=WAREHOUSE,
        database=DATABASE,
        schema=SCHEMA,
        role=ROLE
    )

    print("Snowflake connection successful!")

except Exception as e:

    print("\nSnowflake connection failed.")
    print("Error:", e)
    sys.exit(1)


# ============================================================
# 5. LOAD REVIEWS
# ============================================================

print("\nLoading reviews from Snowflake...")

query = f"""
SELECT
    REVIEW_ID,
    ORDER_ID,
    USER_ID,
    RESTAURANT_ID,
    RATING,
    COMMENT,
    REVIEW_DATE,
    SENTIMENT
FROM {DATABASE}.{SCHEMA}.{TABLE}
WHERE COMMENT IS NOT NULL
  AND TRIM(COMMENT) <> ''
"""

try:

    df = pd.read_sql(query, conn)

    # IMPORTANT:
    # Snowflake returns column names in uppercase.
    # Convert them to lowercase for Python.
    df.columns = df.columns.str.lower()

    print(f"Reviews loaded: {len(df):,}")

except Exception as e:

    print("\nError loading reviews.")
    print("Error:", e)

    conn.close()
    sys.exit(1)


# ============================================================
# 6. CHECK REQUIRED COLUMN
# ============================================================

required_columns = [
    "review_id",
    "order_id",
    "user_id",
    "restaurant_id",
    "rating",
    "comment",
    "review_date",
    "sentiment"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    print("\nMissing columns:")
    print(missing_columns)

    print("\nAvailable columns:")
    print(list(df.columns))

    conn.close()
    sys.exit(1)


# ============================================================
# 7. CLEAN REVIEW TEXT
# ============================================================

df["comment"] = (
    df["comment"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df = df[df["comment"] != ""]

df = df.reset_index(drop=True)

print(f"Valid reviews for RAG: {len(df):,}")


# ============================================================
# 8. DISPLAY SENTIMENT SUMMARY
# ============================================================

print("\nSentiment distribution:")

print(
    df["sentiment"]
    .value_counts(dropna=False)
)


# ============================================================
# 9. LOAD EMBEDDING MODEL
# ============================================================

print("\nLoading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded successfully!")


# ============================================================
# 10. CREATE REVIEW EMBEDDINGS
# ============================================================

print("\nCreating embeddings...")

# For a laptop-friendly project we use a manageable number
# of reviews for the local FAISS demonstration.
#
# You can increase this later.

MAX_REVIEWS = 50000

rag_df = df.head(MAX_REVIEWS).copy()

texts = rag_df["comment"].tolist()

embeddings = model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True
)

print(
    f"Embeddings created: {len(embeddings):,}"
)


# ============================================================
# 11. CREATE FAISS VECTOR INDEX
# ============================================================

print("\nCreating FAISS vector index...")

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(
    embeddings.astype("float32")
)

print(
    f"FAISS index created with {index.ntotal:,} vectors."
)


# ============================================================
# 12. RAG SEARCH FUNCTION
# ============================================================

def search_reviews(question, top_k=5):

    """
    Convert user question into an embedding
    and find the most relevant reviews.
    """

    question_embedding = model.encode(
        [question],
        normalize_embeddings=True
    )

    question_embedding = (
        question_embedding
        .astype("float32")
    )

    scores, indices = index.search(
        question_embedding,
        top_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        row = rag_df.iloc[idx]

        results.append(
            {
                "score": float(score),
                "review_id": row["review_id"],
                "restaurant_id": row["restaurant_id"],
                "rating": row["rating"],
                "sentiment": row["sentiment"],
                "comment": row["comment"],
                "review_date": row["review_date"]
            }
        )

    return results


# ============================================================
# 13. GENERATE RAG RESPONSE
# ============================================================

def generate_answer(question, results):

    """
    Generate a grounded answer using retrieved reviews.

    This version does not require an external LLM API.
    It summarizes the retrieved review evidence directly.
    """

    if not results:

        return "I could not find relevant SWIGGY reviews."


    sentiments = []

    ratings = []

    for result in results:

        sentiment = str(
            result["sentiment"]
        ).lower()

        sentiments.append(sentiment)

        try:
            ratings.append(
                float(result["rating"])
            )

        except:

            pass


    # Sentiment counts

    positive = sum(
        "positive" in s
        for s in sentiments
    )

    neutral = sum(
        "neutral" in s
        for s in sentiments
    )

    negative = sum(
        "negative" in s
        for s in sentiments
    )


    # Average rating

    average_rating = None

    if ratings:

        average_rating = (
            sum(ratings) / len(ratings)
        )


    # Build answer

    answer = []

    answer.append(
        f"Based on {len(results)} relevant SWIGGY reviews:"
    )


    if average_rating is not None:

        answer.append(
            f"- Average rating among retrieved reviews: "
            f"{average_rating:.2f}"
        )


    answer.append(
        f"- Positive reviews: {positive}"
    )

    answer.append(
        f"- Neutral reviews: {neutral}"
    )

    answer.append(
        f"- Negative reviews: {negative}"
    )


    answer.append(
        "\nRelevant review evidence:"
    )


    for i, result in enumerate(
        results,
        start=1
    ):

        comment = result["comment"]

        if len(comment) > 250:

            comment = comment[:250] + "..."

        answer.append(
            f"{i}. "
            f"[{result['sentiment']}] "
            f"{comment}"
        )


    return "\n".join(answer)


# ============================================================
# 14. INTERACTIVE RAG CHATBOT
# ============================================================

print("\n" + "=" * 70)
print("SWIGGY RAG CHATBOT READY")
print("=" * 70)

print(
    "\nAsk questions about customer reviews."
)

print(
    "Type 'exit' to stop."
)

print("=" * 70)


while True:

    try:

        question = input(
            "\nYou: "
        ).strip()

    except KeyboardInterrupt:

        print("\n\nExiting...")
        break


    if question.lower() in [
        "exit",
        "quit",
        "q"
    ]:

        print(
            "\nSWIGGY RAG chatbot stopped."
        )

        break


    if not question:

        continue


    print(
        "\nSearching relevant reviews..."
    )


    results = search_reviews(
        question,
        top_k=5
    )


    print(
        f"Retrieved {len(results)} relevant reviews."
    )


    # Display similarity scores

    print("\nTop matching reviews:")

    for i, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n{i}. "
            f"Similarity: {result['score']:.4f}"
        )

        print(
            f"Sentiment: {result['sentiment']}"
        )

        print(
            f"Rating: {result['rating']}"
        )

        print(
            f"Review: {result['comment'][:300]}"
        )


    # Generate answer

    answer = generate_answer(
        question,
        results
    )


    print(
        "\n" + "-" * 70
    )

    print("RAG ANSWER")

    print("-" * 70)

    print(answer)

    print("-" * 70)


# ============================================================
# 15. CLOSE CONNECTION
# ============================================================

conn.close()

print("\nSnowflake connection closed.")
print("SWIGGY RAG pipeline completed.")