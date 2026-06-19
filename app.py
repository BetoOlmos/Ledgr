import streamlit as st
import pandas as pd
import io

# =====================================================
# CONFIG & EXECUTIVE PREMIUM TYPOGRAPHY
# =====================================================
st.set_page_config(page_title="Business Pulse Engine", layout="centered")

st.markdown("""
    <style>
        @import url('https://googleapis.com');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FAFAFA; }
        
        .brief-header { margin-bottom: 30px; border-bottom: 1px solid #E2E8F0; padding-bottom: 20px; }
        .brief-title { font-size: 32px; font-weight: 700; color: #0F172A; letter-spacing: -0.75px; }
        .brief-subtitle { font-size: 15px; color: #64748B; margin-top: 6px; }
        
        .section-heading { font-size: 20px; font-weight: 700; color: #0F172A; margin: 30px 0 15px 0; letter-spacing: -0.3px; }
        
        /* Snapshot Scorecard Grid */
        .snapshot-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 25px; }
        .snapshot-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
        .snapshot-label { font-size: 13px; font-weight: 500; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; }
        .snapshot-value { font-size: 26px; font-weight: 700; color: #0F172A; margin-top: 4px; }
        .snapshot-subtext { font-size: 13px; color: #475569; margin-top: 6px; }
        
        /* Live Insight Memo Blocks */
        .ratio-container { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 24px; margin-bottom: 20px; }
        .ratio-metric-line { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #2563EB; margin-bottom: 8px; }
        .ratio-question { font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 12px; }
        .ratio-answer { font-size: 15px; color: #334155; line-height: 1.6; margin-bottom: 14px; }
        .ratio-why { font-size: 14px; color: #475569; background-color: #F8FAFC; border-left: 3px solid #10B981; padding: 12px 16px; border-radius: 0 4px 4px 0; }
        .ratio-why-down { border-left-color: #EF4444; }
        .ratio-why-neutral { border-left-color: #64748B; }
        
        .text-muted { color: #64748B; font-size: 13px; }
    </style>
""", unsafe_allowed_html=True)

# =====================================================
# REAL-WORLD ACCOUNTING EXPORT PARSER
# =====================================================
def clean_numeric_cell(val):
    """Safely extracts a float value from noisy accounting cell strings."""
    try:
        if pd.isna(val) or val == "":
            return 0.0
        s = str(val).strip().replace('$', '').replace(',', '')
        if '(' in s and ')' in s:
            s = '-' + s.replace('(', '').replace(')', '')
        s = s.split()[0]  # Remove trailing text inside cells
        return float(s)
    except:
        return 0.0

def parse_accounting_csv(file_obj, keywords):
    """
    Highly robust extraction engine mapping QBO/Xero side row labels 
    and matching column timelines dynamically.
    """
    try:
        # Step 1: Read raw strings to map columns and find header row
        raw_text = file_obj.getvalue().decode("utf-8")
        lines = [line.split(',') for line in raw_text.split('\n') if line.strip()]
        
        header_row_idx = None
        period_names = []
        
        # Look for the header line that houses the monthly breakdown names
        for idx, cells in enumerate(lines):
            joined = " ".join([c.lower() for c in cells])
            if any(m in joined for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "total"]):
                header_row_idx = idx
                # Keep any column header that isn't empty or labeled as account descriptive text
                period_names = [c.strip() for c in cells if c.strip() and not any(x in c.lower() for x in ["account", "description", "row", "label"])]
                break

        if header_row_idx is None:
            return None

        # Step 2: Read dataframe cleanly starting from the detected header row
        file_obj.seek(0)
        df = pd.read_csv(file_obj, skiprows=header_row_idx).fillna("")
        df.columns = [str(c).strip() for c in df.columns]
        
        # Clean up the first identifier text column
        label_col = df.columns[0]
        df[label_col] = df[label_col].astype(str).str.lower().str.strip()
        
        # Match data columns to our clean period strings
        valid_data_cols = [c for c in df.columns if c in period_names or any(p in c for p in period_names)]
        
        # Build dictionary map: { period_name: extracted_float_value }
        timeline_data = {col: 0.0 for col in valid_data_cols}
        
        for index, row in df.iterrows():
            row_label = str(row[label_col])
            # Strict match on structural summary keywords
            if any(kw in row_label for kw in keywords):
                for col in valid_data_cols:
                    extracted_num = clean_numeric_cell(row[col])
                    if extracted_num != 0.0:
                        timeline_data[col] = extracted_num
                break # Take the first high-level row totals group matched
                
        return timeline_data
    except Exception as e:
        return None

# =====================================================
# SMART ADVISORY KNOWLEDGE LIBRARY (Live Rules Engine)
# =====================================================
def run_live_pulse_library(current, prior):
    r, p, c, e, liab, ar = current["revenue"], current["profit"], current["cash"], current["expenses"], current["liabilities"], current["ar"]
    pr, pp, pc, pe, pliab, par = prior.get("revenue", 0), prior.get("profit", 0), prior.get("cash", 0), prior.get("expenses", 0), prior.get("liabilities", 0), prior.get("ar", 0)

    margin = (p / r * 100) if r else 0
    prior_margin = (pp / pr * 100) if pr else 0
    runway = (c / (e / 12)) if e else 0
    current_ratio = (c / liab) if liab else 0
    prior_ratio = (pc / pliab) if pliab else 0

    # 1. BILL-PAY STATUS
    r1_class = "ratio-why-neutral"
    if current_ratio >= 1.5:
        r1_ans = f"Yes. You hold ${c:,.0f} in liquid operating bank capital against ${liab:,.0f} in upcoming liabilities. You possess ${current_ratio:.2f} for every $1.00 of bills coming due."
        if current_ratio > prior_ratio and prior_ratio > 0:
            r1_class = "ratio-why"
            r1_why = f"Why it changed: Your bill-paying cushion improved from ${prior_ratio:.2f} last period. This happened because you reduced short-term liabilities by ${pliab - liab:,.0f}, wiping out immediate vendor debts."
        else:
            r1_why = "Why it changed: Your bill-paying balance remains steady. Your cash generation is keeping clear pace with operational liabilities."
    else:
        r1_ans = f"No, it will be tight. You have ${current_ratio:.2f} available for every $1.00 of liabilities coming due. Total debt outstanding is ${liab:,.0f} against ${c:,.0f} in available cash."
        r1_class = "ratio-why-down"
        if current_ratio < prior_ratio:
            r1_why = f"Why it changed: This indicator dropped from ${prior_ratio:.2f} last period. This happened because your accounts payable crept up by ${liab - pliab:,.0f}, outpacing your cash reserves."
        else:
            r1_why = "Why it changed: Your working capital ratio remains restricted. Immediate revenue needs to be prioritized to clear pending short-term vendor invoices."

    # 2. TRAPPED WEALTH STATUS
    r2_class = "ratio-why-neutral"
    if ar > 0:
        r2_ans = f"Your cash is trapped in your clients' bank accounts. You currently hold ${ar:,.0f} in unpaid customer invoices that have passed their standard settlement timelines."
        if ar > par and par > 0:
            r2_class = "ratio-why-down"
            r2_why = f"Why it changed: This timeline stretched this period, locking up an extra ${ar - par:,.0f} in working capital compared to last month. This delay is what is causing your bank balance to feel lower."
        else:
            r2_class = "ratio-why"
            r2_why = f"Why it changed: Your customer collection trends are improving. You clawed back ${par - ar:,.0f} from outstanding balances, converting old invoices into real bank checking deposits."
    else:
        r2_ans = "Your invoicing pipelines are perfectly clear. All sales value has been converted into liquid cash tokens in your bank account."
        r2_why = "Why it changed: Upfront payment structures or immediate card processing systems are keeping your cash cycle clean."

    # 3. EFFICIENCY MARGIN TRENDS
    r3_class = "ratio-why-neutral"
    if margin >= 15:
        r3_ans = f"Yes, your business is highly efficient. You captured a solid {margin:.1f}% net profit margin, turning sales into ${p:,.0f} of real bottom-line take-home wealth."
        if margin > prior_margin and prior_margin > 0:
            r3_class = "ratio-why"
            r3_why = f"Why it changed: Your profit margin expanded from {prior_margin:.1f}% last period. Your operational efficiency increased because you grew top-line revenue without adding fixed overhead costs."
        else:
            r3_why = "Why it changed: Your bottom-line capture remains rock-solid, maintaining steady profitability across fulfillment delivery cycles."
    else:
        r3_ans = f"No, your growth is currently inefficient. Your net take-home margin compressed to {margin:.1f}%, leaving you with ${p:,.0f} in actual profit from ${r:,.0f} in gross sales volume."
        r3_class = "ratio-why-down"
        if margin < prior_margin:
