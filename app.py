import streamlit as st
import pandas as pd

st.set_page_config(page_title="Business Pulse")

st.title("Business Pulse")

# =====================================================
# HELPERS
# =====================================================

def fmt(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}"


def find_value(df, keywords):
    for _, row in df.iterrows():

        row_text = " ".join(str(x).lower() for x in row)

        for keyword in keywords:
            if keyword in row_text:

                numbers = []

                for cell in row:
                    try:
                        value = float(
                            str(cell)
                            .replace("$", "")
                            .replace(",", "")
                            .replace("(", "-")
                            .replace(")", "")
                        )
                        numbers.append(value)
                    except:
                        pass

                if numbers:
                    return numbers[-1]

    return None


# =====================================================
# FILE UPLOADS
# =====================================================

pnl_file = st.file_uploader(
    "Upload Profit & Loss CSV",
    type=["csv"]
)

bs_file = st.file_uploader(
    "Upload Balance Sheet CSV",
    type=["csv"]
)

generate = st.button("Generate Business Pulse")

# =====================================================
# RUN
# =====================================================

if generate:

    if pnl_file is None or bs_file is None:
        st.error("Please upload both CSV files.")
        st.stop()

    try:

        pnl = pd.read_csv(pnl_file)
        bs = pd.read_csv(bs_file)

        revenue = find_value(
            pnl,
            ["revenue", "sales", "income"]
        )

        expenses = find_value(
            pnl,
            ["expense", "expenses"]
        )

        profit = find_value(
            pnl,
            ["net profit", "net income", "profit"]
        )

        cash = find_value(
            bs,
            ["cash"]
        )

        ar = find_value(
            bs,
            ["accounts receivable", "receivable"]
        )

        liabilities = find_value(
            bs,
            ["total liabilities", "liabilities"]
        )

        # =================================================
        # BUSINESS SNAPSHOT
        # =================================================

        overall = "stable"

        if profit is not None and profit < 0:
            overall = "under pressure"

        elif profit is not None and profit > 0:
            overall = "growing"

        snapshot = (
            f"Revenue was {fmt(revenue)} and profit was {fmt(profit)}. "
            f"Cash is {fmt(cash)} and accounts receivable are {fmt(ar)}. "
            f"Overall, the business appears {overall}."
        )

        # =================================================
        # OUTPUT
        # =================================================

        st.header("Business Snapshot")
        st.write(snapshot)

        st.header("Profitability")

        st.write("### What Happened")
        st.write(f"Revenue: {fmt(revenue)}")
        st.write(f"Profit: {fmt(profit)}")

        st.write("### Why")
        if profit is not None and profit > 0:
            st.write(
                "The business generated positive profit during the period."
            )
        else:
            st.write(
                "Profitability was impacted by expenses relative to revenue."
            )

        st.header("Growth")

        st.write("### What Happened")
        st.write(f"Revenue: {fmt(revenue)}")

        st.write("### Why")
        st.write(
            "Revenue reflects sales activity during the selected period."
        )

        st.header("Expenses")

        st.write("### What Happened")
        st.write(f"Expenses: {fmt(expenses)}")

        st.write("### Why")
        st.write(
            "Expenses reduced the profit retained by the business."
        )

        st.header("Cash Position")

        st.write("### What Happened")
        st.write(f"Cash: {fmt(cash)}")
        st.write(f"Accounts Receivable: {fmt(ar)}")
        st.write(f"Liabilities: {fmt(liabilities)}")

        st.write("### Why")
        st.write(
            "Cash represents available funds while receivables are amounts still owed to the business."
        )

    except Exception as e:
        st.error(f"Error reading files: {e}")
