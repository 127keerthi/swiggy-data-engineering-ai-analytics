"""
SWIGGY RAG ENGINE
-----------------
Retrieval-Augmented Generation engine for SWIGGY customer reviews.

Pipeline:
Snowflake REVIEWS
        ↓
Review embeddings
        ↓
FAISS vector index
        ↓
Semantic similarity search
        ↓
Evidence-based response
"""

import os
import re
import numpy as np
import pandas as pd
import snowflake.connector
import faiss

from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "TBMPXKR-PE66235")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")

SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "SWIGGY_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "SWIGGY")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "MARTS")

MODEL_NAME = "all-MiniLM-L6-v2"

TOP_K = 5
MAX_REVIEWS = 50000


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

def get_connection():
    """Create Snowflake connection."""

    if not SNOWFLAKE_USER:
        raise ValueError(
            "SNOWFLAKE_USER environment variable is not set."
        )

    if not SNOWFLAKE_PASSWORD:
        raise ValueError(
            "SNOWFLAKE_PASSWORD environment variable is not set."
        )

    conn = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
    )

    return conn


# ============================================================
# LOAD REVIEWS
# ============================================================

def load_reviews(limit=MAX_REVIEWS):
    """
    Load customer reviews from Snowflake.

    Uses FCT_REVIEWS from the dbt MARTS layer.
    """

    conn = get_connection()

    query = f"""
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
          AND TRIM(comment) <> ''
        LIMIT {int(limit)}
    """

    try:
        df = pd.read_sql(query, conn)

    finally:
        conn.close()

    if df.empty:
        raise ValueError("No customer reviews found in Snowflake.")

    # Standardize column names
    df.columns = [column.lower() for column in df.columns]

    # Clean comments
    df["comment"] = (
        df["comment"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Remove empty reviews
    df = df[df["comment"] != ""].reset_index(drop=True)

    return df


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """Clean review/question text before embedding."""

    text = str(text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# EMBEDDING MODEL
# ============================================================

def load_embedding_model():
    """
    Load Sentence Transformer embedding model.
    """

    return SentenceTransformer(MODEL_NAME)


# ============================================================
# CREATE FAISS INDEX
# ============================================================

def create_faiss_index(df, model):
    """
    Create FAISS vector index from customer reviews.
    """

    texts = df["comment"].apply(clean_text).tolist()

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


# ============================================================
# RAG ENGINE CLASS
# ============================================================

class SwiggyRAG:

    def __init__(self, max_reviews=MAX_REVIEWS):

        print("=" * 70)
        print("INITIALIZING SWIGGY RAG ENGINE")
        print("=" * 70)

        print("\nLoading embedding model...")

        self.model = load_embedding_model()

        print("Embedding model loaded.")

        print("\nLoading reviews from Snowflake...")

        self.reviews = load_reviews(max_reviews)

        print(f"Reviews loaded: {len(self.reviews):,}")

        print("\nCreating FAISS vector index...")

        self.index = create_faiss_index(
            self.reviews,
            self.model
        )

        print(
            f"FAISS index created with "
            f"{self.index.ntotal:,} vectors."
        )

        print("\nSWIGGY RAG ENGINE READY")
        print("=" * 70)


    # ========================================================
    # SEARCH
    # ========================================================

    def search(self, question, top_k=TOP_K):

        question = clean_text(question)

        if not question:
            return pd.DataFrame()

        question_embedding = self.model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        question_embedding = question_embedding.astype(
            "float32"
        )

        scores, indices = self.index.search(
            question_embedding,
            top_k
        )

        results = []

        for score, index_position in zip(
            scores[0],
            indices[0]
        ):

            if index_position < 0:
                continue

            review = self.reviews.iloc[index_position].copy()

            review["similarity_score"] = float(score)

            results.append(review)

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)


    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    def answer(self, question, top_k=TOP_K):

        results = self.search(
            question,
            top_k
        )

        if results.empty:

            return {
                "answer": (
                    "I could not find relevant SWIGGY "
                    "customer reviews for this question."
                ),
                "results": results,
            }


        # ----------------------------------------------------
        # Ratings
        # ----------------------------------------------------

        ratings = pd.to_numeric(
            results["rating"],
            errors="coerce"
        )

        average_rating = ratings.mean()

        # ----------------------------------------------------
        # Simple sentiment indicators
        # ----------------------------------------------------

        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "perfect",
            "delicious",
            "friendly",
            "fast",
            "fresh",
            "love",
        ]

        negative_words = [
            "bad",
            "poor",
            "slow",
            "late",
            "cold",
            "rude",
            "worst",
            "terrible",
            "bland",
            "delay",
        ]

        positive_count = 0
        negative_count = 0

        for comment in results["comment"].astype(str):

            comment_lower = comment.lower()

            positive_count += sum(
                word in comment_lower
                for word in positive_words
            )

            negative_count += sum(
                word in comment_lower
                for word in negative_words
            )


        # ----------------------------------------------------
        # Overall interpretation
        # ----------------------------------------------------

        if negative_count > positive_count:

            interpretation = (
                "The retrieved reviews mainly indicate "
                "negative customer experiences."
            )

        elif positive_count > negative_count:

            interpretation = (
                "The retrieved reviews mainly indicate "
                "positive customer experiences."
            )

        else:

            interpretation = (
                "The retrieved reviews show mixed or "
                "neutral customer experiences."
            )


        # ----------------------------------------------------
        # Average rating text
        # ----------------------------------------------------

        if pd.isna(average_rating):

            rating_text = (
                "A reliable average rating was not "
                "available for the retrieved reviews."
            )

        else:

            rating_text = (
                f"The average rating among the retrieved "
                f"reviews is {average_rating:.2f}/5."
            )


        answer = (
            f"Based on {len(results)} relevant SWIGGY "
            f"customer reviews, {interpretation} "
            f"{rating_text}"
        )


        return {
            "answer": answer,
            "results": results,
        }


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    rag = SwiggyRAG()

    print("\n" + "=" * 70)
    print("SWIGGY RAG CHATBOT")
    print("=" * 70)

    print("\nAsk questions about SWIGGY customer reviews.")
    print("Type 'exit' to stop.")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() == "exit":

            print("\nSWIGGY RAG chatbot stopped.")

            break

        if not question:

            continue

        result = rag.answer(question)

        print("\n" + "-" * 70)

        print(result["answer"])

        print("\nRelevant review evidence:")

        for number, (_, row) in enumerate(
            result["results"].iterrows(),
            start=1
        ):

            print(
                f"{number}. "
                f"[Rating: {row['rating']}] "
                f"{row['comment']}"
            )

        print("-" * 70)
        