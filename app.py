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

def num(v):
    try:
        v = float(v)
        if v == 0:
            return None
        return v
    except:
        return None

def delta(curr, prev):
    if curr is None or prev is None:
        return None
    return curr - prev

def safe(v):
    return v if v is not None else None

# =====================================================
# PARSER (TEXT)
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {}
    lines = text.split("\n")

    for line in lines:
        l = line.lower()
        nums = re.findall(r"[\$]?\d[\d,]*\.?\d*", l)

        if not nums:
            continue

        value = num(nums[-1].replace("$", "").replace(",", ""))
        if value is None:
            continue

        if "revenue" in l or "sales" in l:
            out["revenue"] = value
        elif "expense" in l:
            out["expenses"] = value
        elif "profit" in l or "net income" in l:
            out["profit"] = value
        elif "cash" in l:
            out["cash"] = value
        elif "liabil" in l or "debt" in l:
            out["liabilities"] = value
        elif "receivable" in l or "ar" in l:
            out["ar"] = value

    return out

# =====================================================
# CSV PARSER
# =====================================================
def parse_csv(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower()

    out = {}

    for c in df.columns:
        col = df[c]

        if "revenue" in c or "sales" in c:
            out["revenue"] = num(col.sum())

        elif "expense" in c:
            out["expenses"] = num(col.sum())

        elif "profit" in c:
            out["profit"] = num(col.sum())

        elif "cash" in c:
            out["cash"] = num(col.sum())

        elif "liabil" in c or "debt" in c:
            out["liabilities"] = num(col.sum())

        elif "receivable" in c or "ar" in c:
            out["ar"] = num(col.sum())

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
# SNAPSHOT ENGINE (FIXED CORE VALUE)
# =====================================================
def build_snapshot(r, e, p, c, l):

    r = safe(r)
    e = safe(e)
    p = safe(p)
    c = safe(c)

    profit = p if p is not None else (r - e if r and e else None)

    parts = []

    if r and e:
        parts.append(f"Revenue was {fmt(r)} against {fmt(e)} in expenses")

    if profit is not None:
        parts.append(f"resulting in about {fmt(profit)} in profit")

    if c:
        parts.append(f"Cash stands at {fmt(c)}")

    if l:
        parts.append(f"with liabilities around {fmt(l)}")

    base = ". ".join(parts)

    return base + "."

# =====================================================
# INSIGHTS ENGINE
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

    rev_d = delta(r, rp)
    prof_d = delta(p, pp)
    exp_d = delta(e, ep)

    snapshot = build_snapshot(r, e, p, c, l)

    return [
        {
            "title": "Business Snapshot",
            "what": snapshot,
            "evidence": []
        },
        {
            "title": "Profitability",
            "what": f"Revenue {fmt(r)}, Expenses {fmt(e)}, Profit {fmt(p)}",
            "evidence": [
                f"Profit Change: {fmt(prof_d)}"
            ]
        },
        {
            "title": "Growth",
            "what": f"Revenue {fmt(r)} (change {fmt(rev_d)})",
            "evidence": []
        },
        {
            "title": "Expenses",
            "what": f"Expenses {fmt(e)} (change {fmt(exp_d)})",
            "evidence": []
        },
        {
            "title": "Cash Position",
            "what": f"Cash {fmt(c)} with receivables {fmt(ar)}",
            "evidence": []
        },
        {
            "title": "Financial Stability",
            "what": f"Cash {fmt(c)} vs liabilities {fmt(l)}",
            "evidence": []
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
# MAIN FLOW
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
        st.warning("No data detected.")
        st.stop()

    sections = build_sections(latest, prev)

    # CLEAR INPUT (REAL FIX)
    st.session_state["financial_input"] = ""

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
