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
    if v is None or v == 0:
        return "N/A"
    return f"${v:,.0f}"

def clean(v):
    # IMPORTANT: treat 0 as missing signal (your requirement fix)
    if v is None or v == 0:
        return None
    return v

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

        val = clean(val)

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
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["revenue"] = clean(v)

        if "expense" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["expenses"] = clean(v)

        if "profit" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["profit"] = clean(v)

        if "cash" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["cash"] = clean(v)

        if "liabil" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["liabilities"] = clean(v)

        if "receivable" in c or "ar" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["ar"] = clean(v)

    return out

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

text = st.text_area(
    "Paste financial report",
    height=200,
    key="financial_input"
)

csv_file = st.file_uploader(
    "Upload CSV (optional)",
    type=["csv"]
)

generate_btn = st.button(
    "Generate Business Pulse",
    use_container_width=True
)

# =====================================================
# GENERATE (ADD + ANALYZE IN ONE STEP)
# =====================================================

if generate_btn:

    parsed = {}

    if csv_file is not None:
        parsed = parse_csv(csv_file)

    elif text.strip():
        parsed = extract_numbers(text)

    if parsed:
        st.session_state.reports.append({
            "data": parsed,
            "time": datetime.now()
        })

    latest, prev = get_models()

    if not latest:
        st.warning("Paste a report or upload a CSV.")
        st.stop()

    sections = build_sections(latest, prev)

    # CLEAR INPUT BOX AFTER PROCESSING
    st.session_state.financial_input = ""

    st.markdown("## Business Pulse")

    for s in sections:

        st.subheader(s["title"])

        st.write(s["what"])

        st.write(
            f"Why: {s['why']}"
        )

        st.write(
            f"Why it matters: {s['why_matters']}"
        )

        if s["evidence"]:

            st.write("Evidence")

            for item in s["evidence"]:
                st.write(f"- {item}")

    st.rerun()

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
# SNAPSHOT BUILDER (FIXED)
# =====================================================
def build_snapshot(r, e, p, c, l, ar, rev_d, prof_d, exp_d, ar_d):

    parts = []

    if rev_d is not None:
        parts.append(f"Revenue moved {fmt(rev_d)}")

    if prof_d is not None:
        parts.append(f"profit changed {fmt(prof_d)}")

    if exp_d is not None:
        parts.append(f"expenses shifted {fmt(exp_d)}")

    if ar_d is not None:
        parts.append(f"receivables changed {fmt(ar_d)}")

    base = " ".join(parts)

    return f"{base}. Revenue is {fmt(r)}, profit is {fmt(p)}, cash is {fmt(c)}."

# =====================================================
# INSIGHTS ENGINE
# =====================================================
def build_sections(latest, prev):

    r = clean(latest.get("revenue"))
    e = clean(latest.get("expenses"))
    p = clean(latest.get("profit"))
    c = clean(latest.get("cash"))
    l = clean(latest.get("liabilities"))
    ar = clean(latest.get("ar"))

    rp = clean(prev.get("revenue"))
    ep = clean(prev.get("expenses"))
    pp = clean(prev.get("profit"))
    arp = clean(prev.get("ar"))

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
    # SNAPSHOT
    # =================================================
    sections.append({
        "title": "👀 CFO Snapshot",
        "what": snapshot,
        "why": "High-level view of financial movement across the business.",
        "why_matters": "Shows whether growth is healthy or being absorbed by costs and liquidity pressure.",
        "evidence": []
    })

    # =================================================
    # PROFITABILITY
    # =================================================
    sections.append({
        "title": "💰 Profitability",
        "what": f"Revenue {fmt(r)}, expenses {fmt(e)}, profit {fmt(p)}.",
        "why": "Profit is what remains after costs.",
        "why_matters": "Weak profit signals cost or pricing issues even in growth.",
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
        "what": f"Revenue is {fmt(r)} (change {fmt(rev_d)}).",
        "why": "Revenue drives scale.",
        "why_matters": "Growth without profit improvement reduces quality.",
        "evidence": [f"Revenue Change: {fmt(rev_d)}"]
    })

    # =================================================
    # EXPENSES
    # =================================================
    sections.append({
        "title": "💸 Expenses",
        "what": f"Expenses are {fmt(e)} (change {fmt(exp_d)}).",
        "why": "Expenses determine efficiency.",
        "why_matters": "Rising expenses reduce margin even with stable revenue.",
        "evidence": [f"Expense Change: {fmt(exp_d)}"]
    })

    # =================================================
    # CASH
    # =================================================
    sections.append({
        "title": "🏦 Cash Position",
        "what": f"Cash {fmt(c)} with receivables {fmt(ar)}.",
        "why": "Cash reflects liquidity.",
        "why_matters": "Receivables delay real cash availability.",
        "evidence": [f"AR Change: {fmt(ar_d)}"]
    })

    # =================================================
    # STABILITY
    # =================================================
    sections.append({
        "title": "⚖️ Financial Stability",
        "what": f"Cash {fmt(c)} vs liabilities {fmt(l)}. Coverage {coverage_display}.",
        "why": "Ability to meet obligations.",
        "why_matters": "Low coverage increases financial risk.",
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
