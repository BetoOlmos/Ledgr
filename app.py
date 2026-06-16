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

        if "revenue" in l or "sales" in l:
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

        if "receivable" in c:
            out["ar"] = pd.to_numeric(df[col], errors="coerce").sum()

    return out

# =====================================================
# UI
# =====================================================
st.title("Business Pulse")

text = st.text_area("Paste P&L or Balance Sheet", height=200)
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
# CORE MODEL (LATEST + PREVIOUS)
# =====================================================
def get_models():
    if not st.session_state.reports:
        return None, None

    latest = st.session_state.reports[-1]["data"]
    prev = st.session_state.reports[-2]["data"] if len(st.session_state.reports) > 1 else None

    return latest, prev

# =====================================================
# INSIGHT ENGINE (REAL BUSINESS LOGIC)
# =====================================================
def build_insights(latest, prev):

    r = latest.get("revenue")
    e = latest.get("expenses")
    p = latest.get("profit")
    c = latest.get("cash")
    l = latest.get("liabilities")
    ar = latest.get("ar")

    rp = prev.get("revenue") if prev else None
    ep = prev.get("expenses") if prev else None
    pp = prev.get("profit") if prev else None
    cp = prev.get("cash") if prev else None
    arp = prev.get("ar") if prev else None

    # =================================================
    # DELTAS
    # =================================================
    rev_d = delta(r, rp)
    prof_d = delta(p, pp)
    exp_d = delta(e, ep)
    cash_d = delta(c, cp)
    ar_d = delta(ar, arp)

    insights = {}

    # =================================================
    # 👀 BUSINESS SNAPSHOT (NARRATIVE)
    # =================================================
    snapshot = []

    if r and rp:
        snapshot.append(f"Revenue changed by {fmt(rev_d)}.")

    if p and pp:
        snapshot.append(f"Profit changed by {fmt(prof_d)}.")

    if exp_d:
        snapshot.append(f"Expenses moved by {fmt(exp_d)}.")

    if ar_d:
        snapshot.append(f"Accounts receivable changed by {fmt(ar_d)}.")

    if r and p:
        snapshot.append(
            f"Revenue is {fmt(r)} while profit is {fmt(p)}, "
            f"showing {'strong' if p/r > 0.15 else 'moderate' if p/r > 0.05 else 'weak'} margin efficiency."
        )

    insights["👀 Business Snapshot"] = {
        "summary": " ".join(snapshot),
        "evidence": [
            f"Revenue: {fmt(r)}",
            f"Profit: {fmt(p)}",
            f"Expenses: {fmt(e)}",
            f"Cash: {fmt(c)}",
            f"AR: {fmt(ar)}"
        ]
    }

    # =================================================
    # 💰 PROFITABILITY
    # =================================================
    if r and e and p:
        insights["💰 Profitability"] = {
            "summary": (
                f"Revenue is {fmt(r)}, but profit is only {fmt(p)} because expenses are {fmt(e)}."
                + (f" Profit changed by {fmt(prof_d)}." if prof_d else "")
            ),
            "why": "Profit is determined by how much of revenue is retained after costs.",
            "why_it_matters": "Strong revenue with weak profit signals cost pressure or inefficiency.",
            "evidence": [
                f"Revenue Change: {fmt(rev_d)}",
                f"Profit Change: {fmt(prof_d)}",
                f"Expense Change: {fmt(exp_d)}"
            ]
        }

    # =================================================
    # 📈 GROWTH
    # =================================================
    if r:
        insights["📈 Growth"] = {
            "summary": f"Revenue is currently {fmt(r)} with a change of {fmt(rev_d)}.",
            "why": "Revenue is the top-line driver of all business performance.",
            "why_it_matters": "Growth without profit improvement may indicate rising cost structure.",
            "evidence": [
                f"Revenue Change: {fmt(rev_d)}"
            ]
        }

    # =================================================
    # 💸 EXPENSES
    # =================================================
    if e:
        insights["💸 Expenses"] = {
            "summary": f"Expenses are {fmt(e)} with a change of {fmt(exp_d)}.",
            "why": "Expenses determine how efficiently revenue is converted into profit.",
            "why_it_matters": "Rising expenses without matching revenue growth reduces sustainability.",
            "evidence": [
                f"Expense Change: {fmt(exp_d)}"
            ]
        }

    # =================================================
    # 🏦 CASH
    # =================================================
    if c or ar:
        insights["🏦 Cash Position"] = {
            "summary": (
                f"Cash is {fmt(c)} with {fmt(ar)} in unpaid invoices."
                + (f" AR changed by {fmt(ar_d)}." if ar_d else "")
            ),
            "why": "Cash represents real liquidity, not accounting profit.",
            "why_it_matters": "High receivables can create cash flow stress even in profitable businesses.",
            "evidence": [
                f"Cash Change: {fmt(cash_d)}",
                f"AR Change: {fmt(ar_d)}"
            ]
        }

    # =================================================
    # ⚖️ DEBT / STABILITY
    # =================================================
    if c and l:
        ratio = c / l if l else 0

        insights["⚖️ Debt & Stability"] = {
            "summary": f"Cash of {fmt(c)} vs liabilities of {fmt(l)}.",
            "why": "Measures short-term financial resilience.",
            "why_it_matters": "Low coverage indicates dependency on incoming cash flow to survive obligations.",
            "evidence": [
                f"Cash: {fmt(c)}",
                f"Liabilities: {fmt(l)}",
                f"Coverage Ratio: {ratio:.2f}"
            ]
        }

    return insights

# =====================================================
# RUN
# =====================================================
if run_btn:

    latest, prev = get_models()

    if not latest:
        st.warning("No reports yet")
        st.stop()

    result = build_insights(latest, prev)

    st.markdown("## Business Pulse")

    for k, v in result.items():
        st.subheader(k)

        st.write(v["summary"])

        if "why" in v:
            st.write("Why:", v["why"])

        if "why_it_matters" in v:
            st.write("Why it matters:", v["why_it_matters"])

        st.write("Evidence:")
        for e in v["evidence"]:
            st.write("- " + e)

    st.write("---")
    st.write(f"Reports stored: {len(st.session_state.reports)}")
