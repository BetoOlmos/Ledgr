import streamlit as st
import re

st.set_page_config(page_title="Business Pulse", layout="wide")

st.title("Business Pulse")

# =====================================================
# HELPERS
# =====================================================

def fmt(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}"


def find_value(lines, keywords):
    """
    Finds a number from a line that contains ANY keyword.
    Works for QuickBooks exports.
    """
    for line in lines:
        l = line.lower()

        if any(k in l for k in keywords):

            nums = re.findall(r"-?\$?[\d,]+\.?\d*", line)

            if nums:
                raw = nums[-1]

                try:
                    return float(
                        raw.replace("$", "").replace(",", "")
                    )
                except:
                    continue

    return None


# =====================================================
# UPLOADS
# =====================================================

pnl_file = st.file_uploader("Upload Profit & Loss CSV", type=["csv"])
bs_file = st.file_uploader("Upload Balance Sheet CSV", type=["csv"])

generate = st.button("Generate Business Pulse")


# =====================================================
# RUN
# =====================================================

if generate:

    if pnl_file is None or bs_file is None:
        st.error("Please upload both Profit & Loss and Balance Sheet CSV files.")
        st.stop()

    try:

        # =====================================================
        # READ FILES AS TEXT
        # =====================================================

        pnl_lines = pnl_file.getvalue().decode("utf-8", errors="ignore").split("\n")
        bs_lines = bs_file.getvalue().decode("utf-8", errors="ignore").split("\n")

        # =====================================================
        # P&L EXTRACTION
        # =====================================================

        revenue = find_value(pnl_lines, [
            "total revenue",
            "total income",
            "net sales",
            "sales"
        ])

        expenses = find_value(pnl_lines, [
            "total expenses",
            "expenses"
        ])

        profit = find_value(pnl_lines, [
            "net income",
            "net operating income"
        ])

        # =====================================================
        # BALANCE SHEET EXTRACTION
        # =====================================================

        cash = find_value(bs_lines, [
            "cash",
            "checking",
            "bank",
            "total bank",
            "cash and cash equivalents"
        ])

        ar = find_value(bs_lines, [
            "accounts receivable",
            "receivable"
        ])

        liabilities = find_value(bs_lines, [
            "total liabilities",
            "liabilities"
        ])

        # =====================================================
        # BUSINESS STATE
        # =====================================================

        overall = "stable"

        if profit is not None:
            if profit > 0:
                overall = "growing"
            elif profit < 0:
                overall = "under pressure"

        # =====================================================
        # BUSINESS SNAPSHOT
        # =====================================================

        snapshot = (
            f"Revenue was {fmt(revenue)} and profit was {fmt(profit)}. "
            f"Cash is {fmt(cash)} and accounts receivable are {fmt(ar)}. "
            f"Overall, the business appears {overall}."
        )

        # =====================================================
        # OUTPUT
        # =====================================================

        st.header("Business Snapshot")
        st.write(snapshot)

        st.header("Profitability")
        st.write("What Happened")
        st.write(f"Revenue: {fmt(revenue)}")
        st.write(f"Profit: {fmt(profit)}")

        st.write("Why")
        st.write("Profit is revenue minus expenses over the period.")

        st.header("Growth")
        st.write("What Happened")
        st.write(f"Revenue: {fmt(revenue)}")

        st.write("Why")
        st.write("Revenue reflects total sales activity during the period.")

        st.header("Expenses")
        st.write("What Happened")
        st.write(f"Expenses: {fmt(expenses)}")

        st.write("Why")
        st.write("Expenses reduce profit retained by the business.")

        st.header("Cash Position")
        st.write("What Happened")
        st.write(f"Cash: {fmt(cash)}")
        st.write(f"Accounts Receivable: {fmt(ar)}")
        st.write(f"Liabilities: {fmt(liabilities)}")

        st.write("Why")
        st.write("Cash is available funds, receivables are money owed, liabilities are obligations.")

    except Exception as e:
        st.error(f"Error processing files: {e}")
