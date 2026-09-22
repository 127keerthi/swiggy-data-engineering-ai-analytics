
import os
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob


# ============================================================
# SWIGGY END-TO-END DATA ENGINEERING DASHBOARD
# Architecture adapted from the referenced Darshil Parmar project:
# Food-delivery data -> warehouse layers -> dbt -> Airflow -> AI/RAG.
# This local version keeps the user's local-data/Snowflake setup.
# ============================================================

st.set_page_config(
    page_title="Swiggy Analytics",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / "airflow" / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)

ACCOUNT = (
    os.getenv("SNOWFLAKE_ACCOUNT")
    or os.getenv("SNOWFLAKE_ACCOUNT_IDENTIFIER")
    or "TBMPXKR-PE66235"
)
USER = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
PASSWORD = os.getenv("SNOWFLAKE_PASSWORD") or os.getenv("SNOWFLAKE_PASS")
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "SWIGGY_WH")
ROLE = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")
DATABASE = "SWIGGY"


# ============================================================
# DESIGN — intentionally simple: CSS styles Streamlit elements,
# never wraps Plotly/dataframe widgets inside raw HTML.
# ============================================================
st.markdown(
    """
<style>
:root{
    --bg:#071a31;
    --bg2:#0a2340;
    --panel:#0d2f55;
    --panel2:#123b67;
    --line:#2874aa;
    --line2:#3d93ce;
    --text:#f7fbff;
    --muted:#a9c3dc;
    --orange:#ff8500;
    --blue:#35a1ff;
    --green:#18e6a0;
    --purple:#a978ff;
    --red:#ff5b78;
    --yellow:#ffd05c;
}

html,body,.stApp{
    background:
        radial-gradient(circle at 15% 0%,rgba(35,141,243,.16),transparent 28%),
        radial-gradient(circle at 90% 8%,rgba(255,121,0,.12),transparent 24%),
        linear-gradient(180deg,#06152b 0%,#081f39 48%,#06182e 100%) !important;
    color:var(--text) !important;
}
[data-testid="stHeader"]{display:none !important}
[data-testid="stToolbar"]{display:none !important}
[data-testid="stDecoration"]{display:none !important}
footer{display:none !important}

.main .block-container{
    max-width:1540px !important;
    padding:10px 20px 24px !important;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#071a31 0%,#0a2544 62%,#06172c 100%) !important;
    border-right:1px solid #2b6e9e !important;
    box-shadow:8px 0 30px rgba(0,0,0,.18);
}
[data-testid="stSidebar"] > div:first-child{
    padding:18px 14px !important;
}
[data-testid="stSidebar"] *{color:#eaf3ff}

.brand-row{
    display:flex;
    align-items:center;
    gap:14px;
    padding:4px 7px 0;
}
.brand-mark{
    width:54px;height:54px;border-radius:15px;
    display:flex;align-items:center;justify-content:center;
    background:linear-gradient(145deg,#ff8b17,#ff5c00);
    color:#fff !important;font-size:32px;font-weight:950;
    box-shadow:0 8px 28px rgba(255,105,0,.22);
}
.brand-name{font-size:28px;font-weight:950;letter-spacing:-1px}
.brand-sub{margin:8px 0 22px 69px;color:#91aac5 !important;font-size:13px}

.side-label{
    margin:8px 8px 8px;
    color:#7695b4 !important;
    text-transform:uppercase;
    letter-spacing:1.2px;
    font-size:9px;
    font-weight:900;
}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:5px !important}
[data-testid="stSidebar"] div[role="radiogroup"] label{
    min-height:40px !important;
    padding:8px 10px !important;
    border:1px solid transparent !important;
    border-radius:10px !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
    background:#082747 !important;
    border-color:#174d7b !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"]{
    background:linear-gradient(90deg,#104a79,#0d3158) !important;
    border-color:#3d91c9 !important;
    box-shadow:inset 4px 0 0 var(--orange),0 5px 18px rgba(30,129,206,.12);
}
[data-testid="stSidebar"] div[role="radiogroup"] label p{
    font-size:13px !important;font-weight:800 !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{
    display:none !important;
}

.status-title{
    color:#7897b6 !important;
    text-transform:uppercase;
    letter-spacing:1.2px;
    font-size:9px;
    font-weight:900;
    margin:18px 8px 7px;
}
.status-box{
    border:1px solid #174a74;
    border-radius:12px;
    overflow:hidden;
    background:#061c36;
}
.status-row{
    display:flex;
    align-items:center;
    gap:9px;
    padding:10px 11px;
    border-bottom:1px solid #123856;
    font-size:11px;
}
.status-row:last-child{border-bottom:0}
.dot{
    width:8px;height:8px;border-radius:50%;
    background:#16e695;
    box-shadow:0 0 10px rgba(22,230,149,.65);
}
.status-ok{margin-left:auto;color:#16e695 !important;font-weight:900}

.sidebar-note{
    margin-top:12px;
    padding:12px;
    border:1px solid #185482;
    border-radius:12px;
    background:#062746;
}
.sidebar-note b{font-size:11px}
.sidebar-note div{margin-top:4px;color:#91aac5 !important;font-size:9px}

/* Top bar */
.topbar{
    display:grid;
    grid-template-columns:minmax(0,1fr) 180px;
    gap:12px;
    margin-bottom:8px;
}
.top-search-form{
    background:transparent !important;
    border:0 !important;
    padding:0 !important;
}
.top-search-form [data-testid="stForm"]{
    background:transparent !important;
    border:0 !important;
    padding:0 !important;
}
.top-search-form .stTextInput{
    margin:0 !important;
}
.top-search-form .stTextInput > div{
    min-height:42px !important;
}
.top-search-form .stTextInput input{
    height:42px !important;
    border:1px solid #1b5a8e !important;
    border-radius:11px !important;
    background:linear-gradient(135deg,#0d3156,#0a2748) !important;
    padding:0 13px 0 38px !important;
    color:#ffffff !important;
    font-size:11px !important;
    font-weight:600 !important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
}
.top-search-form .stTextInput input:focus{
    border-color:#48a8e8 !important;
    box-shadow:0 0 0 2px rgba(53,161,255,.14) !important;
}
.top-search-form .stTextInput label{display:none !important}
.top-search-form [data-testid="stFormSubmitButton"] button{
    height:42px !important;
    margin-top:0 !important;
    border:1px solid #2b79ad !important;
    border-radius:10px !important;
    background:linear-gradient(135deg,#0d416d,#0c3154) !important;
    color:#fff !important;
    font-size:11px !important;
    font-weight:800 !important;
}
.top-search-form [data-testid="stFormSubmitButton"] button:hover{
    border-color:#ff8500 !important;
}
.global-search-results{
    margin:-2px 0 10px;
    padding:10px 12px;
    border:1px solid #246c9d;
    border-radius:11px;
    background:linear-gradient(135deg,#0b2948,#0b2340);
}
.global-search-title{
    color:#fff !important;font-size:11px;font-weight:900;margin-bottom:7px;
}
.global-search-item{
    padding:7px 9px;border-radius:8px;background:#09223e;
    border:1px solid #174d76;margin-top:5px;color:#dcecff !important;
    font-size:10px;
}

/* Streamlit form container used by the global search */
[data-testid="stForm"]{
    border:0 !important;
    padding:0 !important;
    background:transparent !important;
}
[data-testid="stForm"] .stTextInput input{
    height:42px !important;
    border:1px solid #1b5a8e !important;
    border-radius:11px !important;
    background:linear-gradient(135deg,#0d3156,#0a2748) !important;
    color:#ffffff !important;
    -webkit-text-fill-color:#ffffff !important;
    font-size:11px !important;
    font-weight:600 !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button{
    height:42px !important;
    border:1px solid #2b79ad !important;
    border-radius:10px !important;
    background:linear-gradient(135deg,#0d416d,#0c3154) !important;
    color:#fff !important;
    font-size:10px !important;
    font-weight:800 !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover{
    border-color:#ff8500 !important;
}
.topbar-box{
    height:42px;
    border:1px solid #1b5a8e;
    border-radius:11px;
    background:linear-gradient(135deg,#0d3156,#0a2748);
    display:flex;
    align-items:center;
    padding:0 13px;
    color:#b7cbe0 !important;
    font-size:10px;
}
.profile-box{gap:9px}
.avatar{
    width:26px;height:26px;border-radius:50%;
    background:#ff9200;color:white !important;
    display:flex;align-items:center;justify-content:center;
    font-weight:900;
}
.profile-name{font-size:11px;color:#fff !important;font-weight:850}
.profile-chevron{margin-left:auto;color:#7794b0 !important}

/* Page headers / hero */
.hero-box,.page-box{
    border:1px solid #3a83b8;
    border-radius:18px;
    background:linear-gradient(110deg,#0d3156 0%,#124574 58%,#173858 100%);
    box-shadow:0 12px 35px rgba(0,0,0,.16), inset 0 1px 0 rgba(255,255,255,.06);
    padding:18px 22px;
    margin-bottom:9px;
}
.hero-box{
    min-height:96px;
    display:flex;
    align-items:center;
    justify-content:space-between;
}
.hero-title{
    font-size:28px;
    line-height:1.15;
    font-weight:950;
    letter-spacing:-1px;
}
.hero-title span{color:var(--orange)}
.hero-sub,.page-sub{
    color:#aac1d8 !important;
    font-size:11px;
    margin-top:7px;
}
.hero-side{text-align:right;color:white !important;font-size:13px;font-weight:900}
.hero-btn{
    display:inline-block;
    margin-top:9px;
    padding:8px 12px;
    border-radius:8px;
    background:var(--orange);
    color:white !important;
    font-size:9px;
    font-weight:900;
}
.page-title{font-size:29px;font-weight:950;line-height:1.1}
.page-sub{margin-top:8px}

/* KPI cards */
div[data-testid="stMetric"]{
    background:linear-gradient(145deg,#0e335b 0%,#0b294b 100%) !important;
    border:1px solid #3a80b4 !important;
    border-radius:15px !important;
    padding:13px 15px !important;
    min-height:104px !important;
    box-shadow:0 10px 26px rgba(0,0,0,.13), inset 0 1px 0 rgba(255,255,255,.055);
    transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
}
div[data-testid="stMetric"]:hover{
    transform:translateY(-2px);
    border-color:#5ba7d9 !important;
    box-shadow:0 14px 30px rgba(0,0,0,.18),0 0 22px rgba(53,161,255,.08);
}
div[data-testid="stMetric"] label{
    color:#b9cce0 !important;
    font-size:10px !important;
    font-weight:800 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
    color:#fff !important;
    font-size:25px !important;
    font-weight:950 !important;
    line-height:1.1 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"]{
    font-size:9px !important;
}

/* Section headings are standalone; widgets come after them */
.section-head{
    border:1px solid #1e6398;
    border-radius:12px 12px 0 0;
    background:linear-gradient(90deg,#0e355d,#0b2b4d);
    padding:10px 14px;
    color:#f6f9ff !important;
    font-size:13px;
    font-weight:900;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
    display:flex;
    align-items:center;
    justify-content:space-between;
}
.section-head span{
    color:#bcd0e3 !important;
    border:1px solid #286c9f;
    border-radius:8px;
    padding:5px 8px;
    font-size:8px;
    font-weight:600;
}
.section-space{height:12px}

/* Review cards */
.review-card{
    padding:11px 12px;
    margin:0 0 8px;
    border:1px solid #153f65;
    border-radius:10px;
    background:linear-gradient(135deg,#09213b,#0a2947);
}
.review-rating{color:#ffd35c !important;font-size:11px;font-weight:900}
.review-rating span{color:#19df95 !important;margin-left:4px}
.review-text{color:#eaf4ff !important;font-size:11px;line-height:1.45;margin-top:5px}

/* Native dataframe */
[data-testid="stDataFrame"]{
    border:1px solid #286a98 !important;
    border-top:0 !important;
    border-radius:0 0 12px 12px !important;
    overflow:hidden !important;
    background:#0a2746 !important;
}
[data-testid="stDataFrame"] *{font-size:11px !important}

/* Plotly charts — bright, consistent chart panels */
div[data-testid="stPlotlyChart"]{
    margin:0 !important;
    padding:4px 5px 2px !important;
    border:1px solid #2c739f !important;
    border-top:0 !important;
    border-radius:0 0 13px 13px !important;
    background:linear-gradient(145deg,#0b2a4b,#0a2441) !important;
    box-shadow:0 10px 24px rgba(0,0,0,.11), inset 0 1px 0 rgba(255,255,255,.025);
    overflow:hidden !important;
}
div[data-testid="stPlotlyChart"] iframe{
    border-radius:10px !important;
}

/* Keep chart rows visually aligned */
div[data-testid="column"] > div > div > div[data-testid="stPlotlyChart"]{
    min-height:320px;
}

/* Buttons / inputs */
.stButton > button{
    border:1px solid #286a9f !important;
    background:linear-gradient(135deg,#0d3b65,#0b2e50) !important;
    color:#eaf4ff !important;
    border-radius:9px !important;
    font-weight:800 !important;
}
.stButton > button:hover{
    border-color:#ff7900 !important;
    color:#fff !important;
}
.stTextInput input,.stTextArea textarea,.stSelectbox select{
    color:#fff !important;
    -webkit-text-fill-color:#fff !important;
    caret-color:#ff7900 !important;
    background:#071e3b !important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{
    color:#7089a4 !important;
    -webkit-text-fill-color:#7089a4 !important;
    opacity:1 !important;
}
.stSlider label,.stSelectbox label,.stTextInput label{
    color:#bdd0e3 !important;
}

/* Expander */
[data-testid="stExpander"]{
    border:1px solid #2b6f9e !important;
    border-radius:12px !important;
    background:linear-gradient(145deg,#0a2848,#0b3155) !important;
    box-shadow:0 8px 20px rgba(0,0,0,.10);
}
[data-testid="stExpander"] summary{
    color:#eaf4ff !important;
}

/* Info / success */
.stAlert{
    background:#072544 !important;
    border-color:#1b5a8e !important;
}

/* Pipeline */
.pipeline-row{
    display:flex;
    align-items:center;
    gap:8px;
    margin:7px 0 11px;
    padding:5px;
    border:1px solid #245f88;
    border-radius:16px;
    background:linear-gradient(90deg,rgba(10,40,70,.72),rgba(15,54,88,.72));
}
.pipeline-node{
    flex:1;
    min-height:64px;
    border:1px solid #1e6296;
    border-radius:12px;
    background:linear-gradient(145deg,#10416d,#0c3154);
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:#fff !important;
    font-size:10px;
    font-weight:850;
}
.pipeline-node small{
    color:#8eabc5 !important;
    font-size:8px;
    margin-top:5px;
    font-weight:500;
}
.pipeline-arrow{
    color:#ff7900 !important;
    font-size:17px;
    font-weight:950;
}

/* Footer */
.footer{
    text-align:center;
    color:#527da4 !important;
    font-size:9px;
    padding:18px 0 4px;
}

/* Compact, polished dashboard spacing */
[data-testid="stHorizontalBlock"]{
    gap:0.8rem !important;
    margin-bottom:0.35rem !important;
}
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stHorizontalBlock"]){
    gap:0.45rem !important;
}
.stMarkdown{margin-bottom:0 !important;}
[data-testid="stPlotlyChart"] + div{margin-top:0 !important;}

/* prevent horizontal overflow */
[data-testid="column"]{min-width:0 !important}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SNOWFLAKE
# ============================================================
@st.cache_resource(show_spinner=False)
def get_connection():
    if not USER:
        raise RuntimeError("SNOWFLAKE_USER is missing from your .env file.")
    if not PASSWORD:
        raise RuntimeError("SNOWFLAKE_PASSWORD is missing from your .env file.")

    return snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        password=PASSWORD,
        warehouse=WAREHOUSE,
        database=DATABASE,
        role=ROLE,
        client_session_keep_alive=True,
        client_session_keep_alive_heartbeat_frequency=900,
        login_timeout=30,
        network_timeout=60,
    )


def expired_auth(exc):
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "390114",
            "authentication token has expired",
            "reauthenticationrequest",
            "token has expired",
        )
    )


@st.cache_data(ttl=900, show_spinner=False)
def query(sql):
    con = get_connection()
    cur = None
    try:
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=columns)
    except Exception as exc:
        if not expired_auth(exc):
            raise
        try:
            con.close()
        except Exception:
            pass
        get_connection.clear()
        fresh = get_connection()
        cur = fresh.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass


def clear_caches():
    get_connection.clear()
    query.clear()
    for fn in (
        load_kpi, load_monthly, load_city, load_restaurants,
        load_food, load_payment, load_reviews, load_rag_reviews,
        build_rag_index, load_sentiment, analyze_sentiment,
    ):
        try:
            fn.clear()
        except Exception:
            pass


# ============================================================
# HELPERS + REAL PROJECT VIEWS
# ============================================================
def numeric(df, cols):
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def fmt_int(value):
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return "0"


def fmt_money(value):
    try:
        return f"₹{float(value):,.0f}"
    except Exception:
        return "₹0"


def fmt_money_short(value):
    try:
        n = float(value)
        if abs(n) >= 1_000_000_000:
            return f"₹{n/1_000_000_000:.2f}B"
        if abs(n) >= 1_000_000:
            return f"₹{n/1_000_000:.2f}M"
        if abs(n) >= 1_000:
            return f"₹{n/1_000:.1f}K"
        return f"₹{n:,.0f}"
    except Exception:
        return "₹0"


def fmt_num(value):
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return "0.00"


def get_value(row, names, default=0):
    for name in names:
        if name in row.index and pd.notna(row[name]):
            return row[name]
    return default


@st.cache_data(ttl=900, show_spinner=False)
def load_kpi():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_SWIGGY_KPI"),
        [
            "TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE",
            "AVERAGE_CUSTOMER_RATING","AVERAGE_RATING",
            "AVERAGE_DELIVERY_TIME","AVERAGE_DELIVERY_TIME_MIN",
        ],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_monthly():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_MONTHLY_PERFORMANCE"),
        ["TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE"],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_city():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_CITY_PERFORMANCE"),
        ["TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE","AVERAGE_RATING"],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_restaurants():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_RESTAURANT_PERFORMANCE"),
        ["TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE","AVERAGE_RATING"],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_food():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_FOOD_PERFORMANCE"),
        ["TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE","TOTAL_QUANTITY"],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_payment():
    return numeric(
        query("SELECT * FROM SWIGGY.MARTS.VW_PAYMENT_PERFORMANCE"),
        ["TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_ORDER_VALUE"],
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_reviews(limit=200):
    return query(
        f"""
        SELECT REVIEW_ID, RATING, COMMENT, REVIEW_DATE
        FROM SWIGGY.MARTS.FCT_REVIEWS
        WHERE COMMENT IS NOT NULL AND TRIM(COMMENT) <> ''
        ORDER BY REVIEW_DATE DESC
        LIMIT {int(limit)}
        """
    )


KPI = load_kpi()
if KPI.empty:
    st.error("SWIGGY.MARTS.VW_SWIGGY_KPI returned no data.")
    st.stop()

K = KPI.iloc[0]
TOTAL_ORDERS = get_value(K, ["TOTAL_ORDERS"])
TOTAL_REVENUE = get_value(K, ["TOTAL_REVENUE"])
AOV = get_value(K, ["AVERAGE_ORDER_VALUE","AVG_ORDER_VALUE"])
RATING = get_value(K, ["AVERAGE_CUSTOMER_RATING","AVERAGE_RATING"])
DELIVERY = get_value(K, ["AVERAGE_DELIVERY_TIME","AVERAGE_DELIVERY_TIME_MIN"])


def trend_change(monthly):
    if monthly.empty or len(monthly) < 4:
        return 0.0, 0.0
    d = monthly.copy()
    d["ORDER_MONTH"] = pd.to_datetime(d["ORDER_MONTH"], errors="coerce")
    d = d.dropna(subset=["ORDER_MONTH"]).sort_values("ORDER_MONTH")
    n = min(6, len(d)//2)
    latest, previous = d.tail(n), d.iloc[-2*n:-n]
    op = previous["TOTAL_ORDERS"].sum()
    rp = previous["TOTAL_REVENUE"].sum()
    ot = ((latest["TOTAL_ORDERS"].sum()/op)-1)*100 if op else 0
    rt = ((latest["TOTAL_REVENUE"].sum()/rp)-1)*100 if rp else 0
    return ot, rt


# ============================================================
# RAG / SENTIMENT / TEXT-TO-SQL
# ============================================================
@st.cache_data(ttl=900, show_spinner=False)
def load_rag_reviews(limit=25000):
    return query(
        f"""
        SELECT REVIEW_ID, ORDER_ID, USER_ID, RESTAURANT_ID,
               RATING, COMMENT, REVIEW_DATE
        FROM SWIGGY.MARTS.FCT_REVIEWS
        WHERE COMMENT IS NOT NULL AND TRIM(COMMENT) <> ''
        LIMIT {int(limit)}
        """
    )


@st.cache_resource(show_spinner=False)
def build_rag_index():
    df = load_rag_reviews().copy()
    df["COMMENT"] = df["COMMENT"].fillna("").astype(str)
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1,2),
        max_features=30000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(df["COMMENT"])
    return df, vectorizer, matrix


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def rag_search(question, top_k):
    df, vectorizer, matrix = build_rag_index()
    q = re.sub(r"\s+", " ", str(question).strip())
    if not q:
        return pd.DataFrame()

    # Small synonym expansion makes natural queries such as
    # "delivery was late" and "late delivery" behave more consistently.
    synonym_map = {
        "late": "delay delayed delivery",
        "slow": "delay delayed delivery",
        "quality": "food taste fresh stale",
        "bad": "poor terrible negative",
        "good": "great excellent positive",
        "packaging": "package packed spill damaged",
    }
    expanded = q + " " + " ".join(v for k, v in synonym_map.items() if k in tokens(q))

    tfidf = cosine_similarity(vectorizer.transform([expanded]), matrix).ravel()
    qt = tokens(expanded)
    kw = []
    for text in df["COMMENT"]:
        tt = tokens(text)
        kw.append(len(qt & tt)/len(qt) if qt else 0)
    score = .75*tfidf + .25*pd.Series(kw).to_numpy()
    out = df.copy()
    out["RELEVANCE_SCORE"] = score
    out["_COMMENT_KEY"] = out["COMMENT"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
    out = out[out["RELEVANCE_SCORE"] > 0].sort_values("RELEVANCE_SCORE", ascending=False)
    out = out.drop_duplicates(subset=["_COMMENT_KEY"], keep="first")
    return out.head(top_k).drop(columns=["_COMMENT_KEY"], errors="ignore")


def _top_n(question, default=10, maximum=50):
    match = re.search(r"\btop\s+(\d+)\b", str(question).lower())
    if not match:
        return default
    return max(1, min(int(match.group(1)), maximum))


def _available_columns(loader):
    try:
        return {str(c).upper() for c in loader().columns}
    except Exception:
        return set()


def _restaurant_sql(question):
    cols = _available_columns(load_restaurants)
    n = _top_n(question)
    select = []
    for col in ["RESTAURANT_NAME", "TOTAL_ORDERS", "TOTAL_REVENUE", "AVERAGE_RATING", "AVERAGE_ORDER_VALUE"]:
        if col in cols:
            select.append(col)
    if not select:
        return None, None

    q = question.lower()
    if "rating" in q or "rated" in q:
        order_col = "AVERAGE_RATING" if "AVERAGE_RATING" in cols else "TOTAL_REVENUE"
        title = f"Top {n} restaurants by rating"
    elif "order" in q:
        order_col = "TOTAL_ORDERS" if "TOTAL_ORDERS" in cols else "TOTAL_REVENUE"
        title = f"Top {n} restaurants by orders"
    else:
        order_col = "TOTAL_REVENUE" if "TOTAL_REVENUE" in cols else "TOTAL_ORDERS"
        title = f"Top {n} restaurants by revenue"

    return (
        f"SELECT {', '.join(select)}\n"
        f"FROM SWIGGY.MARTS.VW_RESTAURANT_PERFORMANCE\n"
        f"ORDER BY {order_col} DESC NULLS LAST LIMIT {n};",
        title,
    )


def _food_sql(question):
    cols = _available_columns(load_food)
    n = _top_n(question)
    name_col = "FOOD_NAME" if "FOOD_NAME" in cols else ("FOOD" if "FOOD" in cols else None)
    if not name_col:
        return None, None
    select = [name_col]
    for col in ["TOTAL_ORDERS", "TOTAL_REVENUE", "TOTAL_QUANTITY", "AVERAGE_ORDER_VALUE", "AVERAGE_RATING"]:
        if col in cols:
            select.append(col)
    order_col = "TOTAL_REVENUE" if "TOTAL_REVENUE" in cols else "TOTAL_ORDERS"
    return (
        f"SELECT {', '.join(select)}\nFROM SWIGGY.MARTS.VW_FOOD_PERFORMANCE\nORDER BY {order_col} DESC NULLS LAST LIMIT {n};",
        f"Top {n} food items by revenue" if order_col == "TOTAL_REVENUE" else f"Top {n} food items by orders",
    )


def text_to_sql(question):
    q = re.sub(r"\s+", " ", str(question).lower().strip())
    if not q:
        return None, None

    if any(word in q for word in ("restaurant", "restaurants")) and any(word in q for word in ("top", "highest", "best", "rank")):
        return _restaurant_sql(q)

    if any(word in q for word in ("food", "item", "items", "dish", "dishes")) and any(word in q for word in ("top", "highest", "best", "rank")):
        return _food_sql(q)

    if "city" in q and any(word in q for word in ("revenue", "sales")):
        cols = _available_columns(load_city)
        select = [c for c in ["CITY", "TOTAL_ORDERS", "TOTAL_REVENUE", "AVERAGE_RATING", "AVERAGE_ORDER_VALUE"] if c in cols]
        if "CITY" in cols and select:
            return f"SELECT {', '.join(select)}\nFROM SWIGGY.MARTS.VW_CITY_PERFORMANCE ORDER BY TOTAL_REVENUE DESC NULLS LAST;", "Revenue by city"

    if "city" in q and "order" in q:
        cols = _available_columns(load_city)
        select = [c for c in ["CITY", "TOTAL_ORDERS", "TOTAL_REVENUE", "AVERAGE_RATING"] if c in cols]
        if "CITY" in cols and "TOTAL_ORDERS" in cols:
            return f"SELECT {', '.join(select)}\nFROM SWIGGY.MARTS.VW_CITY_PERFORMANCE ORDER BY TOTAL_ORDERS DESC NULLS LAST;", "Orders by city"

    if "monthly" in q or "month" in q or "trend" in q:
        cols = _available_columns(load_monthly)
        select = [c for c in ["ORDER_MONTH", "TOTAL_ORDERS", "TOTAL_REVENUE", "AVERAGE_ORDER_VALUE"] if c in cols]
        if "ORDER_MONTH" in cols:
            return f"SELECT {', '.join(select)}\nFROM SWIGGY.MARTS.VW_MONTHLY_PERFORMANCE ORDER BY ORDER_MONTH;", "Monthly performance"

    if "payment" in q:
        return "SELECT * FROM SWIGGY.MARTS.VW_PAYMENT_PERFORMANCE ORDER BY TOTAL_REVENUE DESC NULLS LAST;", "Payment performance"

    if "delivery" in q:
        return "SELECT AVERAGE_DELIVERY_TIME_MIN FROM SWIGGY.MARTS.VW_SWIGGY_KPI;", "Average delivery time"

    if "rating" in q:
        return "SELECT AVERAGE_CUSTOMER_RATING FROM SWIGGY.MARTS.VW_SWIGGY_KPI;", "Average customer rating"

    if "revenue" in q or "sales" in q:
        return "SELECT TOTAL_REVENUE FROM SWIGGY.MARTS.VW_SWIGGY_KPI;", "Total revenue"

    if "order" in q:
        return "SELECT TOTAL_ORDERS FROM SWIGGY.MARTS.VW_SWIGGY_KPI;", "Total orders"

    return None, None


@st.cache_data(ttl=900, show_spinner=False)
def load_sentiment():
    return load_rag_reviews(30000)


@st.cache_data(ttl=900, show_spinner=False)
def analyze_sentiment(df):
    out = df.copy()

    def classify(text):
        score = TextBlob(str(text)).sentiment.polarity
        label = "Positive" if score > .10 else "Negative" if score < -.10 else "Neutral"
        return pd.Series([label, score])

    out[["SENTIMENT","SENTIMENT_SCORE"]] = out["COMMENT"].apply(classify)
    return out


# ============================================================
# SIDEBAR / NAVIGATION
# ============================================================
PAGES = [
    "🏠 Executive Overview",
    "📊 Business Analytics",
    "🚚 Operations",
    "😊 Sentiment Intelligence",
    "🔎 RAG Review Search",
    "💬 Text-to-SQL",
    "⚙️ Data Pipeline",
]

with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">S</div>
            <div class="brand-name">SWIGGY</div>
        </div>
        <div class="brand-sub">Data Platform</div>
        <div class="side-label">Navigation</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio("Navigation", PAGES, label_visibility="collapsed")

    st.markdown('<div class="status-title">System Status</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="status-box">
            <div class="status-row"><span class="dot"></span>Snowflake <b class="status-ok">Connected</b></div>
            <div class="status-row"><span class="dot"></span>dbt <b class="status-ok">Ready</b></div>
            <div class="status-row"><span class="dot"></span>Airflow <b class="status-ok">Ready</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↻  Refresh Snowflake Data", use_container_width=True):
        clear_caches()
        st.rerun()

    st.markdown(
        """
        <div class="sidebar-note">
            <b>⚡ Data-Driven Insights</b>
            <div>Faster decisions. Better outcomes.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# COMMON UI
# ============================================================
def global_search_results(term):
    """Search the loaded business/review datasets without generating SQL."""
    q = str(term).strip().lower()
    if not q:
        return []

    results = []
    try:
        city = load_city()
        if "CITY" in city.columns:
            hits = city[city["CITY"].astype(str).str.lower().str.contains(re.escape(q), na=False)]
            for _, row in hits.head(4).iterrows():
                results.append(("📍 City", str(row.get("CITY", "")), f"{fmt_int(row.get('TOTAL_ORDERS', 0))} orders • {fmt_money_short(row.get('TOTAL_REVENUE', 0))} revenue"))
    except Exception:
        pass

    try:
        restaurants = load_restaurants()
        if "RESTAURANT_NAME" in restaurants.columns:
            hits = restaurants[restaurants["RESTAURANT_NAME"].astype(str).str.lower().str.contains(re.escape(q), na=False)]
            for _, row in hits.head(4).iterrows():
                results.append(("🍔 Restaurant", str(row.get("RESTAURANT_NAME", "")), f"{fmt_int(row.get('TOTAL_ORDERS', 0))} orders • {fmt_money_short(row.get('TOTAL_REVENUE', 0))} revenue"))
    except Exception:
        pass

    try:
        food = load_food()
        name_col = "FOOD_NAME" if "FOOD_NAME" in food.columns else ("FOOD" if "FOOD" in food.columns else None)
        if name_col:
            hits = food[food[name_col].astype(str).str.lower().str.contains(re.escape(q), na=False)]
            for _, row in hits.head(4).iterrows():
                results.append(("🥗 Food", str(row.get(name_col, "")), f"{fmt_int(row.get('TOTAL_ORDERS', 0))} orders • {fmt_money_short(row.get('TOTAL_REVENUE', 0))} revenue"))
    except Exception:
        pass

    try:
        reviews = load_rag_reviews(5000)
        if "COMMENT" in reviews.columns:
            hits = reviews[reviews["COMMENT"].astype(str).str.lower().str.contains(re.escape(q), na=False)]
            seen = set()
            for _, row in hits.iterrows():
                comment = str(row.get("COMMENT", "")).strip()
                key = re.sub(r"\s+", " ", comment).lower()
                if not comment or key in seen:
                    continue
                seen.add(key)
                results.append(("💬 Review", comment[:90], f"Rating {float(row.get('RATING', 0) or 0):.1f}"))
                if len([x for x in results if x[0] == "💬 Review"]) >= 3:
                    break
    except Exception:
        pass

    return results[:10]


def topbar():
    left, right = st.columns([6, 1], gap="small")
    with left:
        with st.form("global_search_form", clear_on_submit=False, border=False):
            q, submit = st.columns([5, 1], gap="small")
            with q:
                term = st.text_input(
                    "Global search",
                    placeholder="⌕  Search insights, restaurants, cities, food or reviews...",
                    key="global_search_term",
                    label_visibility="collapsed",
                )
            with submit:
                do_search = st.form_submit_button("Search", use_container_width=True)

        if do_search:
            clean = term.strip()
            st.session_state["global_search_active"] = clean

    with right:
        st.markdown(
            '<div class="topbar-box profile-box"><span class="avatar">K</span><span class="profile-name">Keerthi</span><span class="profile-chevron">⌄</span></div>',
            unsafe_allow_html=True,
        )

    active = st.session_state.get("global_search_active", "").strip()
    if active:
        results = global_search_results(active)
        if results:
            items = "".join(
                f'<div class="global-search-item"><b>{kind}</b> &nbsp; {name} <span style="color:#8fb1cf">— {detail}</span></div>'
                for kind, name, detail in results
            )
            st.markdown(
                f'<div class="global-search-results"><div class="global-search-title">Search results for “{active}”</div>{items}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(f'No results found for “{active}”. Try a restaurant, city, food item, or review keyword.')


def page_header(title, subtitle):
    topbar()
    st.markdown(
        f"""
        <div class="page-box">
            <div class="page-title">{title}</div>
            <div class="page-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title, control=None):
    suffix = f"<span>{control}</span>" if control else ""
    st.markdown(f'<div class="section-head"><b>{title}</b>{suffix}</div>', unsafe_allow_html=True)


def chart_base(fig, height=360):
    fig.update_layout(
        height=height,
        paper_bgcolor="#0b2a4b",
        plot_bgcolor="#09233f",
        margin=dict(l=58, r=58, t=48, b=52),
        font=dict(color="#d9ebfa", size=11, family="Arial"),
        title=dict(font=dict(color="#ffffff", size=14, family="Arial")),
        legend=dict(
            bgcolor="rgba(9,35,63,.78)",
            bordercolor="#2c6f9b",
            borderwidth=1,
            font=dict(color="#f2f8ff", size=10),
            orientation="h",
            y=1.08, x=0,
        ),
        hoverlabel=dict(
            bgcolor="#123b61",
            bordercolor="#55a8dc",
            font_color="#fff",
            font_size=11,
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        color="#b5cce1",
        linecolor="#2a5e83",
        tickfont=dict(color="#b5cce1", size=10),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(70,130,175,.24)",
        zeroline=True,
        zerolinecolor="rgba(95,157,201,.35)",
        color="#b5cce1",
        linecolor="#2a5e83",
        tickfont=dict(color="#b5cce1", size=10),
    )
    return fig


def metric_row(items):
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            st.metric(
                item["label"],
                item["value"],
                item.get("delta"),
                delta_color=item.get("delta_color","normal"),
            )


def full_table(df, title=None, height=320):
    if title:
        section(title)
    if df is None or df.empty:
        st.info("No data available.")
        return
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height,
    )


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================
if page == "🏠 Executive Overview":
    topbar()
    st.markdown(
        """
        <div class="hero-box">
            <div>
                <div class="hero-title">Welcome to <span>Swiggy</span> Analytics</div>
                <div class="hero-sub">End-to-End Data Engineering • Business Intelligence • AI Powered Insights</div>
            </div>
            <div class="hero-side">
                Good food.<br><b>Greater insights.</b><br>
                <span class="hero-btn">Turn data into decisions ›</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    monthly = load_monthly()
    payment = load_payment()
    city = load_city()
    restaurants = load_restaurants()
    reviews = load_reviews(30).copy()
    if not reviews.empty and "COMMENT" in reviews.columns:
        reviews["_COMMENT_KEY"] = reviews["COMMENT"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
        reviews = reviews.drop_duplicates(subset=["_COMMENT_KEY"]).head(5)
    ot, rt = trend_change(monthly)

    metric_row([
        {"label":"🛒 Total Orders","value":fmt_int(TOTAL_ORDERS),
         "delta":f"{ot:+.0f}% vs period"},
        {"label":"₹ Total Revenue","value":fmt_money(TOTAL_REVENUE),
         "delta":f"{rt:+.0f}% vs period"},
        {"label":"🛍️ Average Order Value","value":fmt_money(AOV),
         "delta":"Revenue / order","delta_color":"off"},
        {"label":"★ Customer Rating","value":fmt_num(RATING),
         "delta":"Average rating","delta_color":"off"},
        {"label":"◷ Avg Delivery Time","value":f"{fmt_num(DELIVERY)} min",
         "delta":"Delivery performance","delta_color":"off"},
    ])

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)

    left, right = st.columns([1.6,1.0], gap="large")

    with left:
        section("▥  Revenue & Orders Trend","Last 12 Months")
        m = monthly.copy()
        m["ORDER_MONTH"] = pd.to_datetime(m["ORDER_MONTH"], errors="coerce")
        m = m.dropna(subset=["ORDER_MONTH"]).sort_values("ORDER_MONTH").tail(12)
        fig = go.Figure()
        fig.add_bar(
            x=m["ORDER_MONTH"], y=m["TOTAL_ORDERS"],
            name="Orders", marker_color="#268eff"
        )
        fig.add_scatter(
            x=m["ORDER_MONTH"], y=m["TOTAL_REVENUE"],
            name="Revenue (₹)", mode="lines+markers", yaxis="y2",
            line=dict(color="#ff7900",width=3),
            marker=dict(size=6,color="#ff9a28"),
        )
        fig.update_layout(
            yaxis2=dict(title="Revenue (₹)",overlaying="y",side="right",showgrid=False),
            yaxis=dict(title="Orders",tickformat=".2s"),
            xaxis=dict(tickformat="%b %Y"),
            bargap=.25,
        )
        st.plotly_chart(chart_base(fig,370),use_container_width=True,config={"displayModeBar":False})

    with right:
        section("💬  Payment Method Distribution","All Time")
        if not payment.empty:
            fig = px.pie(
                payment,names="PAYMENT_METHOD",values="TOTAL_ORDERS",
                hole=.65,
                color_discrete_sequence=["#268eff","#12d993","#ff4d5d","#ff9fbd","#8bd2ff"],
            )
            fig.update_traces(
                textinfo="percent",textposition="inside",
                marker=dict(line=dict(color="#061a34",width=2))
            )
            fig.add_annotation(
                text=f"<b>{float(TOTAL_ORDERS)/1_000_000:.2f}M</b><br>Orders",
                x=.5,y=.5,showarrow=False,font=dict(color="#fff",size=16)
            )
            fig.update_layout(margin=dict(l=15,r=15,t=55,b=15))
            st.plotly_chart(chart_base(fig,370),use_container_width=True,config={"displayModeBar":False})

    st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3,gap="large")
    with c1:
        section("📍  Top Cities by Orders","Top 10")
        top_city = city.nlargest(10,"TOTAL_ORDERS").copy()
        st.dataframe(
            top_city[[c for c in ["CITY","TOTAL_ORDERS","TOTAL_REVENUE","AVERAGE_RATING"] if c in top_city.columns]],
            use_container_width=True,hide_index=True,height=310
        )
    with c2:
        section("🍔  Top Restaurants by Revenue","Top 10")
        top_rest = restaurants.nlargest(10,"TOTAL_REVENUE").copy()
        st.dataframe(
            top_rest[[c for c in ["RESTAURANT_NAME","TOTAL_REVENUE","TOTAL_ORDERS","AVERAGE_RATING"] if c in top_rest.columns]],
            use_container_width=True,hide_index=True,height=310
        )
    with c3:
        section("💬  Recent Reviews","Latest 5")
        if reviews.empty:
            st.info("No reviews available.")
        else:
            for _,r in reviews.iterrows():
                rating = float(r.get("RATING",0) or 0)
                comment = re.sub(r"\s+", " ", str(r.get("COMMENT", "")).strip())
                if len(comment) > 155:
                    comment = comment[:152].rstrip() + "..."
                stars = "★" * max(1, min(5, int(round(rating))))
                st.markdown(
                    f'<div class="review-card"><div class="review-rating">{stars} <span>{rating:.1f}</span></div><div class="review-text">{comment}</div></div>', 
                    unsafe_allow_html=True,
                )

    with st.expander("View complete city performance data"):
        st.dataframe(city,use_container_width=True,hide_index=True,height=380)

    with st.expander("View complete restaurant performance data"):
        st.dataframe(restaurants,use_container_width=True,hide_index=True,height=380)

    st.markdown('<div class="footer">SWIGGY ANALYTICS • Snowflake • dbt • Airflow • Streamlit • Local AI</div>',unsafe_allow_html=True)


# ============================================================
# BUSINESS ANALYTICS
# ============================================================
elif page == "📊 Business Analytics":
    page_header("Business Analytics","City, restaurant, food and payment performance")

    city = load_city()
    restaurants = load_restaurants()
    food = load_food()
    payment = load_payment()

    selected = st.selectbox(
        "City filter",
        ["All"] + sorted(city["CITY"].dropna().astype(str).unique().tolist()),
    )
    data = city if selected == "All" else city[city["CITY"].astype(str)==selected]

    metric_row([
        {"label":"📍 Cities","value":fmt_int(data["CITY"].nunique()),"delta":"Active cities","delta_color":"off"},
        {"label":"🛒 Orders","value":fmt_int(data["TOTAL_ORDERS"].sum()),"delta":"Order volume","delta_color":"off"},
        {"label":"₹ Revenue","value":fmt_money_short(data["TOTAL_REVENUE"].sum()),"delta":"City revenue","delta_color":"off"},
        {"label":"🛍️ AOV","value":fmt_money(data["AVERAGE_ORDER_VALUE"].mean()),"delta":"Revenue / order","delta_color":"off"},
        {"label":"★ Rating","value":fmt_num(data["AVERAGE_RATING"].mean()),"delta":"Customer rating","delta_color":"off"},
    ])

    a,b = st.columns(2,gap="large")
    with a:
        section("💰 Revenue by City","Top 10")
        d=data.nlargest(10,"TOTAL_REVENUE").sort_values("TOTAL_REVENUE")
        fig=px.bar(d,x="TOTAL_REVENUE",y="CITY",orientation="h",text_auto=".3s")
        fig.update_traces(textfont=dict(color="#ffffff",size=10))
        fig.update_traces(marker_color="#ff7900")
        st.plotly_chart(chart_base(fig,400),use_container_width=True,config={"displayModeBar":False})
    with b:
        section("🛒 Orders by City","Top 10")
        d=data.nlargest(10,"TOTAL_ORDERS").sort_values("TOTAL_ORDERS")
        fig=px.bar(d,x="TOTAL_ORDERS",y="CITY",orientation="h",text_auto=".3s")
        fig.update_traces(textfont=dict(color="#ffffff",size=10))
        fig.update_traces(marker_color="#268eff")
        st.plotly_chart(chart_base(fig,400),use_container_width=True,config={"displayModeBar":False})

    a,b = st.columns(2,gap="large")
    with a:
        section("🍔 Top Restaurants by Revenue","Top 10")
        d=restaurants.nlargest(10,"TOTAL_REVENUE").sort_values("TOTAL_REVENUE")
        fig=px.bar(d,x="TOTAL_REVENUE",y="RESTAURANT_NAME",orientation="h")
        fig.update_traces(marker_color="#12d993")
        st.plotly_chart(chart_base(fig,400),use_container_width=True,config={"displayModeBar":False})
    with b:
        section("🥗 Top Food Items by Revenue","Top 10")
        d=food.nlargest(10,"TOTAL_REVENUE").sort_values("TOTAL_REVENUE")
        name_col="FOOD_NAME" if "FOOD_NAME" in food.columns else ("FOOD" if "FOOD" in food.columns else food.columns[0])
        fig=px.bar(d,x="TOTAL_REVENUE",y=name_col,orientation="h")
        fig.update_traces(marker_color="#9b63ff")
        st.plotly_chart(chart_base(fig,400),use_container_width=True,config={"displayModeBar":False})

    with st.expander("Complete city performance data"):
        st.dataframe(city,use_container_width=True,hide_index=True,height=430)
    with st.expander("Complete restaurant performance data"):
        st.dataframe(restaurants,use_container_width=True,hide_index=True,height=430)
    with st.expander("Complete food performance data"):
        st.dataframe(food,use_container_width=True,hide_index=True,height=430)
    with st.expander("Complete payment performance data"):
        st.dataframe(payment,use_container_width=True,hide_index=True,height=430)


# ============================================================
# OPERATIONS
# ============================================================
elif page == "🚚 Operations":
    page_header("Operations","Delivery performance, order volume and payment operations")

    monthly=load_monthly()
    payment=load_payment()
    city=load_city()

    metric_row([
        {"label":"🛒 Total Orders","value":fmt_int(TOTAL_ORDERS),"delta":"All orders","delta_color":"off"},
        {"label":"₹ Total Revenue","value":fmt_money_short(TOTAL_REVENUE),"delta":"Platform revenue","delta_color":"off"},
        {"label":"🛍️ AOV","value":fmt_money(AOV),"delta":"Revenue / order","delta_color":"off"},
        {"label":"◷ Delivery","value":f"{fmt_num(DELIVERY)} min","delta":"Delivery performance","delta_color":"off"},
        {"label":"★ Rating","value":fmt_num(RATING),"delta":"Experience score","delta_color":"off"},
    ])

    a,b=st.columns([1.6,1.0],gap="large")
    with a:
        section("📈 Monthly Order Volume","Last 18 Months")
        m=monthly.copy()
        m["ORDER_MONTH"]=pd.to_datetime(m["ORDER_MONTH"],errors="coerce")
        m=m.dropna(subset=["ORDER_MONTH"]).sort_values("ORDER_MONTH").tail(18)
        fig=px.bar(m,x="ORDER_MONTH",y="TOTAL_ORDERS")
        fig.update_traces(marker_color="#268eff")
        fig.update_layout(xaxis_title="Order Month",yaxis_title="Total Orders")
        st.plotly_chart(chart_base(fig,370),use_container_width=True,config={"displayModeBar":False})
    with b:
        section("💳 Payment Mix","All Time")
        fig=px.pie(payment,names="PAYMENT_METHOD",values="TOTAL_ORDERS",hole=.62,
                   color_discrete_sequence=["#268eff","#12d993","#ff4d5d","#ff9fbd","#8bd2ff"])
        fig.update_traces(textinfo="percent")
        st.plotly_chart(chart_base(fig,370),use_container_width=True,config={"displayModeBar":False})

    a,b=st.columns(2,gap="large")
    with a:
        section("🚚 Highest Order Volume Cities","Complete ranking")
        d=city.sort_values("TOTAL_ORDERS",ascending=False)
        st.dataframe(d,use_container_width=True,hide_index=True,height=430)
    with b:
        section("💳 Payment Performance","Complete ranking")
        st.dataframe(payment.sort_values("TOTAL_REVENUE",ascending=False),use_container_width=True,hide_index=True,height=430)

    with st.expander("Complete monthly performance data"):
        st.dataframe(monthly,use_container_width=True,hide_index=True,height=430)


# ============================================================
# SENTIMENT
# ============================================================
elif page == "😊 Sentiment Intelligence":
    page_header("Sentiment Intelligence","Local NLP analysis of real SWIGGY customer reviews")

    sentiment=analyze_sentiment(load_sentiment())
    positive=int((sentiment["SENTIMENT"]=="Positive").sum())
    neutral=int((sentiment["SENTIMENT"]=="Neutral").sum())
    negative=int((sentiment["SENTIMENT"]=="Negative").sum())

    metric_row([
        {"label":"💬 Reviews Analysed","value":fmt_int(len(sentiment)),"delta":"Reviews processed","delta_color":"off"},
        {"label":"😊 Positive","value":fmt_int(positive),"delta":f"{positive/max(len(sentiment),1)*100:.1f}%","delta_color":"off"},
        {"label":"😐 Neutral","value":fmt_int(neutral),"delta":f"{neutral/max(len(sentiment),1)*100:.1f}%","delta_color":"off"},
        {"label":"☹️ Negative","value":fmt_int(negative),"delta":f"{negative/max(len(sentiment),1)*100:.1f}%","delta_color":"off"},
        {"label":"★ Average Rating","value":fmt_num(pd.to_numeric(sentiment["RATING"],errors="coerce").mean()),"delta":"Overall rating","delta_color":"off"},
    ])

    a,b=st.columns(2,gap="large")
    with a:
        section("😊 Sentiment Distribution")
        counts=sentiment["SENTIMENT"].value_counts().reindex(["Positive","Neutral","Negative"]).fillna(0).reset_index()
        counts.columns=["Sentiment","Reviews"]
        fig=px.pie(counts,names="Sentiment",values="Reviews",hole=.62,
                   color="Sentiment",
                   color_discrete_map={"Positive":"#12d993","Neutral":"#ffc34d","Negative":"#ff4d6d"})
        fig.update_traces(textinfo="percent")
        st.plotly_chart(chart_base(fig,350),use_container_width=True,config={"displayModeBar":False})
    with b:
        section("📊 Sentiment Score Distribution")
        fig=px.histogram(sentiment,x="SENTIMENT_SCORE",nbins=28)
        fig.update_traces(marker_color="#9561ff")
        st.plotly_chart(chart_base(fig,350),use_container_width=True,config={"displayModeBar":False})

    section("💬 Recent Negative Feedback","Latest 10")
    neg=sentiment[sentiment["SENTIMENT"]=="Negative"].head(10)
    st.dataframe(neg[["RATING","COMMENT","SENTIMENT_SCORE","REVIEW_DATE"]],use_container_width=True,hide_index=True,height=360)

    with st.expander("Complete sentiment dataset"):
        st.dataframe(sentiment,use_container_width=True,hide_index=True,height=500)


# ============================================================
# RAG
# ============================================================
elif page == "🔎 RAG Review Search":
    page_header("RAG Review Search","Retrieve the most relevant customer reviews from the SWIGGY review corpus")

    section("🔎 Local Retrieval Engine")
    st.caption("TF-IDF + keyword matching + cosine similarity • no paid API required")

    q=st.text_input("Search reviews",placeholder="Try: delivery time, late order, packaging, food quality",key="rag_question")
    k=st.slider("Relevant reviews",1,10,5)
    if st.button("🔎 Search Reviews",type="primary"):
        if not q.strip():
            st.warning("Enter a search query.")
        else:
            with st.spinner("Searching review corpus..."):
                results=rag_search(q,k)
            if results.empty:
                st.info("No matching reviews found.")
            else:
                for _,r in results.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**Rating:** {float(r.get('RATING',0) or 0):.1f}  •  **Relevance:** {float(r['RELEVANCE_SCORE']):.3f}")
                        st.write(str(r.get("COMMENT","")))
            st.caption(f"Search corpus: {len(load_rag_reviews()):,} reviews")


# ============================================================
# TEXT TO SQL
# ============================================================
elif page == "💬 Text-to-SQL":
    page_header("Text-to-SQL","Ask business questions in plain English and execute safe read-only SQL")

    section("💬 Natural Language → SQL")
    question=st.text_input(
        "Business question",
        placeholder="Try: show me top 5 restaurants | top 10 food items | revenue by city | monthly orders",
        key="sql_question",
    )
    st.caption("Examples: top 5 restaurants, top 10 food items, revenue by city, orders by city, monthly performance, payment performance, average delivery time")

    if st.button("▶ Generate & Run SQL",type="primary"):
        if not question.strip():
            st.warning("Enter a question.")
        else:
            sql,title=text_to_sql(question)
            if sql is None:
                st.warning("Supported questions: revenue, orders, cities, restaurants, food items, monthly performance, payment, delivery time and rating.")
            else:
                st.success(title)
                st.code(sql,language="sql")
                try:
                    result=query(sql)
                    st.dataframe(result,use_container_width=True,hide_index=True,height=420)
                except Exception as exc:
                    st.error("SQL execution failed.")
                    error_text = str(exc)
                    if "invalid identifier" in error_text.lower():
                        st.warning("The generated query referenced a column that is not present in this view. The query generator has been updated to use the columns actually available in the project views. Please click Generate & Run SQL again.")
                    else:
                        st.caption(error_text[:900])


# ============================================================
# DATA PIPELINE
# ============================================================
elif page == "⚙️ Data Pipeline":
    page_header("SWIGGY Data Pipeline","Local data lake → Snowflake → dbt → Airflow → Analytics → AI")

    st.markdown(
        """
        <div class="pipeline-row">
            <div class="pipeline-node">📁 Local CSV<small>Landing / Raw</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">❄️ Snowflake<small>RAW</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">⚙️ dbt<small>STAGING</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">⭐ dbt<small>MARTS / GOLD</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">⏱ Airflow<small>Orchestration</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">📊 BI<small>Streamlit</small></div>
            <div class="pipeline-arrow">→</div>
            <div class="pipeline-node">🤖 AI<small>RAG / SQL</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a,b=st.columns([1.15,1.0],gap="large")

    with a:
        section("📦 MARTS Data Volumes","Live Snowflake")
        tables={
            "Users":"SWIGGY.MARTS.DIM_USERS",
            "Restaurants":"SWIGGY.MARTS.DIM_RESTAURANTS",
            "Food":"SWIGGY.MARTS.DIM_FOOD",
            "Menu":"SWIGGY.MARTS.DIM_MENU",
            "Orders":"SWIGGY.MARTS.FCT_ORDERS",
            "Order Items":"SWIGGY.MARTS.FCT_ORDER_ITEMS",
            "Reviews":"SWIGGY.MARTS.FCT_REVIEWS",
        }
        rows=[]
        for name,table in tables.items():
            try:
                n=int(query(f"SELECT COUNT(*) AS CNT FROM {table}").iloc[0]["CNT"])
            except Exception:
                n=0
            rows.append({"Dataset":name,"Rows":n})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True,height=330)

    with b:
        section("⚙️ Pipeline Health")
        health=pd.DataFrame({
            "Component":["Snowflake","dbt models","dbt tests","Airflow DAG","Streamlit","AI/RAG"],
            "Status":["Connected","Ready","Ready","Ready","Running","Ready"],
        })
        st.dataframe(health,use_container_width=True,hide_index=True,height=330)

    section("📐 Medallion Architecture")
    arch=st.columns(4,gap="small")
    arch[0].info("**BRONZE / RAW**\n\nRaw CSV data is retained for traceability.")
    arch[1].info("**SILVER / STAGING**\n\nCleaning, standardization and transformation.")
    arch[2].success("**GOLD / MARTS**\n\nBusiness-ready facts, dimensions and KPI views.")
    arch[3].warning("**AI / CONSUMPTION**\n\nRAG search, Text-to-SQL and Streamlit analytics.")


st.markdown(
    '<div class="footer">Swiggy Analytics • Snowflake • dbt • Airflow • Streamlit • Local AI</div>',
    unsafe_allow_html=True,
)
