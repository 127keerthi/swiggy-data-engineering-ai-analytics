
# ============================================================
# SWIGGY AI DATA PLATFORM - COMPLETE STREAMLIT APPLICATION
# ============================================================
# Features
# 1. Dashboard
# 2. Business Analytics
# 3. Sentiment Analysis
# 4. RAG Review Search
# 5. Text-to-SQL
#
# Data sources:
#   SWIGGY.MARTS.DIM_USERS
#   SWIGGY.MARTS.DIM_RESTAURANTS
#   SWIGGY.MARTS.DIM_FOOD
#   SWIGGY.MARTS.DIM_MENU
#   SWIGGY.MARTS.FCT_ORDERS
#   SWIGGY.MARTS.FCT_ORDER_ITEMS
#   SWIGGY.MARTS.FCT_REVIEWS
#   SWIGGY.AI.REVIEW_SENTIMENT
# ============================================================

import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import snowflake.connector

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SWIGGY AI Data Platform",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS - MODERN CARD DASHBOARD
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f7f9fc;
    }

    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1500px;
        overflow: visible !important;
    }

    /* Prevent Streamlit markdown wrappers from clipping custom headings. */
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stMarkdownContainer"] > div,
    .stMarkdown {
        overflow: visible !important;
    }

    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background: #f1f4f9;
        border-right: 1px solid #e2e7ef;
    }

    .sidebar-brand {
        padding: 8px 8px 18px 8px;
    }

    .sidebar-brand-title {
        font-size: 28px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0;
    }

    .sidebar-brand-subtitle {
        font-size: 14px;
        color: #64748b;
    }

    .pipeline-card {
        background: #eaf2ff;
        border: 1px solid #d6e5ff;
        border-radius: 14px;
        padding: 18px;
        margin-top: 20px;
    }

    .pipeline-title {
        font-size: 18px;
        font-weight: 800;
        color: #0756a8;
        margin-bottom: 12px;
    }

    .pipeline-step {
        color: #334155;
        font-size: 14px;
        margin: 7px 0;
    }

    /* ---------- PAGE HEADER ---------- */

    .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 20px;
        margin: 0 0 26px 0;
        padding: 8px 0 6px 0;
        min-height: 78px;
        overflow: visible !important;
    }

    .page-title {
        display: block;
        position: relative;
        font-size: 42px;
        font-weight: 800;
        line-height: 1.25 !important;
        color: #111827;
        margin: 0 !important;
        padding: 4px 0 6px 0;
        min-height: 54px;
        height: auto !important;
        overflow: visible !important;
        white-space: normal;
    }

    .page-title::after {
        content: "";
        display: block;
        clear: both;
    }

    .page-subtitle {
        font-size: 17px;
        color: #64748b;
        margin-top: 7px;
    }

    .updated-card {
        background: white;
        border: 1px solid #dbe4ef;
        border-radius: 14px;
        padding: 13px 18px;
        min-width: 190px;
    }

    .updated-label {
        color: #64748b;
        font-size: 12px;
        margin-bottom: 4px;
    }

    .updated-value {
        color: #172033;
        font-weight: 700;
        font-size: 14px;
    }

    /* ---------- KPI CARDS ---------- */

    .kpi-card {
        background: white;
        border: 1px solid #e1e8f0;
        border-radius: 15px;
        padding: 18px 18px 16px 18px;
        min-height: 125px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
        margin-bottom: 12px;
    }

    .kpi-label {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        color: #111827;
        font-size: 27px;
        font-weight: 800;
        margin-top: 9px;
    }

    .kpi-note {
        color: #64748b;
        font-size: 12px;
        margin-top: 6px;
    }

    /* ---------- CHART CARDS ---------- */

    .chart-card {
        background: white;
        border: 1px solid #e1e8f0;
        border-radius: 15px;
        padding: 14px 18px 8px 18px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
    }

    .chart-title {
        color: #172033;
        font-size: 20px;
        font-weight: 800;
        margin: 2px 0 6px 0;
    }

    /* ---------- INFO CARDS ---------- */

    .info-card {
        background: white;
        border: 1px solid #e1e8f0;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .info-title {
        font-size: 21px;
        font-weight: 800;
        color: #172033;
        margin-bottom: 8px;
    }

    .info-text {
        color: #64748b;
        line-height: 1.6;
    }

    /* ---------- PIPELINE ---------- */

    .pipeline-horizontal {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        background: white;
        border: 1px solid #e1e8f0;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .pipeline-node {
        background: #eef5ff;
        border: 1px solid #cfe0ff;
        color: #1559a6;
        border-radius: 10px;
        padding: 9px 13px;
        font-weight: 700;
        font-size: 13px;
    }

    .pipeline-arrow {
        color: #94a3b8;
        font-weight: 800;
    }

    /* ---------- SEARCH / SQL ---------- */

    .answer-card {
        background: white;
        border: 1px solid #dbe4ef;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        background: white;
        border: 1px solid #e1e8f0;
        border-radius: 12px;
        padding: 13px 18px;
        margin-top: 24px;
        color: #64748b;
        font-size: 13px;
        text-align: center;
    }

    /* Keep titles fully visible on smaller screens. */
    @media (max-width: 900px) {
        .page-title {
            font-size: 34px;
            line-height: 1.25 !important;
            min-height: 46px;
        }
        .page-header {
            min-height: 64px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SNOWFLAKE CONFIG
# ============================================================

SNOWFLAKE_ACCOUNT = os.getenv(
    "SNOWFLAKE_ACCOUNT",
    "TBMPXKR-PE66235",
)

SNOWFLAKE_DATABASE = "SWIGGY"
SNOWFLAKE_SCHEMA = "MARTS"
SNOWFLAKE_WAREHOUSE = "SWIGGY_WH"
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")


# ============================================================
# SNOWFLAKE CREDENTIALS
# ============================================================

# The app first checks environment variables. If the username/password
# are not present, the sidebar provides secure input fields.
ENV_SNOWFLAKE_USER = (
    os.getenv("SNOWFLAKE_USER")
    or os.getenv("SNOWFLAKE_USERNAME")
)

ENV_SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

@st.cache_resource
def get_snowflake_connection(username, password):
    if not username:
        raise RuntimeError("Enter your Snowflake username.")

    if not password:
        raise RuntimeError("Enter your Snowflake password.")

    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=username,
        password=password,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE,
    )


def get_credentials():
    username = st.session_state.get(
        "snowflake_username",
        ENV_SNOWFLAKE_USER or "",
    )
    password = st.session_state.get(
        "snowflake_password",
        ENV_SNOWFLAKE_PASSWORD or "",
    )
    return username, password


def run_query(query):
    username, password = get_credentials()

    if not username or not password:
        raise RuntimeError(
            "Snowflake credentials are missing. Enter them in the sidebar."
        )

    conn = get_snowflake_connection(username, password)
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        if cursor.description is None:
            return pd.DataFrame()

        rows = cursor.fetchall()

        columns = [
            description[0].lower()
            for description in cursor.description
        ]

        return pd.DataFrame(rows, columns=columns)

    finally:
        cursor.close()


# ============================================================
# SQL HELPER
# ============================================================


def scalar(query, default=0):
    df = run_query(query)

    if df.empty:
        return default

    value = df.iloc[0, 0]

    if pd.isna(value):
        return default

    return value


# ============================================================
# FORMATTING
# ============================================================

def fmt_int(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "0"


def fmt_money(value):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return "₹0.00"


def fmt_float(value, decimals=2):
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return "0.00"


def show_bar_chart(df, category_col, value_col, horizontal=False):
    if df.empty:
        st.info("No data available.")
        return

    if PLOTLY_AVAILABLE:
        if horizontal:
            fig = px.bar(
                df,
                x=value_col,
                y=category_col,
                orientation="h",
                text=value_col,
            )
        else:
            fig = px.bar(
                df,
                x=category_col,
                y=value_col,
                text=value_col,
            )

        fig.update_layout(
            height=330,
            margin=dict(l=15, r=15, t=20, b=50),
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title="",
            yaxis_title="",
        )

        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

    else:
        st.bar_chart(
            df.set_index(category_col)[value_col]
        )


def chart_card(title, df, category_col, value_col, horizontal=False):
    st.markdown(
        f"""
        <div class="chart-card">
            <div class="chart-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    show_bar_chart(
        df,
        category_col,
        value_col,
        horizontal=horizontal,
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🍔 SWIGGY</div>
            <div class="sidebar-brand-subtitle">
                AI Data Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📊 Business Analytics",
            "😊 Sentiment Analysis",
            "🔎 RAG Review Search",
            "💬 Text-to-SQL",
        ],
    )

    st.markdown(
        """
        <div class="pipeline-card">
            <div class="pipeline-title">End-to-End Pipeline</div>
            <div class="pipeline-step">📄 Local CSV → Snowflake RAW</div>
            <div class="pipeline-step">🧱 dbt STAGING → dbt MARTS</div>
            <div class="pipeline-step">⚙️ Airflow orchestration</div>
            <div class="pipeline-step">🧠 Python AI + Sentiment</div>
            <div class="pipeline-step">🔎 RAG Review Search</div>
            <div class="pipeline-step">💬 Text-to-SQL</div>
            <div class="pipeline-step">📊 Streamlit Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### 🔐 Snowflake Login")

    st.text_input(
        "Snowflake Username",
        value=ENV_SNOWFLAKE_USER or "",
        key="snowflake_username",
        help="Use the same Snowflake username used by your dbt profile.",
    )

    st.text_input(
        "Snowflake Password",
        value=ENV_SNOWFLAKE_PASSWORD or "",
        type="password",
        key="snowflake_password",
        help="Your password is used only for this Streamlit session.",
    )

    if st.button(
        "🔌 Connect to Snowflake",
        use_container_width=True,
    ):
        get_snowflake_connection.clear()
        st.rerun()

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):
        get_snowflake_connection.clear()
        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-title">
                    🍔 SWIGGY AI Data Platform
                </div>
                <div class="page-subtitle">
                    End-to-End Data Engineering • AI • RAG • Text-to-SQL
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        connection_info = run_query(
            """
            SELECT
                CURRENT_USER() AS USER_NAME,
                CURRENT_ROLE() AS ROLE_NAME,
                CURRENT_DATABASE() AS DATABASE_NAME,
                CURRENT_SCHEMA() AS SCHEMA_NAME,
                CURRENT_WAREHOUSE() AS WAREHOUSE_NAME
            """
        )

        st.success(
            "🟢 Connected to Snowflake successfully"
        )

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">
                    🚀 SWIGGY End-to-End Architecture
                </div>
                <div class="info-text">
                    Local CSV files are loaded into Snowflake RAW,
                    transformed through dbt STAGING and MARTS,
                    orchestrated with Airflow, enriched with Python
                    sentiment analysis, and exposed through RAG,
                    Text-to-SQL and Streamlit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="pipeline-horizontal">
                <span class="pipeline-node">Local CSV</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">Snowflake RAW</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">dbt STAGING</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">dbt MARTS</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">Airflow</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">AI</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">RAG</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">Text-to-SQL</span>
                <span class="pipeline-arrow">→</span>
                <span class="pipeline-node">Streamlit</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Snowflake Connection")

        st.dataframe(
            connection_info,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            """
            <div class="footer">
                SWIGGY AI Data Platform |
                Snowflake • dbt • Airflow • Python • RAG • Text-to-SQL • Streamlit
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Snowflake connection failed: {e}")


# ============================================================
# BUSINESS ANALYTICS
# ============================================================

elif page == "📊 Business Analytics":

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-title">📊 SWIGGY Business Analytics</div>
                <div class="page-subtitle">
                    Explore key metrics and insights from your food delivery data
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        users = scalar(
            """
            SELECT COUNT(*)
            FROM SWIGGY.MARTS.DIM_USERS
            """
        )

        restaurants = scalar(
            """
            SELECT COUNT(*)
            FROM SWIGGY.MARTS.DIM_RESTAURANTS
            """
        )

        orders = scalar(
            """
            SELECT COUNT(*)
            FROM SWIGGY.MARTS.FCT_ORDERS
            """
        )

        reviews = scalar(
            """
            SELECT COUNT(*)
            FROM SWIGGY.MARTS.FCT_REVIEWS
            """
        )

        total_sales = scalar(
            """
            SELECT COALESCE(SUM(SALES_AMOUNT), 0)
            FROM SWIGGY.MARTS.FCT_ORDERS
            """
        )

        avg_delivery = scalar(
            """
            SELECT AVG(DELIVERY_TIME_MIN)
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE DELIVERY_TIME_MIN IS NOT NULL
            """
        )

        avg_rating = scalar(
            """
            SELECT AVG(RATING)
            FROM SWIGGY.MARTS.FCT_REVIEWS
            WHERE RATING IS NOT NULL
            """
        )

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        kpis = [
            ("👥 Users", fmt_int(users), "Registered users"),
            ("🍽️ Restaurants", fmt_int(restaurants), "Restaurant records"),
            ("📦 Orders", fmt_int(orders), "Order transactions"),
            ("⭐ Reviews", fmt_int(reviews), "Customer reviews"),
            ("💰 Total Sales", fmt_money(total_sales), "Sales amount"),
            (
                "🚴 Avg Delivery Time",
                f"{fmt_float(avg_delivery)} min",
                "Average delivery time",
            ),
            (
                "⭐ Avg Review Rating",
                f"{fmt_float(avg_rating)} / 5",
                "Average customer rating",
            ),
        ]

        cols = st.columns(4)

        for i, (label, value, note) in enumerate(kpis[:4]):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-note">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        cols = st.columns(3)

        for i, (label, value, note) in enumerate(kpis[4:]):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-note">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ----------------------------------------------------
        # SALES BY CITY
        # ----------------------------------------------------

        sales_city = run_query(
            """
            SELECT
                RESTAURANT_CITY AS CITY,
                ROUND(SUM(SALES_AMOUNT), 2) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE RESTAURANT_CITY IS NOT NULL
              AND SALES_AMOUNT IS NOT NULL
            GROUP BY RESTAURANT_CITY
            ORDER BY TOTAL_SALES DESC
            LIMIT 10
            """
        )

        # ----------------------------------------------------
        # ORDER STATUS
        # ----------------------------------------------------

        status = run_query(
            """
            SELECT
                ORDER_STATUS,
                COUNT(*) AS ORDER_COUNT
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE ORDER_STATUS IS NOT NULL
            GROUP BY ORDER_STATUS
            ORDER BY ORDER_COUNT DESC
            """
        )

        # ----------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------

        payment = run_query(
            """
            SELECT
                PAYMENT_METHOD,
                COUNT(*) AS ORDER_COUNT
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE PAYMENT_METHOD IS NOT NULL
            GROUP BY PAYMENT_METHOD
            ORDER BY ORDER_COUNT DESC
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            chart_card(
                "💰 Sales by City",
                sales_city,
                "city",
                "total_sales",
            )

        with col2:
            chart_card(
                "📦 Orders by Status",
                status,
                "order_status",
                "order_count",
            )

        # ----------------------------------------------------
        # PAYMENT + CUISINE
        # ----------------------------------------------------

        cuisine = run_query(
            """
            SELECT
                CUISINE,
                COUNT(*) AS ORDER_COUNT
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE CUISINE IS NOT NULL
            GROUP BY CUISINE
            ORDER BY ORDER_COUNT DESC
            LIMIT 10
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            chart_card(
                "💳 Payment Methods",
                payment,
                "payment_method",
                "order_count",
            )

        with col2:
            chart_card(
                "🍛 Popular Cuisines",
                cuisine,
                "cuisine",
                "order_count",
            )

        # ----------------------------------------------------
        # TOP RESTAURANTS
        # ----------------------------------------------------

        top_restaurants = run_query(
            """
            SELECT
                COALESCE(
                    r.RESTAURANT_NAME,
                    'Unknown Restaurant'
                ) AS RESTAURANT_NAME,
                ROUND(
                    SUM(o.SALES_AMOUNT),
                    2
                ) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS o
            LEFT JOIN SWIGGY.MARTS.DIM_RESTAURANTS r
                ON o.RESTAURANT_ID = r.RESTAURANT_ID
            WHERE o.SALES_AMOUNT IS NOT NULL
            GROUP BY r.RESTAURANT_NAME
            ORDER BY TOTAL_SALES DESC
            LIMIT 10
            """
        )

        chart_card(
            "🏆 Top Restaurants by Sales",
            top_restaurants,
            "restaurant_name",
            "total_sales",
            horizontal=True,
        )

        # ----------------------------------------------------
        # DATA TABLES
        # ----------------------------------------------------

        with st.expander("View Business Analytics Data"):

            st.markdown("**Sales by City**")
            st.dataframe(
                sales_city,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Orders by Status**")
            st.dataframe(
                status,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Payment Methods**")
            st.dataframe(
                payment,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Popular Cuisines**")
            st.dataframe(
                cuisine,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("**Top Restaurants**")
            st.dataframe(
                top_restaurants,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:
        st.error(f"Business Analytics failed: {e}")


# ============================================================
# SENTIMENT ANALYSIS
# ============================================================

elif page == "😊 Sentiment Analysis":

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-title">😊 SWIGGY Sentiment Analysis</div>
                <div class="page-subtitle">
                    Customer review sentiment generated by Python + TextBlob
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        total = scalar(
            """
            SELECT COUNT(*)
            FROM SWIGGY.AI.REVIEW_SENTIMENT
            """
        )

        if int(total) == 0:

            st.warning(
                """
                `SWIGGY.AI.REVIEW_SENTIMENT` exists but contains no rows.
                Run the sentiment pipeline first.
                """
            )

        else:

            sentiment_counts = run_query(
                """
                SELECT
                    SENTIMENT,
                    COUNT(*) AS REVIEW_COUNT
                FROM SWIGGY.AI.REVIEW_SENTIMENT
                GROUP BY SENTIMENT
                ORDER BY REVIEW_COUNT DESC
                """
            )

            counts = {
                str(row["sentiment"]).upper(): int(row["review_count"])
                for _, row in sentiment_counts.iterrows()
            }

            positive = counts.get("POSITIVE", 0)
            neutral = counts.get("NEUTRAL", 0)
            negative = counts.get("NEGATIVE", 0)

            cols = st.columns(4)

            sentiment_kpis = [
                ("📝 Total Reviews", int(total)),
                ("😊 Positive", positive),
                ("😐 Neutral", neutral),
                ("😞 Negative", negative),
            ]

            for i, (label, value) in enumerate(sentiment_kpis):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div class="kpi-card">
                            <div class="kpi-label">{label}</div>
                            <div class="kpi-value">{value:,}</div>
                            <div class="kpi-note">AI sentiment result</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            col1, col2 = st.columns(2)

            with col1:
                chart_card(
                    "📊 Sentiment Distribution",
                    sentiment_counts,
                    "sentiment",
                    "review_count",
                )

            with col2:

                percentage = sentiment_counts.copy()

                percentage["percentage"] = (
                    percentage["review_count"]
                    / int(total)
                    * 100
                ).round(2)

                st.markdown(
                    """
                    <div class="chart-card">
                        <div class="chart-title">
                            📈 Sentiment Percentage
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.dataframe(
                    percentage[
                        [
                            "sentiment",
                            "review_count",
                            "percentage",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            # ------------------------------------------------
            # SENTIMENT BY RATING
            # ------------------------------------------------

            sentiment_rating = run_query(
                """
                SELECT
                    RATING,
                    SENTIMENT,
                    COUNT(*) AS REVIEW_COUNT
                FROM SWIGGY.AI.REVIEW_SENTIMENT
                WHERE RATING IS NOT NULL
                GROUP BY RATING, SENTIMENT
                ORDER BY RATING
                """
            )

            st.markdown(
                """
                <div class="chart-card">
                    <div class="chart-title">
                        ⭐ Sentiment by Customer Rating
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not sentiment_rating.empty:

                pivot = sentiment_rating.pivot(
                    index="rating",
                    columns="sentiment",
                    values="review_count",
                ).fillna(0)

                if PLOTLY_AVAILABLE:

                    fig = px.bar(
                        sentiment_rating,
                        x="rating",
                        y="review_count",
                        color="sentiment",
                        barmode="group",
                    )

                    fig.update_layout(
                        height=350,
                        margin=dict(
                            l=15,
                            r=15,
                            t=20,
                            b=50,
                        ),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        xaxis_title="Rating",
                        yaxis_title="Review Count",
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )

                else:
                    st.bar_chart(pivot)

            # ------------------------------------------------
            # SCORE
            # ------------------------------------------------

            score_summary = run_query(
                """
                SELECT
                    AVG(SENTIMENT_SCORE) AS AVG_SCORE,
                    MIN(SENTIMENT_SCORE) AS MIN_SCORE,
                    MAX(SENTIMENT_SCORE) AS MAX_SCORE
                FROM SWIGGY.AI.REVIEW_SENTIMENT
                """
            )

            if not score_summary.empty:

                row = score_summary.iloc[0]

                cols = st.columns(3)

                values = [
                    ("Average Score", row["avg_score"]),
                    ("Minimum Score", row["min_score"]),
                    ("Maximum Score", row["max_score"]),
                ]

                for i, (label, value) in enumerate(values):

                    with cols[i]:

                        st.markdown(
                            f"""
                            <div class="kpi-card">
                                <div class="kpi-label">{label}</div>
                                <div class="kpi-value">
                                    {fmt_float(value, 4)}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # ------------------------------------------------
            # REVIEW EXPLORER
            # ------------------------------------------------

            st.markdown(
                """
                <div class="info-card">
                    <div class="info-title">
                        🔎 Review Sentiment Explorer
                    </div>
                    <div class="info-text">
                        Filter the AI-generated review classifications
                        stored in Snowflake.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)

            with c1:
                selected_sentiment = st.selectbox(
                    "Sentiment",
                    [
                        "ALL",
                        "POSITIVE",
                        "NEUTRAL",
                        "NEGATIVE",
                    ],
                )

            with c2:
                limit = st.slider(
                    "Reviews to display",
                    10,
                    100,
                    20,
                    10,
                )

            condition = ""

            if selected_sentiment != "ALL":
                condition = (
                    "AND SENTIMENT = "
                    f"'{selected_sentiment}'"
                )

            review_data = run_query(
                f"""
                SELECT
                    REVIEW_ID,
                    ORDER_ID,
                    RESTAURANT_ID,
                    RATING,
                    COMMENT,
                    REVIEW_DATE,
                    SENTIMENT,
                    SENTIMENT_SCORE
                FROM SWIGGY.AI.REVIEW_SENTIMENT
                WHERE COMMENT IS NOT NULL
                {condition}
                ORDER BY REVIEW_DATE DESC NULLS LAST
                LIMIT {int(limit)}
                """
            )

            st.dataframe(
                review_data,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:
        st.error(
            "Sentiment Analysis failed. "
            f"Check that SWIGGY.AI.REVIEW_SENTIMENT exists. Error: {e}"
        )


# ============================================================
# RAG REVIEW SEARCH
# ============================================================

elif page == "🔎 RAG Review Search":

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-title">🔎 SWIGGY RAG Review Search</div>
                <div class="page-subtitle">
                    Retrieve relevant customer reviews using keyword-based
                    retrieval from Snowflake.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">How this RAG layer works</div>
            <div class="info-text">
                The application takes your question, extracts useful search
                terms, retrieves matching SWIGGY reviews from Snowflake,
                and displays the most relevant review records.
                This implementation works without requiring a paid LLM API.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Ask about SWIGGY customer reviews",
        placeholder=(
            "Example: customers complaining about delivery time"
        ),
    )

    limit = st.slider(
        "Number of reviews",
        3,
        20,
        5,
    )

    examples = [
        "delivery taking too long",
        "food quality",
        "late delivery",
        "good taste",
        "bad service",
        "packaging",
    ]

    st.caption("Try one of these:")
    example_cols = st.columns(3)

    for i, example in enumerate(examples):

        with example_cols[i % 3]:

            if st.button(
                example,
                key=f"rag_example_{i}",
                use_container_width=True,
            ):
                question = example

    if st.button(
        "🔎 Search Reviews",
        type="primary",
        use_container_width=False,
    ):

        if not question.strip():

            st.warning(
                "Enter a review question first."
            )

        else:

            # ------------------------------------------------
            # SAFE KEYWORD EXTRACTION
            # ------------------------------------------------

            stopwords = {
                "what",
                "are",
                "the",
                "about",
                "customers",
                "customer",
                "saying",
                "say",
                "reviews",
                "review",
                "show",
                "me",
                "find",
                "for",
                "with",
                "from",
                "does",
                "do",
                "how",
                "why",
                "is",
                "and",
                "or",
                "to",
                "of",
                "in",
                "on",
                "a",
                "an",
                "their",
            }

            words = re.findall(
                r"[A-Za-z0-9]+",
                question.lower(),
            )

            keywords = [
                word
                for word in words
                if len(word) >= 3
                and word not in stopwords
            ]

            # Keep query manageable
            keywords = keywords[:8]

            if not keywords:

                st.warning(
                    "Please enter more specific review keywords."
                )

            else:

                conditions = []

                for word in keywords:

                    escaped = word.replace("'", "''")

                    conditions.append(
                        "UPPER(COMMENT) LIKE "
                        f"'%{escaped.upper()}%'"
                    )

                where_clause = " OR ".join(
                    conditions
                )

                try:

                    rag_results = run_query(
                        f"""
                        SELECT
                            REVIEW_ID,
                            ORDER_ID,
                            RESTAURANT_ID,
                            RATING,
                            COMMENT,
                            REVIEW_DATE,
                            SENTIMENT
                        FROM SWIGGY.AI.REVIEW_SENTIMENT
                        WHERE COMMENT IS NOT NULL
                          AND ({where_clause})
                        ORDER BY
                            REVIEW_DATE DESC NULLS LAST
                        LIMIT {int(limit)}
                        """
                    )

                    st.markdown(
                        f"""
                        <div class="answer-card">
                            <b>Retrieved keywords:</b>
                            {", ".join(keywords)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if rag_results.empty:

                        st.info(
                            "No matching reviews were found."
                        )

                    else:

                        st.success(
                            f"Found {len(rag_results)} relevant reviews."
                        )

                        st.dataframe(
                            rag_results,
                            use_container_width=True,
                            hide_index=True,
                        )

                        # ------------------------------------------------
                        # SIMPLE RETRIEVAL SUMMARY
                        # ------------------------------------------------

                        avg_rating = (
                            rag_results["rating"]
                            .dropna()
                            .mean()
                        )

                        sentiment_summary = (
                            rag_results["sentiment"]
                            .value_counts()
                            .to_dict()
                        )

                        c1, c2 = st.columns(2)

                        with c1:
                            st.metric(
                                "Average Retrieved Rating",
                                (
                                    f"{avg_rating:.2f}/5"
                                    if pd.notna(avg_rating)
                                    else "N/A"
                                ),
                            )

                        with c2:
                            st.write(
                                "Retrieved Sentiments:",
                                sentiment_summary,
                            )

                except Exception as e:
                    st.error(
                        f"RAG search failed: {e}"
                    )


# ============================================================
# TEXT-TO-SQL
# ============================================================

elif page == "💬 Text-to-SQL":

    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-title">💬 SWIGGY Text-to-SQL</div>
                <div class="page-subtitle">
                    Ask business questions in natural language and execute
                    safe SQL against the SWIGGY MARTS layer.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-card">
            <div class="info-title">
                🤖 Natural Language → SQL → Snowflake
            </div>
            <div class="info-text">
                Select a supported business question or type a matching
                question. The application maps it to a validated SQL query
                and executes that query against Snowflake.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    question_options = [
        "How many orders are there?",
        "How many users are there?",
        "How many restaurants are there?",
        "How many reviews are there?",
        "What is the total sales?",
        "What is the average rating?",
        "What is the average delivery time?",
        "Show top cities by sales",
        "Show payment methods",
        "Show order status",
        "Show popular cuisine",
        "Show top restaurants by sales",
    ]

    selected_question = st.selectbox(
        "Choose a business question",
        question_options,
    )

    custom_question = st.text_input(
        "Or type your own supported question",
        placeholder="Example: What is the total sales?",
    )

    question = (
        custom_question.strip()
        if custom_question.strip()
        else selected_question
    )

    # --------------------------------------------------------
    # SAFE SQL MAPPINGS
    # --------------------------------------------------------

    sql_map = {

        "how many orders": """
            SELECT COUNT(*) AS TOTAL_ORDERS
            FROM SWIGGY.MARTS.FCT_ORDERS
        """,

        "how many users": """
            SELECT COUNT(*) AS TOTAL_USERS
            FROM SWIGGY.MARTS.DIM_USERS
        """,

        "how many restaurants": """
            SELECT COUNT(*) AS TOTAL_RESTAURANTS
            FROM SWIGGY.MARTS.DIM_RESTAURANTS
        """,

        "how many reviews": """
            SELECT COUNT(*) AS TOTAL_REVIEWS
            FROM SWIGGY.MARTS.FCT_REVIEWS
        """,

        "what is the total sales": """
            SELECT
                ROUND(SUM(SALES_AMOUNT), 2) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS
        """,

        "what is the average rating": """
            SELECT
                ROUND(AVG(RATING), 2) AS AVERAGE_RATING
            FROM SWIGGY.MARTS.FCT_REVIEWS
            WHERE RATING IS NOT NULL
        """,

        "what is the average delivery time": """
            SELECT
                ROUND(AVG(DELIVERY_TIME_MIN), 2)
                    AS AVERAGE_DELIVERY_TIME
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE DELIVERY_TIME_MIN IS NOT NULL
        """,

        "show top cities by sales": """
            SELECT
                RESTAURANT_CITY AS CITY,
                ROUND(SUM(SALES_AMOUNT), 2) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE RESTAURANT_CITY IS NOT NULL
            GROUP BY RESTAURANT_CITY
            ORDER BY TOTAL_SALES DESC
            LIMIT 10
        """,

        "show payment methods": """
            SELECT
                PAYMENT_METHOD,
                COUNT(*) AS ORDER_COUNT,
                ROUND(SUM(SALES_AMOUNT), 2) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE PAYMENT_METHOD IS NOT NULL
            GROUP BY PAYMENT_METHOD
            ORDER BY ORDER_COUNT DESC
        """,

        "show order status": """
            SELECT
                ORDER_STATUS,
                COUNT(*) AS ORDER_COUNT
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE ORDER_STATUS IS NOT NULL
            GROUP BY ORDER_STATUS
            ORDER BY ORDER_COUNT DESC
        """,

        "show popular cuisine": """
            SELECT
                CUISINE,
                COUNT(*) AS ORDER_COUNT,
                ROUND(SUM(SALES_AMOUNT), 2) AS TOTAL_SALES
            FROM SWIGGY.MARTS.FCT_ORDERS
            WHERE CUISINE IS NOT NULL
            GROUP BY CUISINE
            ORDER BY ORDER_COUNT DESC
            LIMIT 10
        """,

        "show top restaurants by sales": """
            SELECT
                COALESCE(
                    r.RESTAURANT_NAME,
                    'Unknown Restaurant'
                ) AS RESTAURANT_NAME,
                ROUND(
                    SUM(o.SALES_AMOUNT),
                    2
                ) AS TOTAL_SALES,
                COUNT(*) AS ORDER_COUNT
            FROM SWIGGY.MARTS.FCT_ORDERS o
            LEFT JOIN SWIGGY.MARTS.DIM_RESTAURANTS r
                ON o.RESTAURANT_ID = r.RESTAURANT_ID
            WHERE o.SALES_AMOUNT IS NOT NULL
            GROUP BY r.RESTAURANT_NAME
            ORDER BY TOTAL_SALES DESC
            LIMIT 10
        """,
    }

    def resolve_sql(user_question):

        normalized = re.sub(
            r"[^a-z0-9\s]",
            "",
            user_question.lower(),
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        for phrase, sql in sql_map.items():

            if phrase in normalized:
                return sql

        return None

    if st.button(
        "▶ Run Query",
        type="primary",
    ):

        sql = resolve_sql(question)

        if sql is None:

            st.warning(
                """
                This question is not in the current safe query
                library. Try one of the example questions above.
                """
            )

        else:

            st.markdown(
                """
                <div class="answer-card">
                    <b>Generated SQL</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.code(
                sql.strip(),
                language="sql",
            )

            try:

                result = run_query(sql)

                st.markdown(
                    """
                    <div class="answer-card">
                        <b>Snowflake Result</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True,
                )

                if (
                    len(result) == 1
                    and len(result.columns) == 1
                ):

                    value = result.iloc[0, 0]

                    st.success(
                        f"Answer: {value}"
                    )

            except Exception as e:
                st.error(
                    f"Text-to-SQL query failed: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        SWIGGY AI Data Platform |
        Snowflake • dbt • Airflow • Python • AI • RAG • Text-to-SQL • Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
