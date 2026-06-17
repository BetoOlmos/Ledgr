import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Business Pulse", layout="wide")

# =====================================================
# MEMORY
# =====================================================
if "reports" not in st.session_state:
    st.session_state.reports = []

# =====================================================
# HELPERS
# =====================================================
def fmt(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}"

def delta(curr, prev):
    if curr is None or prev is None:
        return None
    return curr - prev

# =====================================================
# PARSER
# =====================================================
def extract(text):
    if not text:
        return {}

    out = {}

    for line in text.split("\n"):
        l = line.lower()
        nums = re.findall(r"\$?\(?\d[\d,]*\.?\d*\)?", l)

        if not nums:
            continue

        val = nums[-1].replace("$", "").replace(",", "")
        if "(" in val:
            val = "-" + val.replace("(", "").replace(")", "")

        try:
            v = float(val)
        except:
            continue

        if "revenue" in l or "sales" in l:
            out["revenue"] = v
        elif "expense" in l:
            out["expenses"] = v
        elif "profit" in l:
            out["profit"] = v
        elif "cash" in l:
            out["cash"] = v
        elif "liabil" in l:
            out["liabilities"] = v
        elif "receivable" in l or "ar" in l:
            out["ar"] = v

    return out

# =====================================================
# MODEL
# =====================================================
def get_models():
    if not st.session_state.reports:
        return {}, {}

    latest = st.session_state.reports[-1]["data"]
    prev = st.session_state.reports[-2]["data"] if len(st.session_state.reports) > 1 else {}

    return latest, prev

# =====================================================
# CFO INTELLIGENCE ENGINE (THIS IS THE CORE FIX)
# =====================================================
def build_cfo(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    ar = latest.get("ar")
    l = latest.get("liabilities")

    rp = prev.get("revenue")
    pp = prev.get("profit")
    ep = prev.get("expenses")

    rev_d = delta(r, rp)
    prof_d = delta(p, pp)
    exp_d = delta(e, ep)

    # -----------------------------
    # GLOBAL SNAPSHOT (NARRATIVE)
    # -----------------------------
    summary = []

    if rev_d and prof_d:
        if rev_d > 0 and prof_d < rev_d:
            summary.append(
                f"Revenue increased by approximately {fmt(rev_d)} while profit improved by only {fmt(prof_d)}, "
                f"indicating growth is being absorbed by rising costs."
            )

    if exp_d and exp_d > 0:
        summary.append("Operating expenses increased during the period, putting pressure on margins.")

    if ar and ar > 0:
        summary.append("Unpaid customer invoices increased, tying up cash in receivables.")

    if c:
        summary.append("Cash position remains stable.")

    summary.append("Overall, the business is growing, but profitability quality should be monitored.")

    summary_text = " ".join(summary)

    # -----------------------------
    # SECTIONS
    # -----------------------------
    return summary_text, [
        {
            "title": "Profitability",
            "body": [
                f"Revenue: {fmt(r)}",
                f"Profit: {fmt(p)}",
                f"Profit Change: {fmt(prof_d)}",
                "Insight: Profitability depends on how much revenue converts into retained earnings."
            ]
        },
        {
            "title": "Growth",
            "body": [
                f"Revenue Change: {fmt(rev_d)}",
                "Insight: Growth is measured by expansion in top-line revenue."
            ]
        },
        {
            "title": "Expenses",
            "body": [
                f"Expense Change: {fmt(exp_d)}",
                "Insight: Expense behavior determines scalability."
            ]
        },
        {
            "title": "Cash Position",
            "body": [
                f"Cash: {fmt(c)}",
                f"Accounts Receivable: {fmt(ar)}",
                "Insight: Receivables affect real liquidity."
            ]
        },
        {
            "title": "Financial Stability",
            "body": [
                f"Liabilities: {fmt(l)}",
                f"Cash: {fmt(c)}",
                "Insight: Stability depends on ability to cover obligations."
            ]
        }
    ]

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

text = st.text_area("Paste financial report", height=200)

btn = st.button("Generate Business Pulse", use_container_width=True)

# =====================================================
# RUN
# =====================================================
if btn:

    parsed = extract(text)

    if parsed:
        st.session_state.reports.append({"data": parsed})

    latest, prev = get_models()

    summary, sections = build_cfo(latest, prev)

    st.markdown("## Business Snapshot")
    st.write(summary)

    for s in sections:
        st.subheader(s["title"])
        for line in s["body"]:
            st.write(line)

    st.write(f"Reports stored: {len(st.session_state.reports)}")
