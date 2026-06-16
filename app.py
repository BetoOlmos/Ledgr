import streamlit as st
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

if "input_key" not in st.session_state:
    st.session_state.input_key = 0

# =====================================================
# FORMAT
# =====================================================
def fmt(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}"

# =====================================================
# PARSER
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
# HEADER
# =====================================================
st.title("Business Pulse")
st.write("Paste financial reports → Get business understanding")

# =====================================================
# INPUT (FORCED RESET MECHANISM)
# =====================================================
text = st.text_area(
    "Paste financial report",
    key=f"input_{st.session_state.input_key}",
    height=200
)

col1, col2 = st.columns(2)

with col1:
    add_btn = st.button("Add Report")

with col2:
    run_btn = st.button("Generate Business Snapshot")

# =====================================================
# ADD REPORT (AUTO CLEAR INPUT)
# =====================================================
if add_btn:

    if not text.strip():
        st.warning("No input detected")
        st.stop()

    parsed = extract_numbers(text)

    st.session_state.reports.append({
        "raw": text,
        "data": parsed,
        "time": datetime.now()
    })

    # FORCE CLEAR INPUT
    st.session_state.input_key += 1

    st.success("Report added")
    st.rerun()

# =====================================================
# BUILD LATEST MODEL
# =====================================================
def latest_data():
    if not st.session_state.reports:
        return {}

    return st.session_state.reports[-1]["data"]

# =====================================================
# INSIGHTS ENGINE (UPGRADED)
# =====================================================
def insights(d):

    r = d.get("revenue")
    e = d.get("expenses")
    c = d.get("cash")
    l = d.get("liabilities")
    ar = d.get("ar")

    output = {}

    # PROFITABILITY
    if r and e:
        p = r - e
        output["Profitability"] = {
            "summary": f"Revenue is {fmt(r)} while expenses are {fmt(e)}, leaving about {fmt(p)} profit.",
            "evidence": [
                f"Revenue: {fmt(r)}",
                f"Expenses: {fmt(e)}",
                f"Profit: {fmt(p)}"
            ]
        }

    # CASH FLOW PRESSURE
    if c or ar:
        output["Cash Position"] = {
            "summary": f"Cash is {fmt(c)} with {fmt(ar)} tied in receivables.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Accounts Receivable: {fmt(ar)}"
            ]
        }

    # FINANCIAL STABILITY
    if c and l:
        output["Stability"] = {
            "summary": f"Cash of {fmt(c)} compared to liabilities of {fmt(l)} shows current financial position.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Liabilities: {fmt(l)}"
            ]
        }

    return output

# =====================================================
# SNAPSHOT
# =====================================================
if run_btn:

    data = latest_data()

    if not data:
        st.warning("No reports yet")
        st.stop()

    result = insights(data)

    st.markdown("## Business Snapshot")

    for k, v in result.items():
        st.subheader(k)
        st.write(v["summary"])

        st.write("Evidence:")
        for x in v["evidence"]:
            st.write("- " + x)

    st.write("---")
    st.write("Reports stored:", len(st.session_state.reports))
