import streamlit as st
import pandas as pd
import re
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Business Pulse",
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
html, body, p, span, div {
    color: #FAFAFA !important;
}
.block-container {
    padding-top: 2rem;
}
.title {
    font-size: 42px;
    font-weight: 700;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #9CA3AF;
    margin-bottom: 2rem;
}
.section {
    background-color: #161B22;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("<div class='title'>Business Pulse</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Upload or paste financials → Understand your business instantly</div>", unsafe_allow_html=True)

# =====================================================
# ================= INPUT LAYER =======================
# =====================================================
st.markdown("## Input Financial Data")

text_input = st.text_area("Paste P&L or Balance Sheet (optional)", height=200)
file = st.file_uploader("Or upload CSV", type=["csv"])

# =====================================================
# =============== PARSER LAYER ========================
# =====================================================

def clean_number(value):
    if value is None:
        return None
    value = str(value)
    value = value.replace(",", "").replace("$", "").strip()
    try:
        return float(value)
    except:
        return None


def parse_text_financials(text):
    data = {}
    if not text:
        return data

    text = text.lower()

    patterns = {
        "revenue": r"(revenue|sales|income)[^\d]*([\d,\.]+)",
        "expenses": r"(expenses|expense|operating expenses|opex)[^\d]*([\d,\.]+)",
        "cogs": r"(cogs|cost of goods sold)[^\d]*([\d,\.]+)",
        "net_income": r"(net income|net profit|profit)[^\d]*([\d,\.]+)",
        "cash": r"(cash)[^\d]*([\d,\.]+)",
        "assets": r"(assets)[^\d]*([\d,\.]+)",
        "liabilities": r"(liabilities|debt)[^\d]*([\d,\.]+)",
        "equity": r"(equity)[^\d]*([\d,\.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            data[key] = clean_number(match.group(2))

    return data


# =====================================================
# =============== MODEL LAYER =========================
# =====================================================

def build_model(text_data, csv_df):
    model = {}
    model.update(text_data)

    if csv_df is not None:
        df = csv_df.copy()
        df.columns = df.columns.str.lower().str.strip()

        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"], errors="coerce")
            df = df.sort_values("period")

        if {"revenue", "expenses"}.issubset(df.columns):
            df["profit"] = df["revenue"] - df["expenses"]

            model["revenue_series"] = df["revenue"].tolist()
            model["expenses_series"] = df["expenses"].tolist()
            model["profit_series"] = df["profit"].tolist()

            model["df"] = df

        if {"cash", "assets", "liabilities"}.issubset(df.columns):
            model["cash_series"] = df["cash"].tolist()
            model["assets_series"] = df["assets"].tolist()
            model["liabilities_series"] = df["liabilities"].tolist()

    return model


# =====================================================
# =============== YEAR STORY ENGINE ===================
# =====================================================

def build_year_story(df):
    df = df.copy()
    df = df.sort_values("period")

    df["profit"] = df["revenue"] - df["expenses"]

    story = {
        "total_revenue": df["revenue"].sum(),
        "total_expenses": df["expenses"].sum(),
        "total_profit": df["profit"].sum(),
        "best_month": df.loc[df["profit"].idxmax()],
        "worst_month": df.loc[df["profit"].idxmin()],
        "revenue_trend": df["revenue"].iloc[-1] - df["revenue"].iloc[0],
        "profit_trend": df["profit"].iloc[-1] - df["profit"].iloc[0],
    }

    return story


# =====================================================
# =============== INSIGHT ENGINE ======================
# =====================================================

def generate_insights(model):
    insights = {}

    revenue = model.get("revenue")
    expenses = model.get("expenses")

    if revenue is not None and expenses is not None:
        profit = revenue - expenses
        insights["profit"] = profit
        insights["making_money"] = profit > 0
        insights["expense_ratio"] = expenses / revenue if revenue else 0

    if "profit_series" in model and len(model["profit_series"]) > 1:
        p = model["profit_series"]
        insights["profit_growth"] = p[-1] - p[-2]

    if "revenue_series" in model and len(model["revenue_series"]) > 1:
        r = model["revenue_series"]
        insights["revenue_growth"] = r[-1] - r[-2]

    if "expenses_series" in model and len(model["expenses_series"]) > 1:
        e = model["expenses_series"]
        insights["expense_growth"] = e[-1] - e[-2]

    if model.get("cash") is not None and model.get("liabilities") is not None:
        insights["healthy_balance_sheet"] = model["cash"] > model["liabilities"]

    return insights


# =====================================================
# =============== UI RENDERER =========================
# =====================================================

def render(model, insights, year_story=None):

    st.markdown("## Business Pulse")

    # ---------------- PROFIT ----------------
    st.markdown("### 💰 Am I Making Money?")

    if "profit" in insights:
        if insights["making_money"]:
            st.success(f"Yes — you made ${insights['profit']:,.0f}.")
        else:
            st.error(f"No — you lost ${abs(insights['profit']):,.0f}.")
    else:
        st.info("Not enough data to calculate profit.")

    # ---------------- GROWTH ----------------
    st.markdown("### 📈 Is My Business Growing?")

    if "revenue_growth" in insights:
        st.write(f"Revenue changed by ${insights['revenue_growth']:,.0f}")

    if "profit_growth" in insights:
        st.write(f"Profit changed by ${insights['profit_growth']:,.0f}")

    if "expense_growth" in insights:
        st.write(f"Expenses changed by ${insights['expense_growth']:,.0f}")

    # ---------------- MONEY FLOW ----------------
    st.markdown("### 💸 Where Is My Money Going?")

    if "expense_ratio" in insights:
        st.write(f"Expenses are {insights['expense_ratio']:.0%} of revenue.")

    # ---------------- HEALTH ----------------
    st.markdown("### 🏦 Is My Business Healthy?")

    if "healthy_balance_sheet" in insights:
        if insights["healthy_balance_sheet"]:
            st.success("Cash is stronger than liabilities.")
        else:
            st.warning("Liabilities exceed cash — watch debt.")

    # ---------------- WHAT STANDS OUT ----------------
    st.markdown("### 👀 What Stands Out?")

    if insights.get("making_money"):
        st.write("Business is currently profitable.")

    if insights.get("expense_growth", 0) > 0:
        st.write("Expenses are increasing.")

    if insights.get("revenue_growth", 0) > 0:
        st.write("Revenue is increasing.")

    # ---------------- YEAR STORY ----------------
    if year_story:
        st.markdown("## 📅 Year in Review")

        st.write(f"Total Revenue: ${year_story['total_revenue']:,.0f}")
        st.write(f"Total Expenses: ${year_story['total_expenses']:,.0f}")
        st.write(f"Total Profit: ${year_story['total_profit']:,.0f}")

        best = year_story["best_month"]
        worst = year_story["worst_month"]

        st.success(
            f"Best month: {best['period'].strftime('%b %Y')} "
            f"(${best['profit']:,.0f})"
        )

        st.warning(
            f"Worst month: {worst['period'].strftime('%b %Y')} "
            f"(${worst['profit']:,.0f})"
        )

        if year_story["profit_trend"] > 0:
            st.success("Profit improved over the year.")
        else:
            st.warning("Profit declined over the year.")

        if year_story["revenue_trend"] > 0:
            st.write("Revenue trended upward across the year.")


# =====================================================
# =============== RUN PIPELINE ========================
# =====================================================

text_data = parse_text_financials(text_input)

csv_df = None
year_story = None

if file:
    csv_df = pd.read_csv(file)
    csv_df.columns = csv_df.columns.str.lower().str.strip()

    if "period" in csv_df.columns:
        csv_df["period"] = pd.to_datetime(csv_df["period"], errors="coerce")
        csv_df = csv_df.sort_values("period")

        if len(csv_df) >= 2 and {"revenue", "expenses"}.issubset(csv_df.columns):
            year_story = build_year_story(csv_df)

model = build_model(text_data, csv_df)
insights = generate_insights(model)

render(model, insights, year_story)
