import streamlit as st
import pandas as pd
import sqlite3
import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Ledgr",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CLEAN DARK THEME
# =====================================================
st.markdown("""
<style>

.stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}

[data-testid="stSidebar"] {
    background-color: #161B22;
}

html, body, p, span, div, label {
    color: #FAFAFA !important;
}

.stButton > button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 10px;
    font-weight: 600;
}

.stButton > button p {
    color: #000000 !important;
}

[data-testid="metric-container"] {
    background-color: #161B22;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}

.hero-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
    text-align: center;
}

.hero-title {
    font-size: 72px;
    font-weight: 700;
    margin-bottom: 10px;
}

.hero-subtitle {
    font-size: 20px;
    color: #9CA3AF;
    margin-bottom: 40px;
}

.upload-box {
    width: 100%;
    max-width: 700px;
    margin: auto;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DB
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        event TEXT,
        timestamp TEXT,
        metadata TEXT
    )
    """)

    conn.commit()

init_db()

# =====================================================
# TRACKING
# =====================================================
def track_event(user_id, event, metadata=""):
    cursor.execute("""
        INSERT INTO user_events (user_id, event, timestamp, metadata)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        event,
        datetime.datetime.now().isoformat(),
        metadata
    ))
    conn.commit()

# =====================================================
# USER
# =====================================================
user_id = "demo_business"

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

df = load_data(user_id)

# =====================================================
# WELCOME SCREEN
# =====================================================
if df.empty:

    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Ledgr</div>
        <div class="hero-subtitle">
            Drop your business transactions and instantly understand your numbers.
        </div>
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader(
        "",
        type=["csv"],
        label_visibility="collapsed"
    )

    if file:

        csv = pd.read_csv(file)
        csv.columns = csv.columns.str.lower().str.strip()

        for _, row in csv.iterrows():

            cursor.execute("""
            INSERT INTO transactions (
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
                str(row.get("date", "")),
                row.get("category", "uncategorized"),
                float(row.get("amount", 0)),
                row.get("type", "Expense"),
                "",
                "",
                "csv"
            ))

        conn.commit()

        track_event(user_id, "upload_csv")

        st.success("Upload complete.")
        st.rerun()

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Ledgr")

page = st.sidebar.radio(
    "Navigation",
    [
        "Business Pulse",
        "Transactions",
        "Reports",
        "Feedback"
    ]
)

is_admin = False

# =====================================================
# CALCS
# =====================================================
def calc(df):
    if df.empty:
        return 0, 0, 0

    income = df[df["type"] == "Income"]["amount"].sum()
    expenses = df[df["type"] == "Expense"]["amount"].sum()

    return income, expenses, income - expenses

# =====================================================
# BUSINESS PULSE
# =====================================================
if page == "Business Pulse":

    st.title("Business Pulse")

    track_event(user_id, "view_dashboard")

    income, expenses, net = calc(df)

    c1, c2, c3 = st.columns(3)

    c1.metric("Income", f"${income:,.2f}")
    c2.metric("Expenses", f"${expenses:,.2f}")
    c3.metric("Net", f"${net:,.2f}")

    st.divider()

    st.subheader("Monthly View")

    if not df.empty:

        df["month"] = df["date"].dt.to_period("M")

        pnl = (
            df.groupby(["month", "type"])["amount"]
            .sum()
            .unstack()
            .fillna(0)
        )

        pnl["Net"] = (
            pnl.get("Income", 0)
            - pnl.get("Expense", 0)
        )

        st.dataframe(pnl, use_container_width=True)

# =====================================================
# TRANSACTIONS
# =====================================================
elif page == "Transactions":

    st.title("Transactions")

    track_event(user_id, "view_transactions")

    st.dataframe(
        df.sort_values("date", ascending=False),
        use_container_width=True
    )

    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        "ledgr_data.csv"
    )

# =====================================================
# REPORTS
# =====================================================
elif page == "Reports":

    st.title("Reports")

    track_event(user_id, "view_reports")

    df["month"] = df["date"].dt.to_period("M")

    st.subheader("Profit & Loss")

    pnl = (
        df.groupby(["month", "type"])["amount"]
        .sum()
        .unstack()
        .fillna(0)
    )

    pnl["Net"] = (
        pnl.get("Income", 0)
        - pnl.get("Expense", 0)
    )

    st.dataframe(pnl, use_container_width=True)

    st.subheader("Cash Flow")

    cash = df.groupby("date")["amount"].sum()

    st.line_chart(cash)

    st.subheader("Balance Sheet")

    st.info(
        "Assets, Liabilities, and Equity will be added in a future version."
    )

# =====================================================
# FEEDBACK
# =====================================================
elif page == "Feedback":

    st.title("What do you think?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍"):
            track_event(user_id, "feedback", "positive")
            st.success("Thanks!")

    with col2:
        if st.button("👎"):
            track_event(user_id, "feedback", "negative")
            st.warning("We'll improve!")

    comment = st.text_area("Optional feedback")

    if st.button("Submit feedback") and comment:

        track_event(
            user_id,
            "feedback_comment",
            comment
        )

        st.success("Saved!")
