import streamlit as st
import pandas as pd
import re
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Business Pulse", layout="wide")

# =====================================================
# MEMORY
# =====================================================
if "reports" not in st.session_state:
    st.session_state.reports = []

# =====================================================
# FORMAT
# =====================================================
def fmt(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}"

# =====================================================
# PARSER (TEXT)
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {}

    for line in text.split("\n"):
        l = line.lower()

        nums = re.findall(r"[\$]?\d[\d,]*\.?\d*", l)
        if not nums:
            continue

        try:
            val = float(nums[-1].replace("$", "").replace(",", ""))
        except:
            continue

        if "revenue" in l or "sales" in l or "income" in l:
            out["revenue"] = val
        elif "expense" in l:
            out["expenses"] = val
        elif "profit" in l:
            out["net_income"] = val
        elif "cash" in l:
            out["cash"] = val
        elif "liabil" in l:
            out["liabilities"] = val
        elif "asset" in l:
            out["assets"] = val
        elif "receivable" in l or "ar" in l:
            out["ar"] = val

    return out

# =====================================================
# PARSER (CSV - SIMPLE BUT REAL)
# =====================================================
def parse_csv(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower()

    out = {}

    for col in df.columns:
        c = col.lower()

        if "revenue" in c or "sales" in c:
            out["revenue"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "expense" in c:
            out["expenses"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "profit" in c:
            out["net_income"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "cash" in c:
            out["cash"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "liabil" in c:
            out["liabilities"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "asset" in c:
            out["assets"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "receivable" in c or "ar" in c:
            out["ar"] = pd.to_numeric(df[col], errors="coerce").sum()

    return out

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")
st.write("Upload or paste financial data → understand your business instantly")

text_input = st.text_area("Paste P&L or Balance Sheet", height=200)

csv_file = st.file_uploader("Or drag & drop CSV", type=["csv"])

col1, col2 = st.columns(2)

with col1:
    add_btn = st.button("Add Report")

with col2:
    run_btn = st.button("Generate Business Pulse")

# =====================================================
# ADD REPORT
# =====================================================
if add_btn:

    parsed = {}

    if csv_file:
        parsed = parse_csv(csv_file)

    elif text_input.strip():
        parsed = extract_numbers(text_input)

    if not parsed:
        st.warning("No financial data detected")
        st.stop()

    st.session_state.reports.append({
        "data": parsed,
        "time": datetime.now()
    })

    st.success("Report added")

# =====================================================
# MODEL (LATEST SNAPSHOT)
# =====================================================
def latest():
    if not st.session_state.reports:
        return {}
    return st.session_state.reports[-1]["data"]

# =====================================================
# INSIGHT ENGINE (YOUR ORIGINAL VISION RESTORED)
# =====================================================
def insights(d):

    r = d.get("revenue")
    e = d.get("expenses")
    c = d.get("cash")
    l = d.get("liabilities")
    ar = d.get("ar")

    out = {}

    # =========================
    # PROFITABILITY (WHAT + WHY + SO WHAT)
    # =========================
    if r and e:
        p = r - e

        out["Profitability"] = {
            "what": f"Revenue is {fmt(r)} and expenses are {fmt(e)}, leaving {fmt(p)} profit.",
            "why": "Profit is what remains after all costs are removed from revenue.",
            "so_what": "If expenses rise faster than revenue, profit will shrink even if sales look strong.",
            "evidence": [
                f"Revenue: {fmt(r)}",
                f"Expenses: {fmt(e)}",
                f"Profit: {fmt(p)}"
            ]
        }

    # =========================
    # CASH FLOW REALITY
    # =========================
    if c or ar:

        out["Cash Flow"] = {
            "what": f"Cash is {fmt(c)} with {fmt(ar)} tied in unpaid invoices.",
            "why": "Profit does not equal cash — unpaid invoices delay real money in the bank.",
            "so_what": "High receivables can create cash stress even in profitable businesses.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Accounts Receivable: {fmt(ar)}"
            ]
        }

    # =========================
    # FINANCIAL HEALTH
    # =========================
    if c and l:
        ratio = c / l if l else 0

        out["Financial Health"] = {
            "what": f"Cash of {fmt(c)} vs liabilities of {fmt(l)}.",
            "why": "This shows whether the business can cover short-term obligations.",
            "so_what": "Lower coverage means higher reliance on incoming cash flow to survive.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Liabilities: {fmt(l)}",
                f"Coverage Ratio: {ratio:.2f}"
            ]
        }

    return out

# =====================================================
# SNAPSHOT
# =====================================================
if run_btn:

    data = latest()

    if not data:
        st.warning("No reports yet")
        st.stop()

    result = insights(data)

    st.markdown("## Business Pulse")

    for k, v in result.items():
        st.subheader(k)

        st.write("WHAT")
        st.write(v["what"])

        st.write("WHY")
        st.write(v["why"])

        st.write("SO WHAT")
        st.write(v["so_what"])

        st.write("EVIDENCE")
        for e in v["evidence"]:
            st.write("- " + e)

    st.write("---")
    st.write(f"Reports stored: {len(st.session_state.reports)}")
