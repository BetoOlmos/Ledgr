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
# FORMAT HELPERS
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
# PARSERS
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

    parsed = {}

    if csv_file:
        parsed = parse_csv(csv_file)
    else:
        parsed = extract_numbers(text)

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
# INSIGHT ENGINE (CFO STYLE FIXED)
# =====================================================
def build_insights(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    l = latest.get("liabilities")
    ar = latest.get("ar")

    rp = prev.get("revenue")
    ep = prev.get("expenses")
    pp = prev.get("profit")
    cp = prev.get("cash")
    arp = prev.get("ar")

    rev_d = delta(r, rp)
    exp_d = delta(e, ep)
    prof_d = delta(p, pp)
    cash_d = delta(c, cp)
    ar_d = delta(ar, arp)

    profit_margin = safe_ratio(p, r)
    coverage = safe_ratio(c, l)

    coverage_display = f"{coverage:.2f}" if coverage is not None else "N/A"

    sections = []

    # =================================================
    # 👀 BUSINESS SNAPSHOT
    # =================================================
    story = []

    if rev_d is not None:
        story.append(f"Revenue changed by {fmt(rev_d)}.")

    if prof_d is not None:
        story.append(f"Profit changed by {fmt(prof_d)}.")

    if exp_d is not None:
        story.append(f"Expenses moved by {fmt(exp_d)}.")

    if ar_d is not None:
        story.append(f"Accounts receivable changed by {fmt(ar_d)}.")

    if r and p:
        efficiency = (
            "strong" if profit_margin and profit_margin > 0.15
            else "moderate" if profit_margin and profit_margin > 0.05
            else "weak"
        )

        story.append(
            f"Revenue is {fmt(r)} with profit of {fmt(p)}, showing {efficiency} margin efficiency."
        )

    sections.append({
        "title": "👀 Business Snapshot",
        "what": " ".join(story),
        "why": "This combines revenue, profit, expenses, and cash movement into a single business view.",
        "why_matters": "It shows whether growth is healthy or being absorbed by cost structure or cash pressure.",
        "evidence": [
            f"Revenue: {fmt(r)}",
            f"Profit: {fmt(p)}",
            f"Expenses: {fmt(e)}",
            f"Cash: {fmt(c)}",
            f"AR: {fmt(ar)}"
        ]
    })

    # =================================================
    # 💰 PROFITABILITY
    # =================================================
    sections.append({
        "title": "💰 Profitability",
        "what": f"Revenue is {fmt(r)} and expenses are {fmt(e)}, resulting in profit of {fmt(p)}. Profit changed by {fmt(prof_d)}.",
        "why": "Profit reflects how efficiently revenue converts into actual earnings.",
        "why_matters": "Strong revenue with weak profit signals cost pressure or inefficiency.",
        "evidence": [
            f"Revenue Change: {fmt(rev_d)}",
            f"Expense Change: {fmt(exp_d)}",
            f"Profit Change: {fmt(prof_d)}"
        ]
    })

    # =================================================
    # 📈 GROWTH
    # =================================================
    sections.append({
        "title": "📈 Growth",
        "what": f"Revenue is {fmt(r)} with change of {fmt(rev_d)}.",
        "why": "Revenue is the primary driver of business expansion.",
        "why_matters": "Growth without profit improvement may indicate rising cost structure.",
        "evidence": [
            f"Revenue Change: {fmt(rev_d)}"
        ]
    })

    # =================================================
    # 💸 EXPENSES
    # =================================================
    sections.append({
        "title": "💸 Expenses",
        "what": f"Expenses are {fmt(e)} with change of {fmt(exp_d)}.",
        "why": "Expenses determine operational efficiency.",
        "why_matters": "Rising expenses without revenue growth compress margins.",
        "evidence": [
            f"Expense Change: {fmt(exp_d)}"
        ]
    })

    # =================================================
    # 🏦 CASH POSITION
    # =================================================
    sections.append({
        "title": "🏦 Cash Position",
        "what": f"Cash is {fmt(c)} with {fmt(ar)} in receivables. Cash changed by {fmt(cash_d)}.",
        "why": "Cash represents real liquidity, not accounting profit.",
        "why_matters": "High receivables can create cash flow stress even in profitable businesses.",
        "evidence": [
            f"Cash Change: {fmt(cash_d)}",
            f"AR Change: {fmt(ar_d)}"
        ]
    })

    # =================================================
    # ⚖️ DEBT & STABILITY
    # =================================================
    sections.append({
        "title": "⚖️ Debt & Financial Stability",
        "what": f"Cash is {fmt(c)} vs liabilities of {fmt(l)}. Coverage ratio: {coverage_display}.",
        "why": "Measures ability to cover obligations with available cash.",
        "why_matters": "Low coverage signals dependency on incoming cash flow or financing.",
        "evidence": [
            f"Cash: {fmt(c)}",
            f"Liabilities: {fmt(l)}",
            f"Coverage Ratio: {coverage_display}"
        ]
    })

    return sections

# =====================================================
# RUN SNAPSHOT
# =====================================================
if run_btn:

    latest, prev = get_models()

    if not latest:
        st.warning("No reports yet")
        st.stop()

    result = build_insights(latest, prev)

    st.markdown("## Business Pulse")

    for s in result:
        st.subheader(s["title"])
        st.write(s["what"])
        st.write("Why:", s["why"])
        st.write("Why it matters:", s["why_matters"])
        st.write("Evidence:")
        for e in s["evidence"]:
            st.write("- " + e)

    st.write("---")
    st.write(f"Reports stored: {len(st.session_state.reports)}")
