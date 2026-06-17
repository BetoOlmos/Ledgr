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

def clean(v):
    if v is None:
        return None
    try:
        v = float(v)
    except:
        return None
    if v == 0:
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
# PARSER (TEXT)
# =====================================================
def extract_numbers(text):
    out = {}
    if not text:
        return out

    lines = text.split("\n")

    for line in lines:
        l = line.lower()
        nums = re.findall(r"[\$]?\d[\d,]*\.?\d*", l)

        if not nums:
            continue

        try:
            val = float(nums[-1].replace("$", "").replace(",", ""))
        except:
            continue

        val = clean(val)

        if val is None:
            continue

        if "revenue" in l or "sales" in l or "income" in l:
            out["revenue"] = val
        elif "expense" in l:
            out["expenses"] = val
        elif "profit" in l:
            out["profit"] = val
        elif "cash" in l:
            out["cash"] = val
        elif "liabil" in l or "debt" in l:
            out["liabilities"] = val
        elif "receivable" in l or "ar" in l:
            out["ar"] = val

    return out

# =====================================================
# PARSER (CSV)
# =====================================================
def parse_csv(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower()

    out = {}

    for col in df.columns:
        c = col.lower()

        if "revenue" in c or "sales" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["revenue"] = clean(v)

        elif "expense" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["expenses"] = clean(v)

        elif "profit" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["profit"] = clean(v)

        elif "cash" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["cash"] = clean(v)

        elif "liabil" in c or "debt" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["liabilities"] = clean(v)

        elif "receivable" in c or "ar" in c:
            v = pd.to_numeric(df[col], errors="coerce").sum()
            out["ar"] = clean(v)

    return out

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
# SNAPSHOT
# =====================================================
def build_snapshot(r, e, p, c, l, ar, rev_d, prof_d, exp_d):

    parts = []

    if rev_d is not None:
        parts.append(f"Revenue moved {fmt(rev_d)}")

    if prof_d is not None:
        parts.append(f"profit changed {fmt(prof_d)}")

    if exp_d is not None:
        parts.append(f"expenses shifted {fmt(exp_d)}")

    base = " ".join(parts)

    return f"{base}. Revenue is {fmt(r)}, profit is {fmt(p)}, cash is {fmt(c)}."

# =====================================================
# INSIGHTS
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

    rev_d = delta(r, rp)
    prof_d = delta(p, pp)
    exp_d = delta(e, ep)

    coverage = safe_ratio(c, l)
    coverage_display = f"{coverage:.2f}" if coverage is not None else "N/A"

    snapshot = build_snapshot(r, e, p, c, l, ar, rev_d, prof_d, exp_d)

    return [
        {
            "title": "Business Snapshot",
            "what": snapshot,
            "evidence": []
        },
        {
            "title": "Profitability",
            "what": f"Revenue {fmt(r)}, Expenses {fmt(e)}, Profit {fmt(p)}.",
            "evidence": [
                f"Revenue Change: {fmt(rev_d)}",
                f"Profit Change: {fmt(prof_d)}"
            ]
        },
        {
            "title": "Growth",
            "what": f"Revenue is {fmt(r)} (change {fmt(rev_d)}).",
            "evidence": [f"Revenue Change: {fmt(rev_d)}"]
        },
        {
            "title": "Expenses",
            "what": f"Expenses are {fmt(e)} (change {fmt(exp_d)}).",
            "evidence": [f"Expense Change: {fmt(exp_d)}"]
        },
        {
            "title": "Cash Position",
            "what": f"Cash {fmt(c)} with receivables {fmt(ar)}.",
            "evidence": []
        },
        {
            "title": "Financial Stability",
            "what": f"Cash {fmt(c)} vs liabilities {fmt(l)}. Coverage {coverage_display}.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Liabilities: {fmt(l)}"
            ]
        }
    ]

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

text = st.text_area("Paste financial report", height=200)
csv_file = st.file_uploader("Upload CSV", type=["csv"])

generate_btn = st.button("Generate Business Pulse", use_container_width=True)

# =====================================================
# RUN (SINGLE FLOW)
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

    # clear input after run
    st.session_state.clear_input = True

    st.markdown("## Business Pulse")

    for s in sections:
        st.subheader(s["title"])
        st.write(s["what"])

        if s["evidence"]:
            st.write("Evidence")
            for e in s["evidence"]:
                st.write(f"- {e}")

    st.write("---")
    st.write(f"Reports stored: {len(st.session_state.reports)}")
