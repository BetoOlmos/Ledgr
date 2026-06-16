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

    # =================================================
    # PROFITABILITY (WHAT + WHY + SO WHAT)
    # =================================================
    if r and e:
        p = r - e
        margin = (p / r) if r else 0

        output["Profitability"] = {
            "summary": (
                f"Revenue is {fmt(r)} and expenses are {fmt(e)}, "
                f"resulting in about {fmt(p)} profit. "
                f"This means roughly {margin:.0%} of revenue is retained as profit."
            ),
            "interpretation": (
                "Profit is determined by how efficiently revenue is converted after costs. "
                "Even with strong revenue, high expenses can compress real earnings."
            ),
            "evidence": [
                f"Revenue: {fmt(r)}",
                f"Expenses: {fmt(e)}",
                f"Profit: {fmt(p)}",
                f"Profit Margin: {margin:.0%}"
            ]
        }

    # =================================================
    # CASH POSITION (LIQUIDITY PRESSURE)
    # =================================================
    if c or ar:
        pressure_note = ""

        if ar and r:
            ar_ratio = ar / r
            pressure_note = f"Accounts receivable represents {ar_ratio:.0%} of revenue, which can delay cash flow."

        output["Cash Position"] = {
            "summary": (
                f"Cash is {fmt(c)} with {fmt(ar)} tied in accounts receivable. "
                f"{pressure_note}"
            ),
            "interpretation": (
                "Cash position reflects real liquidity, not just profit. "
                "High receivables can create cash stress even in profitable businesses."
            ),
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Accounts Receivable: {fmt(ar)}"
            ]
        }

    # =================================================
    # FINANCIAL STABILITY (BALANCE PRESSURE)
    # =================================================
    if c and l:
        ratio = c / l if l else 0

        output["Stability"] = {
            "summary": (
                f"Cash of {fmt(c)} compared to liabilities of {fmt(l)} "
                f"gives a liquidity coverage ratio of {ratio:.2f}."
            ),
            "interpretation": (
                "This ratio indicates short-term financial resilience. "
                "Lower coverage can signal reliance on incoming cash flow to meet obligations."
            ),
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Liabilities: {fmt(l)}",
                f"Coverage Ratio: {ratio:.2f}"
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
