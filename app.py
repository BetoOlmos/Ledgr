import streamlit as st
import pandas as pd
import re
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Business Pulse",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# SESSION MEMORY
# =====================================================
if "memory" not in st.session_state:
    st.session_state.memory = {
        "reports": []
    }

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# =====================================================
# UI HEADER
# =====================================================
st.title("Business Pulse")
st.subheader("Paste financial reports → Get instant business understanding")

# =====================================================
# INPUT SECTION
# =====================================================
report_type = st.selectbox(
    "Select report type (optional - system can auto-detect)",
    ["Auto Detect", "Profit & Loss", "Balance Sheet", "CSV"]
)

user_input = st.text_area(
    "Paste your financial report here",
    height=200,
    key="input_text"
)

uploaded_file = st.file_uploader("Or upload CSV", type=["csv"])

col1, col2 = st.columns(2)

with col1:
    add_btn = st.button("➕ Add Report")

with col2:
    run_btn = st.button("🚀 Generate Business Snapshot")

# =====================================================
# HELPERS
# =====================================================
def clean_number(value):
    try:
        value = str(value).replace(",", "").replace("$", "").strip()
        return float(value)
    except:
        return None


def extract_numbers(text):
    """
    More realistic financial parser for CPA-style P&Ls.
    """
    if not text:
        return {}

    text = text.lower()

    patterns = {
        "revenue": r"(total revenue|revenue|sales|income)[^\d]*[\$]?([\d,\,\.]+)",
        "expenses": r"(total expenses|operating expenses|expenses|expense)[^\d]*[\$]?([\d,\,\.]+)",
        "net_income": r"(net income|net profit|net loss|profit)[^\d]*[\$]?([\d,\,\.]+)",
        "cash": r"(cash)[^\d]*[\$]?([\d,\,\.]+)",
        "assets": r"(total assets|assets)[^\d]*[\$]?([\d,\,\.]+)",
        "liabilities": r"(total liabilities|liabilities|debt)[^\d]*[\$]?([\d,\,\.]+)",
        "equity": r"(equity|retained earnings)[^\d]*[\$]?([\d,\,\.]+)"
    }

    out = {}

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text)

        if matches:
            # take LAST match (usually totals are at bottom of P&L)
            value = matches[-1][-1] if isinstance(matches[-1], tuple) else matches[-1]
            try:
                out[key] = float(value.replace(",", ""))
            except:
                pass

    return out


def parse_csv(file):
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.lower()

        row = {}
        for col in df.columns:
            if "revenue" in col:
                row["revenue"] = df[col].sum()
            if "expense" in col:
                row["expenses"] = df[col].sum()
            if "profit" in col:
                row["net_income"] = df[col].sum()
        return row
    except:
        return {}


def detect_type(text):
    text = text.lower()
    if "balance" in text:
        return "bs"
    if "cash" in text or "liabil" in text:
        return "bs"
    return "pl"


# =====================================================
# ADD REPORT
# =====================================================
if add_btn and (user_input.strip() or uploaded_file):

    if uploaded_file:
        parsed = parse_csv(uploaded_file)
        report_kind = "csv"
    else:
        parsed = extract_numbers(user_input)
        report_kind = detect_type(user_input)

    st.session_state.memory["reports"].append({
        "type": report_kind,
        "data": parsed,
        "raw": user_input,
        "time": datetime.now()
    })

    st.session_state.input_text = ""
    st.success("Report added to Business Pulse")

    st.rerun()

# =====================================================
# BUILD MODEL
# =====================================================
def build_model(reports):
    model = {}

    for r in reports:
        for k, v in r["data"].items():
            if v is None:
                continue

            if k not in model:
                model[k] = []

            model[k].append(v)

    # latest values
    latest = {}
    for k, values in model.items():
        latest[k] = values[-1]

    return model, latest


# =====================================================
# INSIGHT ENGINE
# =====================================================
def generate_insights(model, latest):
    insights = {}

    revenue = latest.get("revenue")
    expenses = latest.get("expenses")
    profit = latest.get("net_income")

    ar = latest.get("ar")
    cash = latest.get("cash")
    liabilities = latest.get("liabilities")

    evidence = []

    # -----------------------------
    # PROFITABILITY
    # -----------------------------
    if revenue and expenses:
        profit_calc = revenue - expenses

        insights["profitability"] = {
            "summary": f"Revenue is ${revenue:,.0f} and expenses are ${expenses:,.0f}, resulting in approximately ${profit_calc:,.0f} in operating profit.",
            "why": "Profit is driven by the gap between revenue and expenses.",
            "meaning": "Wider gap = stronger profitability.",
            "evidence": [
                f"Revenue: ${revenue:,.0f}",
                f"Expenses: ${expenses:,.0f}",
                f"Estimated Profit: ${profit_calc:,.0f}"
            ]
        }

    # -----------------------------
    # CASH / AR
    # -----------------------------
    if cash or ar:
        insights["cash"] = {
            "summary": f"Cash position is ${cash:,.0f} with ${ar:,.0f} tied up in receivables.",
            "why": "Cash is affected by timing of collections.",
            "meaning": "High receivables can create cash pressure even when profitable.",
            "evidence": [
                f"Cash: ${cash:,.0f}",
                f"Accounts Receivable: ${ar:,.0f}"
            ]
        }

    # -----------------------------
    # STABILITY
    # -----------------------------
    if liabilities and cash:
        insights["stability"] = {
            "summary": f"Liabilities are ${liabilities:,.0f} compared to ${cash:,.0f} cash on hand.",
            "why": "Debt levels impact financial flexibility.",
            "meaning": "Higher liabilities reduce short-term stability.",
            "evidence": [
                f"Liabilities: ${liabilities:,.0f}",
                f"Cash: ${cash:,.0f}"
            ]
        }

    return insights


# =====================================================
# RUN SNAPSHOT
# =====================================================
if run_btn:

    if not st.session_state.memory["reports"]:
        st.warning("No reports added yet.")
        st.stop()

    model, latest = build_model(st.session_state.memory["reports"])
    insights = generate_insights(model, latest)

    # =================================================
    # BUSINESS SNAPSHOT
    # =================================================
    st.markdown("## 👀 Business Snapshot")

    if "profitability" in insights:
        st.markdown("### 💰 Profitability")
        st.write(insights["profitability"]["summary"])
        st.markdown("**Why:** " + insights["profitability"]["why"])
        st.markdown("**Meaning:** " + insights["profitability"]["meaning"])

        st.markdown("**Evidence:**")
        for e in insights["profitability"]["evidence"]:
            st.write("- " + e)

    if "cash" in insights:
        st.markdown("### 🏦 Cash Position")
        st.write(insights["cash"]["summary"])
        st.markdown("**Why:** " + insights["cash"]["why"])
        st.markdown("**Meaning:** " + insights["cash"]["meaning"])

        st.markdown("**Evidence:**")
        for e in insights["cash"]["evidence"]:
            st.write("- " + e)

    if "stability" in insights:
        st.markdown("### ⚖️ Financial Stability")
        st.write(insights["stability"]["summary"])
        st.markdown("**Why:** " + insights["stability"]["why"])
        st.markdown("**Meaning:** " + insights["stability"]["meaning"])

        st.markdown("**Evidence:**")
        for e in insights["stability"]["evidence"]:
            st.write("- " + e)

    # =================================================
    # MEMORY DEBUG (MINIMAL, TEMPORARY)
    # =================================================
    st.markdown("---")
    st.caption(f"Reports stored: {len(st.session_state.memory['reports'])}")
