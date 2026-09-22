import os
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import snowflake.connector
from dotenv import load_dotenv


# ============================================================
# SWIGGY FOOD DELIVERY ANALYTICS DASHBOARD
# Snowflake + dbt + Airflow + Streamlit
# ============================================================

st.set_page_config(
    page_title="SWIGGY Food Delivery Analytics",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 1. LOAD EXISTING PROJECT ENVIRONMENT
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
AIRFLOW_ENV = PROJECT_DIR / "airflow" / ".env"

# Load the existing Airflow .env file
if AIRFLOW_ENV.exists():
    load_dotenv(AIRFLOW_ENV, override=True)

# Also load a project-level .env if one exists
PROJECT_ENV = PROJECT_DIR / ".env"

if PROJECT_ENV.exists():
    load_dotenv(PROJECT_ENV, override=False)


# ============================================================
# 2. GET SNOWFLAKE CREDENTIALS
# ============================================================

SNOWFLAKE_ACCOUNT = (
    os.getenv("SNOWFLAKE_ACCOUNT")
    or os.getenv("SNOWFLAKE_ACCOUNT_IDENTIFIER")
    or "TBMPXKR-PE66235"
)

SNOWFLAKE_USER = (
    os.getenv("SNOWFLAKE_USER")
    or os.getenv("SNOWFLAKE_USERNAME")
    or os.getenv("AIRFLOW__SNOWFLAKE__USER")
)

SNOWFLAKE_PASSWORD = (
    os.getenv("SNOWFLAKE_PASSWORD")
    or os.getenv("SNOWFLAKE_PASS")
    or os.getenv("AIRFLOW__SNOWFLAKE__PASSWORD")
)

SNOWFLAKE_WAREHOUSE = (
    os.getenv("SNOWFLAKE_WAREHOUSE")
    or "SWIGGY_WH"
)

SNOWFLAKE_DATABASE = "SWIGGY"
SNOWFLAKE_SCHEMA = "MARTS"

SNOWFLAKE_ROLE = (
    os.getenv("SNOWFLAKE_ROLE")
    or "DBT_ROLE"
)


# ============================================================
# 3. SNOWFLAKE CONNECTION
# ============================================================

def get_connection():

    if not SNOWFLAKE_USER:
        st.error(
            "Snowflake username was not found.\n\n"
            "The dashboard checked:\n"
            f"{AIRFLOW_ENV}"
        )
        st.stop()

    if not SNOWFLAKE_PASSWORD:
        st.error(
            "Snowflake password was not found in the existing .env file.\n\n"
            "No password was entered or changed by this dashboard."
        )
        st.stop()

    try:

        connection = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            role=SNOWFLAKE_ROLE,
        )

        return connection

    except Exception as e:

        st.error("Unable to connect to Snowflake.")
        st.code(str(e))

        st.stop()


# ============================================================
# 4. QUERY FUNCTION
# ============================================================

@st.cache_data(ttl=300)
def run_query(sql):

    connection = get_connection()

    try:

        dataframe = pd.read_sql(sql, connection)

        return dataframe

    finally:

        connection.close()


# ============================================================
# 5. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-size: 34px;
        font-weight: 750;
        color: #111827;
        margin-bottom: 0px;
    }

    .dashboard-subtitle {
        font-size: 15px;
        color: #6b7280;
        margin-bottom: 20px;
    }

    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.06);
        min-height: 105px;
    }

    .kpi-label {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 7px;
    }

    .kpi-value {
        color: #111827;
        font-size: 25px;
        font-weight: 750;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin-top: 15px;
        margin-bottom: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6. LOAD SWIGGY ANALYTICS VIEWS
# ============================================================

try:

    KPI = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_SWIGGY_KPI
        """
    )

    CITY = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_CITY_PERFORMANCE
        """
    )

    RESTAURANT = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_RESTAURANT_PERFORMANCE
        """
    )

    FOOD = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_FOOD_PERFORMANCE
        """
    )

    PAYMENT = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_PAYMENT_PERFORMANCE
        """
    )

    MONTHLY = run_query(
        """
        SELECT *
        FROM SWIGGY.MARTS.VW_MONTHLY_PERFORMANCE
        """
    )

except Exception as e:

    st.error("Unable to load SWIGGY analytics views.")

    st.code(str(e))

    st.stop()


# ============================================================
# 7. CHECK DATA
# ============================================================

if KPI.empty:

    st.error("VW_SWIGGY_KPI returned no data.")
    st.stop()


K = KPI.iloc[0]


# ============================================================
# 8. HELPER FUNCTIONS
# ============================================================

def format_number(value):

    try:
        return f"{float(value):,.0f}"

    except:

        return "0"


def format_currency(value):

    try:
        return f"₹{float(value):,.0f}"

    except:

        return "₹0"


def format_decimal(value, decimals=2):

    try:
        return f"{float(value):,.{decimals}f}"

    except:

        return "0"


def create_kpi(label, value):

    st.markdown(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                {label}
            </div>

            <div class="kpi-value">
                {value}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 9. SIDEBAR
# ============================================================

st.sidebar.title("🍔 SWIGGY")

st.sidebar.caption(
    "Food Delivery Analytics Platform"
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Executive Overview",
        "Operations & Delivery",
        "Restaurant & Food",
    ],
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    **Data Engineering Pipeline**

    Local CSV  
    ↓  
    Snowflake RAW  
    ↓  
    dbt STAGING  
    ↓  
    dbt MARTS  
    ↓  
    Airflow  
    ↓  
    Analytics Views  
    ↓  
    Dashboard
    """
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "SWIGGY End-to-End Data Engineering Project"
)


# ============================================================
# PAGE 1
# EXECUTIVE OVERVIEW
# ============================================================

if page == "Executive Overview":

    st.markdown(
        '<div class="dashboard-title">'
        'SWIGGY Food Delivery Analytics'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Executive Performance Overview'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        create_kpi(
            "Total Orders",
            format_number(K["TOTAL_ORDERS"])
        )

    with col2:

        create_kpi(
            "Total Revenue",
            format_currency(K["TOTAL_REVENUE"])
        )

    with col3:

        create_kpi(
            "Average Order Value",
            format_currency(K["AVERAGE_ORDER_VALUE"])
        )

    with col4:

        create_kpi(
            "Average Customer Rating",
            format_decimal(
                K["AVERAGE_CUSTOMER_RATING"],
                2
            )
        )

    with col5:

        create_kpi(
            "Average Delivery Time",
            f'{format_decimal(K["AVERAGE_DELIVERY_TIME"], 1)} min'
        )


    st.markdown(
        '<div class="section-title">'
        'Revenue Trend'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # MONTHLY REVENUE
    # --------------------------------------------------------

    monthly = MONTHLY.copy()

    if "ORDER_MONTH" in monthly.columns:

        monthly["ORDER_MONTH"] = pd.to_datetime(
            monthly["ORDER_MONTH"]
        )

        monthly = monthly.sort_values(
            "ORDER_MONTH"
        )

    fig = px.line(
        monthly,
        x="ORDER_MONTH",
        y="TOTAL_REVENUE",
        markers=True,
        title="Monthly Revenue Trend",
    )

    fig.update_layout(
        height=390,
        xaxis_title="",
        yaxis_title="Revenue (₹)",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # CITY + PAYMENT
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        city_data = CITY.nlargest(
            15,
            "TOTAL_REVENUE"
        )

        fig = px.bar(
            city_data,
            x="TOTAL_REVENUE",
            y="CITY",
            orientation="h",
            title="Revenue by City",
        )

        fig.update_layout(
            height=450,
            yaxis={
                "categoryorder": "total ascending"
            },
            xaxis_title="Revenue (₹)",
            yaxis_title="",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        fig = px.pie(
            PAYMENT,
            names="PAYMENT_METHOD",
            values="TOTAL_ORDERS",
            hole=0.50,
            title="Orders by Payment Method",
        )

        fig.update_layout(
            height=450,
            paper_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # TOP RESTAURANTS + FOOD
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        restaurant_data = RESTAURANT.nlargest(
            10,
            "TOTAL_REVENUE"
        )

        fig = px.bar(
            restaurant_data,
            x="TOTAL_REVENUE",
            y="RESTAURANT_NAME",
            orientation="h",
            title="Top 10 Restaurants by Revenue",
        )

        fig.update_layout(
            height=450,
            yaxis={
                "categoryorder": "total ascending"
            },
            xaxis_title="Revenue (₹)",
            yaxis_title="",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        food_data = FOOD.nlargest(
            10,
            "TOTAL_REVENUE"
        )

        fig = px.bar(
            food_data,
            x="TOTAL_REVENUE",
            y="FOOD_ITEM",
            orientation="h",
            title="Top 10 Food Items by Revenue",
        )

        fig.update_layout(
            height=450,
            yaxis={
                "categoryorder": "total ascending"
            },
            xaxis_title="Revenue (₹)",
            yaxis_title="",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# PAGE 2
# OPERATIONS & DELIVERY
# ============================================================

elif page == "Operations & Delivery":

    st.markdown(
        '<div class="dashboard-title">'
        'Operations & Delivery'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Operational performance, city activity and delivery insights'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        create_kpi(
            "Total Orders",
            format_number(K["TOTAL_ORDERS"])
        )

    with col2:

        create_kpi(
            "Total Revenue",
            format_currency(K["TOTAL_REVENUE"])
        )

    with col3:

        create_kpi(
            "Average Delivery",
            f'{format_decimal(K["AVERAGE_DELIVERY_TIME"], 1)} min'
        )

    with col4:

        create_kpi(
            "Average Rating",
            format_decimal(
                K["AVERAGE_CUSTOMER_RATING"],
                2
            )
        )


    # --------------------------------------------------------
    # ORDERS BY CITY
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        data = CITY.nlargest(
            15,
            "TOTAL_ORDERS"
        )

        fig = px.bar(
            data,
            x="TOTAL_ORDERS",
            y="CITY",
            orientation="h",
            title="Orders by City",
        )

        fig.update_layout(
            height=460,
            yaxis={
                "categoryorder": "total ascending"
            },
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        if "AVERAGE_RATING" in CITY.columns:

            data = CITY.nlargest(
                15,
                "AVERAGE_RATING"
            )

            fig = px.bar(
                data,
                x="AVERAGE_RATING",
                y="CITY",
                orientation="h",
                title="Average Rating by City",
            )

            fig.update_layout(
                height=460,
                yaxis={
                    "categoryorder": "total ascending"
                },
                plot_bgcolor="white",
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # --------------------------------------------------------
    # MONTHLY ORDERS
    # --------------------------------------------------------

    monthly = MONTHLY.copy()

    if "ORDER_MONTH" in monthly.columns:

        monthly["ORDER_MONTH"] = pd.to_datetime(
            monthly["ORDER_MONTH"]
        )

        monthly = monthly.sort_values(
            "ORDER_MONTH"
        )

    fig = px.line(
        monthly,
        x="ORDER_MONTH",
        y="TOTAL_ORDERS",
        markers=True,
        title="Monthly Order Volume",
    )

    fig.update_layout(
        height=390,
        xaxis_title="",
        yaxis_title="Orders",
        plot_bgcolor="white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # PAYMENT PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Payment Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    fig = px.bar(
        PAYMENT.sort_values(
            "TOTAL_REVENUE",
            ascending=False
        ),
        x="PAYMENT_METHOD",
        y="TOTAL_REVENUE",
        title="Revenue by Payment Method",
    )

    fig.update_layout(
        height=400,
        xaxis_title="Payment Method",
        yaxis_title="Revenue (₹)",
        plot_bgcolor="white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # CITY TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'City Performance Details'
        '</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        CITY.sort_values(
            "TOTAL_REVENUE",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# PAGE 3
# RESTAURANT & FOOD
# ============================================================

else:

    st.markdown(
        '<div class="dashboard-title">'
        'Restaurant & Food Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Restaurant, food-item and revenue performance'
        '</div>',
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        create_kpi(
            "Total Restaurants",
            format_number(
                RESTAURANT["RESTAURANT_ID"].nunique()
            )
        )

    with col2:

        create_kpi(
            "Total Food Items",
            format_number(
                FOOD["FOOD_ID"].nunique()
            )
        )

    with col3:

        create_kpi(
            "Total Orders",
            format_number(K["TOTAL_ORDERS"])
        )

    with col4:

        create_kpi(
            "Total Revenue",
            format_currency(K["TOTAL_REVENUE"])
        )


    # --------------------------------------------------------
    # TOP RESTAURANTS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        data = RESTAURANT.nlargest(
            10,
            "TOTAL_REVENUE"
        )

        fig = px.bar(
            data,
            x="TOTAL_REVENUE",
            y="RESTAURANT_NAME",
            orientation="h",
            title="Top 10 Restaurants",
        )

        fig.update_layout(
            height=480,
            yaxis={
                "categoryorder": "total ascending"
            },
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        data = FOOD.nlargest(
            10,
            "TOTAL_REVENUE"
        )

        fig = px.bar(
            data,
            x="TOTAL_REVENUE",
            y="FOOD_ITEM",
            orientation="h",
            title="Top 10 Food Items",
        )

        fig.update_layout(
            height=480,
            yaxis={
                "categoryorder": "total ascending"
            },
            plot_bgcolor="white",
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # RESTAURANT PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Restaurant Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        RESTAURANT.nlargest(
            50,
            "TOTAL_REVENUE"
        ),
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # FOOD PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Food Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        FOOD.nlargest(
            50,
            "TOTAL_REVENUE"
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "SWIGGY Food Delivery Analytics | "
    "Snowflake • dbt • Airflow • Streamlit"
)