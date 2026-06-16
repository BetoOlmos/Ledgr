import streamlit as st
import re
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Business Pulse",
    layout="wide"
)

# =====================================================
# MEMORY
# =====================================================
if "reports" not in st.session_state:
    st.session_state.reports = []

# =====================================================
# TITLE
# =====================================================
st.title("Business Pulse")
st.write("Paste financial reports → Generate business understanding")

# =====================================================
# INPUT FORM (THIS FIXES EVERYTHING)
# =====================================================
with st.form("report_form"):

    text = st.text_area("Paste financial report", height=200)

    submitted = st.form_submit_button("Add Report")

# =====================================================
# PARSER
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {}

    for line in text.split("\n"):
        line_lower = line.lower()

        nums = re.findall(r"[\$]?\d[\d,]*\.?\d*", line_lower)
        if not nums:
            continue

        try:
            value = float(nums[-1].replace("$", "").replace(",", ""))
        except:
            continue

        if "revenue" in line_lower or "sales" in line_lower:
            out["revenue"] = value

        elif "expense" in line_lower:
            out["expenses"] = value

        elif "profit" in line_lower:
            out["net_income"] = value

        elif "cash" in line_lower:
            out["cash"] = value

        elif "liabil" in line_lower:
            out["liabilities"] = value

        elif "asset" in line_lower:
            out["assets"] = value

        elif "receivable" in line_lower or "ar" in line_lower:
            out["ar"] = value

    return out

# =====================================================
# ADD REPORT
# =====================================================
if submitted:

    if not text.strip():
        st.warning("No input detected")
        st.stop()

    parsed = extract_numbers(text)

    st.session_state.reports.append({
        "raw": text,
        "data": parsed,
        "time": datetime.now()
    })

    st.success("Report added")

# =====================================================
# SNAPSHOT BUTTON
# =====================================================
if st.button("Generate Business Snapshot"):

    if not st.session_state.reports:
        st.warning("No reports yet")
        st.stop()

    latest = st.session_state.reports[-1]["data"]

    st.markdown("## Business Snapshot")

    revenue = latest.get("revenue")
    expenses = latest.get("expenses")
    cash = latest.get("cash")
    liabilities = latest.get("liabilities")
    ar = latest.get("ar")

    # PROFITABILITY
    if revenue and expenses:
        profit = revenue - expenses
        st.subheader("Profitability")
        st.write(f"Revenue: ${revenue:,.0f}")
        st.write(f"Expenses: ${expenses:,.0f}")
        st.write(f"Estimated Profit: ${profit:,.0f}")

    # CASH
    if cash or ar:
        st.subheader("Cash Position")
        st.write(f"Cash: ${cash:,.0f}")
        st.write(f"Accounts Receivable: ${ar:,.0f}")

    # STABILITY
    if cash and liabilities:
        st.subheader("Financial Stability")
        st.write(f"Cash: ${cash:,.0f}")
        st.write(f"Liabilities: ${liabilities:,.0f}")

    st.write("---")
    st.write("Reports stored:", len(st.session_state.reports))
