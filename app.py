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

def safe_ratio(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b

# =====================================================
# PARSER
# =====================================================
def extract_numbers(text):
    out = {}
    if not text:
        return out

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
            out["profit"] = val
        elif "cash" in l:
            out["cash"] = val
        elif "liabil" in l:
            out["liabilities"] = val
        elif "receivable" in l or "ar" in l:
            out["ar"] = val

    return out

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
            out["profit"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "cash" in c:
            out["cash"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "liabil" in c:
            out["liabilities"] = pd.to_numeric(df[col], errors="coerce").sum()

        if "receivable" in c or "ar" in c:
            out["ar"] = pd.to_numeric(df[col], errors="coerce").sum()

    return out

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

text = st.text_area("Paste financial report", height=200)
csv_file = st.file_uploader("Or upload CSV", type=["csv"])

col1, col2 = st.columns(2)

with col1:
    add_btn = st.button("Add Report")

with col2:
    run_btn = st.button("Generate Business Pulse")

# =====================================================
# ADD REPORT
# =====================================================
if add_btn:
    parsed = parse_csv(csv_file) if csv_file else extract_numbers(text)

    if not parsed:
        st.warning("No financial data detected")
        st.stop()

    st.session_state.reports.append({
        "data": parsed,
        "time": datetime.now()
    })

    st.success("Report added")

# =====================================================
# MODEL
# =====================================================
def get_models():
    if not st.session_state.reports:
        return None, None

    latest = st.session_state.reports[-1]["data"]
    prev = st.session_state.reports[-2]["data"] if len(st.session_state.reports) > 1 else {}

    return latest, prev

# =====================================================
# CFO SNAPSHOT ENGINE
# =====================================================
def build_snapshot(r, e, p, c, l, ar, rev_d, prof_d, exp_d, ar_d):

    pieces = []

    if rev_d is not None:
        pieces.append(f"Revenue moved by {fmt(rev_d)}")

    if prof_d is not None:
        pieces.append(f"profit changed by {fmt(prof_d)}")

    if exp_d is not None:
        pieces.append(f"expenses shifted by {fmt(exp_d)}")

    if ar_d is not None:
        pieces.append(f"receivables changed by {fmt(ar_d)}")

    return (
        "CFO Snapshot: "
        + ", ".join(pieces)
        + f". Revenue is {fmt(r)}, profit is {fmt(p)}, cash is {fmt(c)}."
    )

# =====================================================
# INSIGHT ENGINE
# =====================================================
def build_sections(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    l = latest.get("liabilities")
    ar = latest.get("ar")

    rp = prev.get("revenue")
    ep = prev.get("expenses")
    pp = prev.get("profit")
    arp = prev.get("ar")

    rev_d = delta(r, rp)
    prof_d = delta(p, pp)
    exp_d = delta(e, ep)
    ar_d = delta(ar, arp)

    profit_margin = safe_ratio(p, r)
    coverage = safe_ratio(c, l)
    coverage_display = f"{coverage:.2f}" if coverage is not None else "N/A"

    snapshot = build_snapshot(r, e, p, c, l, ar, rev_d, prof_d, exp_d, ar_d)

    sections = []

    # =================================================
    # SNAPSHOT (NO EVIDENCE HERE)
    # =================================================
    sections.append({
        "title": "👀 CFO Snapshot",
        "what": snapshot,
        "why": "This is the consolidated view of performance across revenue, profit, expenses, and cash flow.",
        "why_matters": "It tells you in one pass whether the business is improving or deteriorating.",
        "evidence": []
    })

    # =================================================
    # PROFITABILITY
    # =================================================
    sections.append({
        "title": "💰 Profitability",
        "what": f"Revenue is {fmt(r)}, expenses are {fmt(e)}, profit is {fmt(p)}.",
        "why": "Profit shows what remains after all costs are removed.",
        "why_matters": "Rising revenue without profit growth indicates cost pressure.",
        "evidence": [
            f"Revenue Change: {fmt(rev_d)}",
            f"Profit Change: {fmt(prof_d)}"
        ]
    })

    # =================================================
    # GROWTH
    # =================================================
    sections.append({
        "title": "📈 Growth",
        "what": f"Revenue is {fmt(r)} with change of {fmt(rev_d)}.",
        "why": "Revenue is the primary driver of expansion.",
        "why_matters": "Growth without profit improvement reduces business quality.",
        "evidence": [f"Revenue Change: {fmt(rev_d)}"]
    })

    # =================================================
    # EXPENSES
    # =================================================
    sections.append({
        "title": "💸 Expenses",
        "what": f"Expenses are {fmt(e)} with change of {fmt(exp_d)}.",
        "why": "Expenses determine operational efficiency.",
        "why_matters": "Uncontrolled expenses erode profit even when revenue grows.",
        "evidence": [f"Expense Change: {fmt(exp_d)}"]
    })

    # =================================================
    # CASH
    # =================================================
    sections.append({
        "title": "🏦 Cash Position",
        "what": f"Cash is {fmt(c)} with {fmt(ar)} in receivables.",
        "why": "Cash reflects real liquidity available to operate the business.",
        "why_matters": "High receivables can create cash strain even in profitable companies.",
        "evidence": [f"AR Change: {fmt(ar_d)}"]
    })

    # =================================================
    # STABILITY
    # =================================================
    sections.append({
        "title": "⚖️ Financial Stability",
        "what": f"Cash is {fmt(c)} vs liabilities {fmt(l)}. Coverage ratio is {coverage_display}.",
        "why": "Measures ability to meet obligations with available cash.",
        "why_matters": "Low coverage increases financial vulnerability.",
        "evidence": [
            f"Cash: {fmt(c)}",
            f"Liabilities: {fmt(l)}"
        ]
    })

    return sections

# =====================================================
# RUN
# =====================================================
if run_btn:

    latest, prev = get_models()

    if not latest:
        st.warning("No reports yet")
        st.stop()

    sections = build_sections(latest, prev)

    st.markdown("## Business Pulse")

    for s in sections:
        st.subheader(s["title"])
        st.write(s["what"])
        st.write("Why:", s["why"])
        st.write("Why it matters:", s["why_matters"])

        if s["evidence"]:
            st.write("Evidence:")
            for e in s["evidence"]:
                st.write("- " + e)

    st.write("---")
    st.write(f"Reports stored: {len(st.session_state.reports)}")
