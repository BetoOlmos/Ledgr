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
# STYLE (DARK, CLEAN)
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
    padding: 3rem 0;
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

.card {
    background-color: #161B22;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 12px;
}

.metric {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
}

.good { color: #22c55e; }
.warn { color: #facc15; }
.bad { color: #ef4444; }

</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def health_score(rev_growth, exp_growth, profit_margin):
    score = 0

    if rev_growth > 0:
        score += 1
    if exp_growth < rev_growth:
        score += 1
    if profit_margin > 0.1:
        score += 1

    if score == 3:
        return "🟢 Healthy"
    elif score == 2:
        return "🟡 Stable"
    else:
        return "🔴 Needs Attention"


def safe_pct_change(series):
    return series.pct_change().replace([float("inf"), -float("inf")], 0).fillna(0)


def insights(df):
    lines = []

    if len(df) >= 2:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        rev_change = ((last["revenue"] - prev["revenue"]) / prev["revenue"]) * 100 if prev["revenue"] != 0 else 0
        exp_change = ((last["expenses"] - prev["expenses"]) / prev["expenses"]) * 100 if prev["expenses"] != 0 else 0
        profit_change = ((last["profit"] - prev["profit"]) / abs(prev["profit"])) * 100 if prev["profit"] != 0 else 0

        lines.append(f"Revenue changed by {rev_change:.1f}% vs previous period.")
        lines.append(f"Expenses changed by {exp_change:.1f}% vs previous period.")
        lines.append(f"Profit changed by {profit_change:.1f}% vs previous period.")

    # trend insights
    if df["revenue"].is_monotonic_increasing:
        lines.append("Revenue has been consistently increasing.")
    if df["expenses"].iloc[-1] > df["expenses"].mean():
        lines.append("Latest expenses are above average.")

    if df["profit"].iloc[-1] > df["profit"].mean():
        lines.append("Profit is currently above historical average.")

    return lines


def risks_opps(df):
    risks = []
    opps = []

    if len(df) >= 3:
        if df["expenses"].iloc[-1] > df["expenses"].iloc[-2] > df["expenses"].iloc[-3]:
            risks.append("Expenses have increased for 3 consecutive periods.")

        if df["revenue"].iloc[-1] < df["revenue"].iloc[-2]:
            risks.append("Revenue has declined in the latest period.")

        if df["profit"].iloc[-1] > df["profit"].iloc[-2]:
            opps.append("Profit is improving in the latest period.")

        if df["revenue"].iloc[-1] > df["expenses"].iloc[-1]:
            opps.append("Revenue currently exceeds expenses.")

    return risks, opps


# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="hero">
    <div class="title">Ledgr</div>
    <div class="subtitle">
        Upload your P&L. Understand your business instantly.
    </div>
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

# expected: period, revenue, expenses
required = {"period", "revenue", "expenses"}
if not required.issubset(df.columns):
    st.error("CSV must contain: period, revenue, expenses")
    st.stop()

df["profit"] = df["revenue"] - df["expenses"]

df["period"] = pd.to_datetime(df["period"], errors="coerce")
df = df.sort_values("period")

df["rev_growth"] = safe_pct_change(df["revenue"])
df["exp_growth"] = safe_pct_change(df["expenses"])
df["profit_margin"] = df["profit"] / df["revenue"].replace(0, 1)

# =====================================================
# HEALTH
# =====================================================
last = df.iloc[-1]
rev_growth = df["rev_growth"].iloc[-1]
exp_growth = df["exp_growth"].iloc[-1]
profit_margin = df["profit_margin"].iloc[-1]

health = health_score(rev_growth, exp_growth, profit_margin)

st.markdown(f"## Business Pulse: {health}")

st.markdown("### What Changed")

st.write(f"Revenue: {rev_growth*100:.1f}%")
st.write(f"Expenses: {exp_growth*100:.1f}%")
st.write(f"Profit: {((df['profit'].iloc[-1] - df['profit'].iloc[-2]) / abs(df['profit'].iloc[-2]) * 100) if len(df) > 1 else 0:.1f}%")

# =====================================================
# TRENDS
# =====================================================
st.markdown("### Trends")

st.line_chart(df.set_index("period")[["revenue", "expenses", "profit"]])

# =====================================================
# COST DRIVERS (simplified proxy)
# =====================================================
st.markdown("### Key Drivers")

st.write(f"Avg Revenue: {df['revenue'].mean():,.0f}")
st.write(f"Avg Expenses: {df['expenses'].mean():,.0f}")
st.write(f"Avg Profit: {df['profit'].mean():,.0f}")

# =====================================================
# INSIGHTS
# =====================================================
st.markdown("### Insights")

for line in insights(df):
    st.write("• " + line)

# =====================================================
# RISKS & OPPORTUNITIES
# =====================================================
risks, opps = risks_opps(df)

st.markdown("### Risks")
for r in risks:
    st.write("• " + r)

st.markdown("### Opportunities")
for o in opps:
    st.write("• " + o)
