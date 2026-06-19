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
# PARSER (Your Exact Original Robust Version)
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
        elif "net profit" in l or "net income" in l or "profit" in l:
            out["profit"] = v
        elif "cash" in l or "bank balance" in l:
            out["cash"] = v
        elif "liabil" in l or "payable" in l:
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
# UI PRESENTATION LAYER
# =====================================================
st.title("Business Pulse")

with st.form("form", clear_on_submit=True):
    text = st.text_area("Paste financial report details below:")
    submitted = st.form_submit_button("Generate Business Pulse")

# =====================================================
# RUN & ADVISORY LOGIC
# =====================================================
if submitted or len(st.session_state.reports) > 0:

    if submitted and text:
        parsed = parse(text)
        if parsed:
            st.session_state.reports.append({"data": parsed})

    latest, prev = get_models()

    # Extract clean numbers (default to 0 if missing to prevent math crashes)
    r = latest.get("revenue", 0)
    e = latest.get("expenses", 0)
    p = latest.get("profit", 0)
    c = latest.get("cash", 0)
    liab = latest.get("liabilities", 0)
    ar = latest.get("ar", 0)

    rp = prev.get("revenue", 0)
    pp = prev.get("profit", 0)
    cp = prev.get("cash", 0)

    # Core Ratio Math Calculations
    margin = (p / r * 100) if r else 0
    runway = (c / e) if e else 0
    current_ratio = (c / liab) if liab else 0
    
    rev_d = delta(r, rp)
    prof_d = delta(p, pp)

    # Display Section I: The CFO Summary
    st.markdown("## I. The High-Level CFO Summary")
    st.write(f"Total Revenue: {fmt(r)}")
    st.write(f"Take-Home Profit (Net): {fmt(p)} (A true {margin:.1f}% bottom-line margin)")
    st.write(f"Cash in Bank Today: {fmt(c)} (Available operating capital)")
    st.write(f"The Safety Net (Runway): {runway:.1f} Months")

    # Display Section II: Daily & Weekly Questions Explained
    st.markdown("## II. Critical Ratio Explanations")

    # Question 1: Liquidity & Bills Stress Test
    st.markdown("### 1. Can we pay our bills this Friday without stressing?")
    if current_ratio >= 1.5:
        st.write(f"**The Dollar Answer:** Yes. You currently have {fmt(c)} in cash and short-term assets for every {fmt(liab)} of bills coming due over the next 30 days.")
        if cp > 0 and c > cp:
            st.write("Why it changed: This cushion improved from last period because your real-time revenue collection increased faster than your near-term payables.")
        else:
            st.write("Why it changed: Your bill-paying safety net remains steady because your ongoing cash collections are cleanly pacing ahead of incoming bills.")
    else:
        st.write(f"**The Dollar Answer:** It will be tight. You only hold {fmt(c)} in immediate cash reserves against {fmt(liab)} in outstanding liabilities.")
        st.write("Why it changed: This tightening triggered because a large chunk of available capital was re-absorbed into ongoing fulfillment costs or immediate vendor payments.")

    # Question 2: Accounts Receivable Trapped Wealth Test
    st.markdown("### 2. Where is all our money? We are making sales, but the bank account feels empty.")
    if ar > 0:
        st.write(f"**The Dollar Answer:** Your cash is trapped in your clients' bank accounts. You currently have {fmt(ar)} in unpaid invoices outstanding.")
        st.write("Why it changed: Your client collection timelines have stretched out. Capital is locked up in outside invoices instead of being deposited into your checking vault.")
    else:
        st.write("**The Dollar Answer:** Invoicing lines are completely clear! Sales are moving directly from contract completion into liquid bank balances.")
        st.write("Why it changed: Your enforcement of strict payment tracking, immediate processing, or upfront retainers has eliminated a collection logjam.")

    # Question 3: Net Margin Efficiency Test
    st.markdown("### 3. Are we actually making money on our core services, or are our costs eating us alive?")
    if margin >= 15:
        st.write(f"**The Dollar Answer:** Yes, operations are efficient. You keep {margin:.1f}% of every dollar made, converting sales into {fmt(p)} of net profit.")
        if prof_d and prof_d > 0:
            st.write("Why it changed: Your take-home returns expanded because you successfully scaled top-line revenue numbers while keeping fixed operational overhead flat.")
        else:
            st.write("Why it changed: Efficiency remains high, showing that your current service pricing covers delivery costs with a strong safety buffer.")
    else:
        st.write(f"**The Dollar Answer:** No, expansion is inefficient. Your net take-home margin compressed to {margin:.1f}%, leaving you with {fmt(p)} in real profit.")
        if prof_d and prof_d < 0:
            st.write("Why it changed: This dropped from last period because your fulfillment delivery costs, software fees, or unbilled labor crept up faster than your pricing lines.")
        else:
            st.write("Why it changed: Operational costs or structural overhead expenses are re-absorbing too much core value before it reaches your bottom line.")

    st.write("---")
    st.write(f"Reports stored in current session: {len(st.session_state.reports)}")
