import streamlit as st
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

def to_num(x):
    try:
        x = float(x)
        if x == 0:
            return None
        return x
    except:
        return None

def delta(a, b):
    if a is None or b is None:
        return None
    return a - b

# =====================================================
# PARSER (robust enough for MVP)
# =====================================================
def parse(text):
    if not text:
        return {}

    out = {}

    for line in text.split("\n"):
        l = line.lower()
        nums = re.findall(r"\(?\$?\d[\d,]*\.?\d*\)?", l)

        if not nums:
            continue

        raw = nums[-1].replace("$", "").replace(",", "")

        if "(" in raw:
            raw = "-" + raw.replace("(", "").replace(")", "")

        v = to_num(raw)
        if v is None:
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
        elif "receivable" in l:
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
# CFO ENGINE (IMPROVED BUT STILL SIMPLE)
# =====================================================
def build(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    l = latest.get("liabilities")
    ar = latest.get("ar")

    rp = prev.get("revenue")
    pp = prev.get("profit")

    rev_d = delta(r, rp)
    prof_d = delta(p, pp)

    # -----------------------------
    # CFO PARAGRAPH (REAL IMPROVED VERSION)
    # -----------------------------
    parts = []

    if r and p:
        if rev_d and prof_d is not None:
            if rev_d > 0 and prof_d < rev_d:
                parts.append(
                    f"Revenue grew by {fmt(rev_d)} but profit increased by only {fmt(prof_d)}, "
                    f"showing reduced conversion efficiency."
                )
            elif rev_d and rev_d < 0:
                parts.append("Revenue declined during the period, signaling contraction in sales activity.")

    if e:
        parts.append("Expenses remain a key driver of performance.")

    if ar:
        parts.append("Unpaid invoices are tying up cash flow.")

    if c:
        parts.append("Cash position remains stable.")

    if not parts:
        parts.append("Business activity shows mixed signals with limited comparable history.")

    summary = " ".join(parts)

    # -----------------------------
    # SECTIONS
    # -----------------------------
    return summary, [
        ("Profitability", [
            f"Revenue: {fmt(r)}",
            f"Profit: {fmt(p)}",
            f"Profit Change: {fmt(prof_d)}"
        ]),
        ("Growth", [
            f"Revenue Change: {fmt(rev_d)}"
        ]),
        ("Expenses", [
            f"Expenses: {fmt(e)}"
        ]),
        ("Cash Position", [
            f"Cash: {fmt(c)}",
            f"Accounts Receivable: {fmt(ar)}"
        ]),
        ("Financial Stability", [
            f"Liabilities: {fmt(l)}",
            f"Cash: {fmt(c)}"
        ])
    ]

# =====================================================
# UI (FIX: FORM SOLVES INPUT ISSUE COMPLETELY)
# =====================================================
st.title("Business Pulse")

with st.form("form", clear_on_submit=True):

    text = st.text_area("Paste financial report")
    submitted = st.form_submit_button("Generate Business Pulse")

# =====================================================
# RUN
# =====================================================
if submitted:

    parsed = parse(text)

    if parsed:
        st.session_state.reports.append({"data": parsed})

    latest, prev = get_models()
    summary, sections = build(latest, prev)

    st.markdown("## Business Snapshot")
    st.write(summary)

    for title, lines in sections:
        st.subheader(title)
        for l in lines:
            st.write(l)

    st.write(f"Reports stored: {len(st.session_state.reports)}")
