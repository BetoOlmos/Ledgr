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
# STYLE
# =====================================================
st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}
html, body, p, span, div {
    color: #FAFAFA !important;
}
.block-container {
    padding-top: 2rem;
}
.title {
    font-size: 42px;
    font-weight: 700;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #9CA3AF;
    margin-bottom: 2rem;
}
.box {
    background-color: #161B22;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("<div class='title'>Business Pulse</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Build your business story from financial reports</div>", unsafe_allow_html=True)

# =====================================================
# SESSION STATE (CORE MEMORY)
# =====================================================
if "memory" not in st.session_state:
    st.session_state.memory = {
        "pl_reports": [],
        "bs_reports": [],
        "csv_reports": []
    }

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# =====================================================
# PARSER
# =====================================================

def clean_number(value):
    try:
        value = str(value).replace(",", "").replace("$", "").strip()
        return float(value)
    except:
        return None


def parse_text(text):
    """
    Extracts key financial signals from messy text.
    """
    if not text:
        return {}

    text = text.lower()

    patterns = {
        "revenue": r"(revenue|sales|income)[^\d]*([\d,\.]+)",
        "expenses": r"(expenses|expense|opex)[^\d]*([\d,\.]+)",
        "cogs": r"(cogs)[^\d]*([\d,\.]+)",
        "net_income": r"(net income|net profit|profit)[^\d]*([\d,\.]+)",
        "cash": r"(cash)[^\d]*([\d,\.]+)",
        "assets": r"(assets)[^\d]*([\d,\.]+)",
        "liabilities": r"(liabilities|debt)[^\d]*([\d,\.]+)",
        "equity": r"(equity)[^\d]*([\d,\.]+)",
    }

    out = {}

    for k, p in patterns.items():
        m = re.search(p, text)
        if m:
            out[k] = clean_number(m.group(2))

    return out


# =====================================================
# MODEL BUILDER (ACCUMULATED MEMORY)
# =====================================================

def build_model(memory):
    model = {}

    all_reports = (
        memory["pl_reports"] +
        memory["bs_reports"] +
        memory["csv_reports"]
    )

    # Merge all extracted signals
    for r in all_reports:
        model.update(r)

    return model


# =====================================================
# INSIGHT ENGINE
# =====================================================

def generate_insights(model):
    insights = {}

    revenue = model.get("revenue")
    expenses = model.get("expenses")

    if revenue is not None and expenses is not None:
        profit = revenue - expenses
        insights["profit"] = profit
        insights["making_money"] = profit > 0
        insights["expense_ratio"] = expenses / revenue if revenue else 0

    cash = model.get("cash")
    liabilities = model.get("liabilities")

    if cash is not None and liabilities is not None:
        insights["healthy"] = cash > liabilities

    return insights


# =====================================================
# UI HEADER
# =====================================================
st.markdown("## Input Financial Report")

col1, col2 = st.columns([3, 1])

with col1:
    report_type = st.selectbox(
        "Report type",
        ["Profit & Loss", "Balance Sheet"]
    )

    user_input = st.text_area(
        "Paste financial data",
        height=180,
        key="input_text"
    )

with col2:
    st.write("")
    st.write("")

    add = st.button("➕ Add Report")
    run = st.button("🚀 Generate Pulse")


# =====================================================
# ADD REPORT LOGIC (ACCUMULATION + CLEAR INPUT)
# =====================================================

if add and user_input.strip():

    parsed = parse_text(user_input)

    if report_type == "Profit & Loss":
        st.session_state.memory["pl_reports"].append(parsed)
        st.success("P&L added to business memory")

    else:
        st.session_state.memory["bs_reports"].append(parsed)
        st.success("Balance Sheet added to business memory")

    # CLEAR INPUT (UX requirement)
    st.session_state.input_text = ""
    st.rerun()


# =====================================================
# RENDER BUSINESS PULSE
# =====================================================

if run:

    model = build_model(st.session_state.memory)
    insights = generate_insights(model)

    st.markdown("## Business Pulse")

    st.markdown("### 💰 Am I Making Money?")
    if insights.get("making_money") is True:
        st.success(f"Yes — profit is ${insights['profit']:,.0f}")
    elif insights.get("making_money") is False:
        st.error(f"No — loss of ${abs(insights['profit']):,.0f}")
    else:
        st.info("Not enough data yet.")

    st.markdown("### 💸 Where Is My Money Going?")
    if "expense_ratio" in insights:
        st.write(f"Expenses are {insights['expense_ratio']:.0%} of revenue")

    st.markdown("### 🏦 Is My Business Healthy?")
    if "healthy" in insights:
        if insights["healthy"]:
            st.success("Cash is stronger than liabilities")
        else:
            st.warning("Liabilities exceed cash")

    st.markdown("### 📊 Memory Status")
    st.write(f"P&L reports: {len(st.session_state.memory['pl_reports'])}")
    st.write(f"Balance sheets: {len(st.session_state.memory['bs_reports'])}")
