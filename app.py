import streamlit as st
import pandas as pd
import sqlite3
import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Ledgr",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CLEAN DARK THEME (FIXED PROPERLY WRAPPED CSS)
# =====================================================
st.markdown("""
<style>

/* Main app background */
.stApp {
    background-color: #0E1117 !important;
    color: #FAFAFA !important;
}

/* App container */
[data-testid="stAppViewContainer"] {
    background-color: #0E1117 !important;
}

/* Header */
[data-testid="stHeader"] {
    background: #0E1117 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161B22 !important;
}

/* Global text */
html, body, p, span, div, label {
    color: #FAFAFA !important;
}

/* Inputs */
input, textarea, select {
    background-color: #1E242D !important;
    color: #FAFAFA !important;
    border-radius: 8px;
}

/* Buttons */
.stButton > button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 10px;
    border: 1px solid rgba(0,0,0,0.08);
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease-in-out;
}

/* IMPORTANT: fixes button text */
.stButton > button p {
    color: #000000 !important;
}

/* Hover */
.stButton > button:hover {
    background-color: #F2F2F2 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}

/* Metrics */
[data-testid="metric-container"] {
    background-color: #161B22 !important;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 18px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

/* Divider */
hr {
    border-color: rgba(255,255,255,0.08) !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================
conn = sqlite3.connect("ledgr_core.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        date TEXT,
        category TEXT,
        amount REAL,
        type TEXT,
        vendor TEXT,
        account TEXT,
        source TEXT
    )
    """)
    conn.commit()

init_db()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Ledgr")

user_id = st.sidebar.text_input("Business ID", "demo_business").strip().lower()

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Data", "Transactions"]
)

# =====================================================
# SESSION STATE
# =====================================================
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "user_mode" not in st.session_state:
    st.session_state.user_mode = "Track"

# =====================================================
# LOAD DATA
# =====================================================
def load_data(user):
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id = ?",
        conn,
        params=(user,)
    )

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df

if "df" not in st.session_state or st.session_state.get("user") != user_id:
    st.session_state.df = load_data(user_id)
    st.session_state.user = user_id

df = st.session_state.df

# =====================================================
# FINANCIAL ENGINE
# =====================================================
def calc(df):
    if df.empty:
        return 0, 0, 0

    income = df[df["type"] == "Income"]["amount"].sum()
    expenses = df[df["type"] == "Expense"]["amount"].sum()
    net = income - expenses

    return income, expenses, net

# =====================================================
# ONBOARDING
# =====================================================
if not st.session_state.onboarded:

    st.title("Welcome to Ledgr")

    choice = st.radio(
        "How will you use Ledgr?",
        ["Track my business", "Analyze existing data"]
    )

    if st.button("Continue"):
        st.session_state.user_mode = choice
        st.session_state.onboarded = True
        st.rerun()

# =====================================================
# DASHBOARD
# =====================================================
elif page == "Dashboard":

    st.title("Dashboard")

    income, expenses, net = calc(df)

    col1, col2, col3 = st.columns(3)

    col1.metric("Income", f"${income:,.2f}")
    col2.metric("Expenses", f"${expenses:,.2f}")
    col3.metric("Net Profit", f"${net:,.2f}")

    st.divider()

    if net > 0:
        st.success("Your business is profitable")
    else:
        st.error("Your business is running at a loss")

# =====================================================
# ADD DATA
# =====================================================
elif page == "Add Data":

    st.title("Add Transaction")

    with st.form("form"):

        date = st.date_input("Date", datetime.date.today())
        category = st.text_input("Category")
        amount = st.number_input("Amount", value=0.0)
        ttype = st.selectbox("Type", ["Income", "Expense"])
        vendor = st.text_input("Vendor")
        account = st.text_input("Account")

        submit = st.form_submit_button("Save")

        if submit:

            cursor.execute("""
                INSERT INTO transactions
                (user_id, date, category, amount, type, vendor, account, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                str(date),
                category,
                amount,
                ttype,
                vendor,
                account,
                "manual"
            ))

            conn.commit()
            st.session_state.df = load_data(user_id)

            st.success("Transaction saved!")

# =====================================================
# TRANSACTIONS
# =====================================================
else:

    st.title("Transactions")

    if df.empty:
        st.info("No transactions yet.")
    else:
        st.dataframe(
            df.sort_values("date", ascending=False),
            use_container_width=True
        )
