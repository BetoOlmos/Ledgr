import streamlit as st
import pandas as pd
import re
from datetime import datetime

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

# =====================================================
# PARSER
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {"revenue": [], "expenses": [], "profit": [], "cash": [], "liabilities": []}

    for line in text.split("\n"):
        l = line.lower()
        nums = re.findall(r"\(?\$?\d[\d,]*\.?\d*\)?", l)

        if not nums:
            continue

        val = nums[-1].replace("$", "").replace(",", "")
        if "(" in val:
            val = "-" + val.replace("(", "").replace(")", "")

        v = num(val)
        if v is None:
            continue

        if "revenue" in l or "sales" in l:
            out["revenue"].append(v)
        elif "expense" in l:
            out["expenses"].append(v)
        elif "profit" in l or "net income" in l:
            out["profit"].append(v)
        elif "cash" in l:
            out["cash"].append(v)
        elif "liabil" in l:
            out["liabilities"].append(v)

    return {k: sum(v) if v else None for k, v in out.items()}

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
# SNAPSHOT
# =====================================================
def build_snapshot(r, e, p, c):

    if p is None and r is not None and e is not None:
        p = r - e

    parts = []

    if r is not None and e is not None:
        parts.append(f"Revenue of {fmt(r)} with expenses of {fmt(e)}")

    if p is not None:
        parts.append(f"producing about {fmt(p)} in profit")

    if c is not None:
        parts.append(f"Cash sits at {fmt(c)}")

    return ". ".join(parts) + "."

# =====================================================
# INSIGHTS
# =====================================================
def build_sections(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    l = latest.get("liabilities")

    snapshot = build_snapshot(r, e, p, c)

    return [
        {"title": "Business Snapshot", "what": snapshot},
        {"title": "Profitability", "what": f"Revenue {fmt(r)}, Expenses {fmt(e)}, Profit {fmt(p)}"},
        {"title": "Growth", "what": f"Revenue {fmt(r)}"},
        {"title": "Expenses", "what": f"Expenses {fmt(e)}"},
        {"title": "Cash Position", "what": f"Cash {fmt(c)}"},
        {"title": "Financial Stability", "what": f"Cash {fmt(c)} vs Liabilities {fmt(l)}"},
    ]

# =====================================================
# UI (FORM FIX — THIS SOLVES EVERYTHING)
# =====================================================
st.title("Business Pulse")

with st.form("pulse_form", clear_on_submit=True):

    text = st.text_area("Paste financial report", height=200)
    csv_file = st.file_uploader("Upload CSV", type=["csv"])

    submitted = st.form_submit_button("Generate Business Pulse")

# =====================================================
# RUN
# =====================================================
if submitted:

    parsed = {}

    if csv_file:
        parsed = pd.read_csv(csv_file).to_dict()
    elif text.strip():
        parsed = extract_numbers(text)

    if parsed:
        st.session_state.reports.append({
            "data": parsed,
            "time": datetime.now()
        })

    latest, prev = get_models()
    sections = build_sections(latest, prev)

    st.markdown("## Business Snapshot")

    for s in sections:
        st.subheader(s["title"])
        st.write(s["what"])

    st.write(f"Reports stored: {len(st.session_state.reports)}")
