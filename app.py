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

if "draft_input" not in st.session_state:
    st.session_state.draft_input = ""

# =====================================================
# UI HEADER
# =====================================================
st.title("Business Pulse")
st.subheader("Paste financial reports and get business insights")

# =====================================================
# INPUT SECTION
# =====================================================
report_type = st.selectbox(
    "Report type (optional)",
    ["Auto Detect", "Profit & Loss", "Balance Sheet", "CSV"]
)

st.session_state.draft_input = st.text_area(
    "Paste financial report",
    value=st.session_state.draft_input,
    height=200
)

uploaded_file = st.file_uploader("Or upload CSV", type=["csv"])

col1, col2 = st.columns(2)

with col1:
    add_btn = st.button("Add Report")

with col2:
    run_btn = st.button("Generate Business Snapshot")

# =====================================================
# PARSER
# =====================================================
def extract_numbers(text):
    """
    Robust line-based financial parser for real P&Ls.
    """
    if not text:
        return {}

    out = {}

    lines = text.split("\n")

    def clean(val):
        try:
            return float(val.replace("$", "").replace(",", "").strip())
        except:
            return None

    for line in lines:
        line = line.lower().strip()

        # skip empty lines
        if not line:
            continue

        # normalize separators
        line = line.replace(":", " ")

        parts = line.split()

        if len(parts) < 2:
            continue

        # try last token as number
        value = clean(parts[-1])
        if value is None:
            continue

        # match categories by keywords
        if "revenue" in line:
            out["revenue"] = value

        elif "sales" in line:
            out["revenue"] = value

        elif "expenses" in line:
            out["expenses"] = value

        elif "operating expense" in line:
            out["expenses"] = value

        elif "net income" in line:
            out["net_income"] = value

        elif "profit" in line:
            out["net_income"] = value

        elif "cash" in line:
            out["cash"] = value

        elif "liabilit" in line:
            out["liabilities"] = value

        elif "assets" in line:
            out["assets"] = value

        elif "equity" in line:
            out["equity"] = value

        elif "accounts receivable" in line:
            out["ar"] = value

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
    return "pl"

# =====================================================
# ADD REPORT (FIXED STATE HANDLING)
# =====================================================
if add_btn:

    text = st.session_state.draft_input

    if not text.strip() and not uploaded_file:
        st.warning("No report detected")
        st.stop()

    if uploaded_file:
        parsed = parse_csv(uploaded_file)
        report_kind = "csv"
        raw_text = ""
    else:
        parsed = extract_numbers(text)
        report_kind = detect_type(text)
        raw_text = text

    st.session_state.memory["reports"].append({
        "type": report_kind,
        "data": parsed,
        "raw": raw_text,
        "time": datetime.now()
    })

    st.session_state.draft_input = ""

    st.success("Report added")

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

    latest = {k: v[-1] for k, v in model.items()}

    return model, latest

# =====================================================
# INSIGHT ENGINE
# =====================================================
def generate_insights(latest):

    insights = {}

    revenue = latest.get("revenue")
    expenses = latest.get("expenses")
    cash = latest.get("cash")
    liabilities = latest.get("liabilities")
    ar = latest.get("ar")

    # ---------------- PROFITABILITY ----------------
    if revenue and expenses:
        profit = revenue - expenses

        insights["profitability"] = {
            "summary": f"Revenue is ${revenue:,.0f} and expenses are ${expenses:,.0f}, resulting in about ${profit:,.0f} in profit.",
            "evidence": [
                f"Revenue: ${revenue:,.0f}",
                f"Expenses: ${expenses:,.0f}",
                f"Estimated Profit: ${profit:,.0f}"
            ]
        }

    # ---------------- CASH ----------------
    if cash or ar:
        insights["cash"] = {
            "summary": f"Cash is ${cash:,.0f} with ${ar:,.0f} in accounts receivable.",
            "evidence": [
                f"Cash: ${cash:,.0f}",
                f"Accounts Receivable: ${ar:,.0f}"
            ]
        }

    # ---------------- STABILITY ----------------
    if cash and liabilities:
        insights["stability"] = {
            "summary": f"Cash is ${cash:,.0f} compared to ${liabilities:,.0f} in liabilities.",
            "evidence": [
                f"Cash: ${cash:,.0f}",
                f"Liabilities: ${liabilities:,.0f}"
            ]
        }

    return insights

# =====================================================
# RUN SNAPSHOT
# =====================================================
if run_btn:

    if not st.session_state.memory["reports"]:
        st.warning("No reports added yet")
        st.stop()

    model, latest = build_model(st.session_state.memory["reports"])
    insights = generate_insights(latest)

    st.markdown("## Business Snapshot")

    for key, section in insights.items():
        st.markdown(f"### {key.capitalize()}")
        st.write(section["summary"])

        st.markdown("Evidence:")
        for e in section["evidence"]:
            st.write("- " + e)

    st.markdown("---")
    st.caption(f"Reports stored: {len(st.session_state.memory['reports'])}")
