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


import re

def find_value(text_lines, keyword):
    for line in text_lines:
        l = line.lower()

        if keyword in l:

            # find all numbers in line
            nums = re.findall(r"-?\$?[\d,]+\.?\d*", line)

            if nums:
                raw = nums[-1]

                return float(
                    raw.replace("$", "")
                       .replace(",", "")
                )

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
        st.error("Please upload both Profit & Loss and Balance Sheet CSV files.")
        st.stop()

    try:

        # =====================================================
        # READ FILES AS TEXT (IMPORTANT FIX)
        # =====================================================

        pnl_lines = pnl_file.getvalue().decode("utf-8", errors="ignore").split("\n")
        bs_lines = bs_file.getvalue().decode("utf-8", errors="ignore").split("\n")

        # =====================================================
        # VALUE EXTRACTOR
        # =====================================================

        def find_value(lines, keyword):
            for line in lines:
                l = line.lower()

                if keyword in l:

                    nums = re.findall(r"-?\$?[\d,]+\.?\d*", line)

                    if nums:
                        raw = nums[-1]
                        try:
                            return float(
                                raw.replace("$", "").replace(",", "")
                            )
                        except:
                            pass

            return None

        # =====================================================
        # P&L EXTRACTION (QBO SAFE KEYS)
        # =====================================================

        revenue = find_value(pnl_lines, "total revenue")
        expenses = find_value(pnl_lines, "total expenses")
        profit = find_value(pnl_lines, "net income")

        # fallback for QBO variants
        if profit is None:
            profit = find_value(pnl_lines, "net operating income")

        # =====================================================
        # BALANCE SHEET EXTRACTION
        # =====================================================

        cash = find_value(bs_lines, "cash")
        ar = find_value(bs_lines, "accounts receivable")
        liabilities = find_value(bs_lines, "total liabilities")

        # =====================================================
        # SIMPLE BUSINESS STATE
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
        st.write("Profit reflects revenue minus expenses during the period.")

        st.header("Growth")
        st.write("What Happened")
        st.write(f"Revenue: {fmt(revenue)}")

        st.write("Why")
        st.write("Revenue represents total sales activity for the period.")

        st.header("Expenses")
        st.write("What Happened")
        st.write(f"Expenses: {fmt(expenses)}")

        st.write("Why")
        st.write("Expenses reduce the profit retained by the business.")

        st.header("Cash Position")
        st.write("What Happened")
        st.write(f"Cash: {fmt(cash)}")
        st.write(f"Accounts Receivable: {fmt(ar)}")
        st.write(f"Liabilities: {fmt(liabilities)}")

        st.write("Why")
        st.write("Cash is available funds, receivables are unpaid invoices, and liabilities are obligations.")

    except Exception as e:
        st.error(f"Error processing files: {e}")
