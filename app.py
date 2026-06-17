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

def parse_number(s):
    if not s:
        return None

    s = s.replace("$", "").replace(",", "").strip()

    # handle (12,000)
    if "(" in s and ")" in s:
        s = s.replace("(", "-").replace(")", "")

    try:
        v = float(s)
        if v == 0:
            return None
        return v
    except:
        return None

# =====================================================
# STRONG PARSER
# =====================================================
def extract_numbers(text):
    if not text:
        return {}

    out = {
        "revenue": [],
        "expenses": [],
        "profit": [],
        "cash": [],
        "liabilities": [],
        "ar": []
    }

    lines = text.split("\n")

    for line in lines:
        l = line.lower()

        nums = re.findall(r"\(?\$?\d[\d,]*\.?\d*\)?", l)
        if not nums:
            continue

        val = parse_number(nums[-1])
        if val is None:
            continue

        # broader classification logic
        if "revenue" in l or "sales" in l or "income" in l:
            out["revenue"].append(val)

        elif "expense" in l or "cost" in l:
            out["expenses"].append(val)

        elif "net income" in l or "net profit" in l or "profit" in l:
            out["profit"].append(val)

        elif "cash" in l:
            out["cash"].append(val)

        elif "liabil" in l or "debt" in l:
            out["liabilities"].append(val)

        elif "receivable" in l or "ar" in l:
            out["ar"].append(val)

    # collapse lists → single values
    return {k: sum(v) if v else None for k, v in out.items()}

# =====================================================
# CSV PARSER
# =====================================================
def parse_csv(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.lower()

    def colsum(keyword):
        cols = [c for c in df.columns if keyword in c]
        if not cols:
            return None
        total = 0
        for c in cols:
            total += pd.to_numeric(df[c], errors="coerce").sum()
        return total if total != 0 else None

    return {
        "revenue": colsum("revenue") or colsum("sales"),
        "expenses": colsum("expense"),
        "profit": colsum("profit"),
        "cash": colsum("cash"),
        "liabilities": colsum("liabil") or colsum("debt"),
        "ar": colsum("receivable") or colsum("ar")
    }

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
# SNAPSHOT (CORE VALUE)
# =====================================================
def build_snapshot(r, e, p, c):

    # fallback profit if missing
    if p is None and r is not None and e is not None:
        p = r - e

    parts = []

    if r is not None and e is not None:
        parts.append(f"Revenue of {fmt(r)} against expenses of {fmt(e)}")

    if p is not None:
        parts.append(f"resulting in {fmt(p)} in profit")

    if c is not None:
        parts.append(f"Cash position stands at {fmt(c)}")

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
    ar = latest.get("ar")

    rp = prev.get("revenue")
    pp = prev.get("profit")

    rev_d = (r - rp) if r and rp else None
    prof_d = (p - pp) if p and pp else None

    snapshot = build_snapshot(r, e, p, c)

    return [
        {
            "title": "Business Snapshot",
            "what": snapshot,
            "evidence": []
        },
        {
            "title": "Profitability",
            "what": f"Revenue {fmt(r)}, Expenses {fmt(e)}, Profit {fmt(p)}",
            "evidence": [f"Profit Change: {fmt(prof_d)}"]
        },
        {
            "title": "Growth",
            "what": f"Revenue {fmt(r)}",
            "evidence": [f"Revenue Change: {fmt(rev_d)}"]
        },
        {
            "title": "Expenses",
            "what": f"Expenses {fmt(e)}",
            "evidence": []
        },
        {
            "title": "Cash Position",
            "what": f"Cash {fmt(c)}",
            "evidence": []
        },
        {
            "title": "Financial Stability",
            "what": f"Cash {fmt(c)} vs Liabilities {fmt(l)}",
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
# RUN
# =====================================================
if generate_btn:

    parsed = {}

    if csv_file:
        parsed = parse_csv(csv_file)
    elif text.strip():
        parsed = extract_numbers(text)

    if parsed:
        st.session_state.reports.append({
            "data": parsed,
            "time": datetime.now()
        })

    latest, prev = get_models()

    sections = build_sections(latest, prev)

    st.session_state["financial_input"] = ""

    st.markdown("## Business Pulse")

    for s in sections:
        st.subheader(s["title"])
        st.write(s["what"])

    st.write(f"Reports stored: {len(st.session_state.reports)}")
