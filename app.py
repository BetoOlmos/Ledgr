import streamlit as st
import pandas as pd

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Ledgr",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>

.stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}

html, body, p, span, div, label {
    color: #FAFAFA !important;
}

.block-container {
    padding-top: 2rem;
}

.hero {
    text-align: center;
    padding: 2rem 0 1rem 0;
}

.title {
    font-size: 64px;
    font-weight: 700;
}

.subtitle {
    font-size: 18px;
    color: #9CA3AF;
    margin-top: 10px;
}

hr {
    border: 1px solid rgba(255,255,255,0.08);
}

.section {
    margin-top: 1.5rem;
    padding: 1rem;
    background-color: #161B22;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="hero">
    <div class="title">Ledgr</div>
    <div class="subtitle">Upload your P&L. Get instant Business Pulse.</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# UPLOAD
# =====================================================
file = st.file_uploader("Upload P&L CSV", type=["csv"])

if not file:
    st.stop()

df = pd.read_csv(file)
df.columns = df.columns.str.lower().str.strip()

required = {"period", "revenue", "expenses"}
if not required.issubset(df.columns):
    st.error("CSV must contain: period, revenue, expenses")
    st.stop()

df["period"] = pd.to_datetime(df["period"], errors="coerce")
df = df.sort_values("period")

df["profit"] = df["revenue"] - df["expenses"]

# =====================================================
# HELPERS
# =====================================================
def safe_change(curr, prev):
    if prev == 0:
        return 0
    return curr - prev

# =====================================================
# LATEST PERIODS
# =====================================================
latest = df.iloc[-1]
previous = df.iloc[-2] if len(df) > 1 else latest

rev_change = safe_change(latest["revenue"], previous["revenue"])
exp_change = safe_change(latest["expenses"], previous["expenses"])
profit_change = safe_change(latest["profit"], previous["profit"])

# =====================================================
# BUSINESS PULSE TITLE
# =====================================================
st.markdown("---")
st.markdown("# Business Pulse")

# =====================================================
# 1. AM I MAKING MONEY?
# =====================================================
st.markdown("## Am I Making Money?")

if latest["profit"] > 0:
    st.success(f"Yes. You made ${latest['profit']:,.0f} profit in the latest period.")
else:
    st.error(f"No. You lost ${abs(latest['profit']):,.0f} in the latest period.")

# =====================================================
# 2. WHAT CHANGED?
# =====================================================
st.markdown("## What Changed?")

st.write(f"Revenue changed by ${rev_change:,.0f}.")
st.write(f"Expenses changed by ${exp_change:,.0f}.")
st.write(f"Profit changed by ${profit_change:,.0f}.")

# =====================================================
# 3. IS REVENUE GROWING?
# =====================================================
st.markdown("## Is Revenue Growing?")

if latest["revenue"] > previous["revenue"]:
    st.success(
        f"Yes. Revenue increased from ${previous['revenue']:,.0f} to ${latest['revenue']:,.0f}."
    )
else:
    st.warning(
        f"No. Revenue decreased from ${previous['revenue']:,.0f} to ${latest['revenue']:,.0f}."
    )

# =====================================================
# 4. IS PROFIT GROWING?
# =====================================================
st.markdown("## Is Profit Growing?")

if latest["profit"] > previous["profit"]:
    st.success(
        f"Yes. Profit increased from ${previous['profit']:,.0f} to ${latest['profit']:,.0f}."
    )
else:
    st.warning(
        f"No. Profit decreased from ${previous['profit']:,.0f} to ${latest['profit']:,.0f}."
    )

# =====================================================
# 5. WHAT STANDS OUT?
# =====================================================
st.markdown("## What Stands Out?")

if latest["revenue"] > latest["expenses"]:
    st.write("Revenue is higher than expenses, indicating positive operating performance.")
else:
    st.write("Expenses are higher than revenue, which may indicate losses.")

best_month = df.loc[df["profit"].idxmax()]
st.write(
    f"Your strongest period was {best_month['period'].strftime('%B %Y')} "
    f"with ${best_month['profit']:,.0f} profit."
)

# =====================================================
# 6. WHAT SHOULD I PAY ATTENTION TO?
# =====================================================
st.markdown("## What Should I Pay Attention To?")

if exp_change > rev_change:
    st.warning("Expenses increased more than revenue in the latest period.")
else:
    st.success("Expense growth is under control relative to revenue.")

# =====================================================
# 7. WHAT IS IMPROVING?
# =====================================================
st.markdown("## What Is Improving?")

if latest["profit"] > previous["profit"]:
    st.write(f"Profit improved by ${profit_change:,.0f}.")

if latest["revenue"] > previous["revenue"]:
    st.write(f"Revenue improved by ${rev_change:,.0f}.")

# =====================================================
# 8. WHAT IS GETTING WORSE?
# =====================================================
st.markdown("## What Is Getting Worse?")

issues = False

if latest["expenses"] > previous["expenses"]:
    st.write(f"Expenses increased by ${exp_change:,.0f}.")
    issues = True

if latest["profit"] < previous["profit"]:
    st.write(f"Profit decreased by ${abs(profit_change):,.0f}.")
    issues = True

if not issues:
    st.success("No major negative trends detected.")
