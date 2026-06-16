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
# MEMORY
# =====================================================
if "reports" not in st.session_state:
    st.session_state.reports = []

if "draft" not in st.session_state:
    st.session_state.draft = ""

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

st.session_state.draft = st.text_area(
    "Paste financial report",
    value=st.session_state.draft,
    height=200
)

uploaded_file = st.file_uploader("Or upload CSV", type=["csv"])

add_btn = st.button("Add Report")
run_btn = st.button("Generate Snapshot")

st.write("DEBUG draft length:", len(st.session_state.draft))

# =====================================================
# PARSER (SAFE + SIMPLE)
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {}

    for line in text.split("\n"):
        line = line.lower()

        nums = re.findall(r"[\$]?\d[\d,]*\.?\d*", line)
        if not nums:
            continue

        try:
            value = float(nums[-1].replace("$", "").replace(",", ""))
        except:
            continue

        if "revenue" in line or "sales" in line:
            out["revenue"] = value
        elif "expense" in line:
            out["expenses"] = value
        elif "profit" in line:
            out["net_income"] = value
        elif "cash" in line:
            out["cash"] = value
        elif "liabil" in line:
            out["liabilities"] = value
        elif "assets" in line:
            out["assets"] = value
        elif "ar" in line or "receivable" in line:
            out["ar"] = value

    return out

# =====================================================
# ADD REPORT (DEBUG HEAVY)
# =====================================================
if add_btn:

    st.write("BUTTON PRESSED")

    text = st.session_state.draft

    st.write("INPUT RECEIVED:")
    st.write(text)

    if not text.strip():
        st.warning("EMPTY INPUT")
        st.stop()

    parsed = extract_numbers(text)

    st.write("PARSED OUTPUT:")
    st.write(parsed)

    st.session_state.reports.append(parsed)

    st.write("REPORTS STORED:")
    st.write(st.session_state.reports)

    st.session_state.draft = ""

    st.success("ADDED")

    st.rerun()

# =====================================================
# SNAPSHOT
# =====================================================
if run_btn:

    st.write("RUN SNAPSHOT PRESSED")

    if not st.session_state.reports:
        st.warning("NO REPORTS")
        st.stop()

    latest = st.session_state.reports[-1]

    st.markdown("## Business Snapshot")

    revenue = latest.get("revenue")
    expenses = latest.get("expenses")

    if revenue and expenses:
        profit = revenue - expenses

        st.write("Revenue:", revenue)
        st.write("Expenses:", expenses)
        st.write("Profit:", profit)

    st.write("RAW MEMORY:")
    st.write(st.session_state.reports)
