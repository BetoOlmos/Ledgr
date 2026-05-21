import streamlit as st
import pandas as pd
import sqlite3
import datetime

# =====================================================
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# =====================================================
st.set_page_config(
    page_title="Ledgr",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# WHITE BACKGROUND OVERRIDE (ROBUST STREAMLIT FIX)
# =====================================================
st.markdown("""
<style>

/* ================= MAIN APP ================= */
.stApp {
    background-color: #ffffff !important;
    color: #000000;
}

/* Streamlit main container */
div[data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;
}

/* Main content area */
section.main {
    background-color: #ffffff !important;
}

/* Block container */
.block-container {
    padding: 2rem 3rem;
    color: #000000;
}

/* ================= FULL PAGE FALLBACK ================= */
html, body, [class*="css"] {
    background-color: #ffffff !important;
    color: #000000;
}

/* ================= TEXT ================= */
h1, h2, h3, h4, h5, h6,
p, div, span, label {
    color: #000000 !important;
}

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"] {
    background-color: #f5f5f5 !important;
    border-right: 1px solid #e0e0e0;
}

div[data-testid="stSidebar"] {
    background-color: #f5f5f5 !important;
}

/* ================= METRICS ================= */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 14px;
    padding: 18px;
}

/* ================= BUTTONS ================= */
.stButton > button {
    background-color: #000000;
    color: #ffffff;
    border-radius: 10px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #333333;
    color: #ffffff;
}

/* ================= DATAFRAME ================= */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

/* ================= INPUT FIELDS ================= */
input, textarea {
    color: #000000 !important;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE
# =====================================================
conn = sqlite3.connect("ledgr_core.db", check_same_thread=False)
cursor = conn.cursor()

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

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Ledgr")
st.sidebar.caption("Financial clarity without complexity")

user_id = st.sidebar.text_input(
    "Business ID",
    "demo_business"
).strip().lower()

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
    st.session_state.user_mode = None

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
        df["date"] = pd.to_datetime(df["date"])

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
    st.caption(
        "Understand your business in seconds — not spreadsheets."
    )

    st.divider()

    st.subheader("How will you use Ledgr?")

    choice = st.radio(
        "Choose one:",
        [
            "Track my business (bookkeeping)",
            "Analyze existing financials (QuickBooks / Xero / CSV)"
        ]
    )

    if st.button("Continue"):

        st.session_state.user_mode = choice
        st.session_state.onboarded = True

        st.rerun()

# =====================================================
# DASHBOARD
# =====================================================
elif page == "Dashboard":

    st.title("Ledgr")

    if "Analyze" in st.session_state.user_mode:
        st.info(
            "Analysis Mode — importing existing financial data."
        )
    else:
        st.info(
            "Tracking Mode — building financial history."
        )

    st.divider()

    st.success("Your Business Pulse is ready.")
    st.caption(
        "Updated automatically as you add financial data."
    )

    income, expenses, net = calc(df)

    # HEALTH STATUS
    if net > 1000:
        health = "🟢 Healthy"
        message = "Strong profitability."

    elif net > 0:
        health = "🟡 Stable"
        message = "Profitable but tight margins."

    else:
        health = "🔴 Risk"
        message = "Expenses exceed income."

    # TOP EXPENSE
    top_expense = "No data"

    if not df.empty:

        exp = df[df["type"] == "Expense"]

        if not exp.empty:

            top = (
                exp.groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )

            top_expense = (
                f"{top.index[0]} "
                f"(${top.iloc[0]:,.2f})"
            )

    # =================================================
    # BUSINESS PULSE
    # =================================================
    st.subheader("Business Pulse")

    c1, c2, c3 = st.columns(3)

    c1.metric("Income", f"${income:,.2f}")
    c2.metric("Expenses", f"${expenses:,.2f}")
    c3.metric("Net Profit", f"${net:,.2f}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Business Health")
        st.write(health)
        st.write(message)

    with col2:

        st.markdown("### Key Focus")
        st.write(f"Top expense: {top_expense}")

    st.divider()

    if net > 0:
        st.success(
            "Your business is currently profitable."
        )
    else:
        st.error(
            "Your business is currently losing money."
        )

# =====================================================
# ADD DATA
# =====================================================
elif page == "Add Data":

    st.title("Add Data")

    mode = st.radio(
        "Mode",
        ["Manual Entry", "CSV Upload"]
    )

    # =================================================
    # MANUAL ENTRY
    # =================================================
    if mode == "Manual Entry":

        with st.form("transaction_form"):

            date = st.date_input(
                "Date",
                datetime.date.today()
            )

            category = st.text_input("Category")

            amount = st.number_input(
                "Amount",
                value=0.0
            )

            ttype = st.selectbox(
                "Type",
                ["Income", "Expense"]
            )

            vendor = st.text_input("Vendor")

            account = st.text_input("Account")

            submit = st.form_submit_button("Save")

            if submit:

                cursor.execute("""
                    INSERT INTO transactions
                    (
                        user_id,
                        date,
                        category,
                        amount,
                        type,
                        vendor,
                        account,
                        source
                    )
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

                st.success("Transaction saved.")

    # =================================================
    # CSV UPLOAD
    # =================================================
    else:

        file = st.file_uploader(
            "Upload CSV",
            type=["csv"]
        )

        if file:

            csv = pd.read_csv(file)

            csv.columns = (
                csv.columns
                .str.lower()
                .str.strip()
            )

            def find(possible_names):

                for c in csv.columns:
                    if c in possible_names:
                        return c

                return None

            date_col = find(["date"])
            amount_col = find(["amount", "value", "total"])
            type_col = find(["type"])
            category_col = find(
                ["category", "description"]
            )

            if not date_col or not amount_col:

                st.error(
                    "CSV must contain date and amount columns."
                )

                st.stop()

            for _, row in csv.iterrows():

                cursor.execute("""
                    INSERT INTO transactions
                    (
                        user_id,
                        date,
                        category,
                        amount,
                        type,
                        vendor,
                        account,
                        source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    str(row[date_col]),
                    row[category_col]
                    if category_col
                    else "Uncategorized",
                    float(row[amount_col]),
                    row[type_col]
                    if type_col
                    else "Expense",
                    "",
                    "",
                    "csv"
                ))

            conn.commit()

            st.session_state.df = load_data(user_id)

            st.success("CSV uploaded successfully.")

# =====================================================
# TRANSACTIONS
# =====================================================
else:

    st.title("Transactions")

    if df.empty:

        st.info("No transactions yet.")

    else:

        st.dataframe(
            df.sort_values(
                "date",
                ascending=False
            ),
            use_container_width=True
        )
# ========================================
st.markdown("""
<style>

.stApp {
    background-color: #f5f5f5;
    color: #111111;
}

.block-container {
    padding: 2rem 3rem;
}

html, body, [class*="css"] {
    color: #111111;
}

h1, h2, h3, h4, h5, h6,
p, div, span, label {
    color: #111111 !important;
    font-weight: 500;
}

[data-testid="metric-container"] {
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 18px;
    padding: 18px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #eaeaea;
}

.stButton > button {
    background-color: #111111;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.5rem 1rem;
}

.stButton > button:hover {
    background-color: #222222;
    color: white;
}

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)
