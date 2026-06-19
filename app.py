import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pulse Engine", layout="centered")

UI_LAYOUT_CSS = """
<style>
    html, body { font-family: 'Inter', sans-serif; background-color: #FAFAFA; }
    .brief-header { margin-bottom: 30px; border-bottom: 1px solid #E2E8F0; padding-bottom: 20px; }
    .brief-title { font-size: 32px; font-weight: 700; color: #0F172A; }
    .section-heading { font-size: 20px; font-weight: 700; color: #0F172A; margin: 30px 0 15px 0; }
    .snapshot-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 25px; }
    .snapshot-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; }
    .snapshot-label { font-size: 13px; font-weight: 500; color: #64748B; text-transform: uppercase; }
    .snapshot-value { font-size: 26px; font-weight: 700; color: #0F172A; margin-top: 4px; }
    .ratio-container { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 24px; margin-bottom: 20px; }
    .ratio-metric-line { font-size: 13px; font-weight: 600; color: #2563EB; text-transform: uppercase; }
    .ratio-question { font-size: 18px; font-weight: 600; color: #0F172A; margin: 8px 0; }
    .ratio-why { font-size: 14px; color: #475569; background-color: #F8FAFC; border-left: 3px solid #10B981; padding: 12px 16px; }
    .ratio-why-down { border-left-color: #EF4444; }
    .ratio-why-neutral { border-left-color: #64748B; }
</style>
"""
st.html(UI_LAYOUT_CSS)

def clean_and_parse_value(raw_val):
    if pd.isna(raw_val) or str(raw_val).strip() == "":
        return 0.0
    try:
        clean_str = str(raw_val).strip().replace("$", "").replace(",", "")
        if "(" in clean_str and ")" in clean_str:
            clean_str = "-" + clean_str.replace("(", "").replace(")", "")
        return float(clean_str.split()[0])
    except:
        return 0.0

def load_financial_sheet(uploaded_file, target_keywords):
    try:
        raw_bytes = uploaded_file.getvalue().decode("utf-8")
        df = pd.read_csv(io.StringIO(raw_bytes), header=None).fillna("")
        header_row_idx = 0
        periods = []
        months_list = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "total"]
        for idx, row in df.iterrows():
            row_text = " ".join([str(cell).lower() for cell in row.values])
            if any(m in row_text for m in months_list):
                header_row_idx = idx
                periods = [str(c).strip() for c in row.values if str(c).strip() != "" and not any(x in str(c).lower() for x in ["account", "description", "label"])]
                break
        uploaded_file.seek(0)
        clean_df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode("utf-8")), skiprows=header_row_idx).fillna(0)
        clean_df.columns = [str(c).strip() for c in clean_df.columns]
        label_col_name = clean_df.columns[0]
        clean_df[label_col_name] = clean_df[label_col_name].astype(str).str.lower().str.strip()
        active_data_cols = [c for c in clean_df.columns if c in periods or any(p in c for p in periods)]
        extracted_timeline = {col: 0.0 for col in active_data_cols}
        for index, row in clean_df.iterrows():
            row_label = str(row[label_col_name])
            if any(kw in row_label for kw in target_keywords):
                for col in active_data_cols:
                    val = clean_and_parse_value(row[col])
                    if val != 0.0:
                        extracted_timeline[col] = val
                break
        return extracted_timeline
    except:
        return {}
def run_live_pulse_library(current, prior):
    r, p, c, e, liab, ar = current["revenue"], current["profit"], current["cash"], current["expenses"], current["liabilities"], current["ar"]
    pr, pp, pc, pe, pliab, par = prior.get("revenue", 0), prior.get("profit", 0), prior.get("cash", 0), prior.get("expenses", 0), prior.get("liabilities", 0), prior.get("ar", 0)
    margin = (p / r * 100) if r else 0
    p_margin = (pp / pr * 100) if pr else 0
    runway = (c / (e / 12)) if e else 0
    c_ratio = (c / liab) if liab else 0
    p_ratio = (pc / pliab) if pliab else 0
    r1_class = "ratio-why-neutral"
    if c_ratio >= 1.5:
        r1_ans = f"Yes. You hold ${c:,.0f} in capital against ${liab:,.0f} in liabilities. You have ${c_ratio:.2f} for every $1.00 of bills."
        if c_ratio > p_ratio and p_ratio > 0:
            r1_class = "ratio-why"
            r1_why = f"Why it changed: Your cushion improved from ${p_ratio:.2f} last period because you reduced liabilities by ${pliab - liab:,.0f}."
        else:
            r1_why = "Why it changed: Your bill-paying balance remains steady. Cash keeps pace with liabilities."
    else:
        r1_ans = f"No, tight. You have ${c_ratio:.2f} for every $1.00 of upcoming bills. Total debt is ${liab:,.0f} against ${c:,.0f} in cash."
        r1_class = "ratio-why-down"
        if c_ratio < p_ratio:
            r1_why = f"Why it changed: Dropped from ${p_ratio:.2f}. Your accounts payable grew by ${liab - pliab:,.0f}, outpacing your available cash reserves."
        else:
            r1_why = "Why it changed: Working capital ratio is restricted. Immediate revenue is needed to clear outstanding debt."
    r2_class = "ratio-why-neutral"
    if ar > 0:
        r2_ans = f"Your cash is trapped. You hold ${ar:,.0f} in unpaid customer invoices that have passed standard settlement timelines."
        if ar > par and par > 0:
            r2_class = "ratio-why-down"
            r2_why = f"Why it changed: Invoices grew by ${ar - par:,.0f} compared to last period. This delayed cash collection is making the bank account feel emptier."
        else:
            r2_class = "ratio-why"
            r2_why = f"Why it changed: Collection habits are improving. You clawed back ${par - ar:,.0f} from balances, turning invoices into real bank checking deposits."
    else:
        r2_ans = "Your invoicing pipelines are completely clear. All sales have been converted into liquid cash."
        r2_why = "Why it changed: Upfront payment structures keep your operational cash cycle perfectly clean."
    r3_class = "ratio-why-neutral"
    if margin >= 15:
        r3_ans = f"Yes, highly efficient. You captured a {margin:.1f}% net margin, turning sales into ${p:,.0f} of real take-home wealth."
        if margin > p_margin and p_margin > 0:
            r3_class = "ratio-why"
            r3_why = f"Why it changed: Expanded from {p_margin:.1f}% last period. Efficiency grew because you raised revenue without increasing your fixed overhead costs."
        else:
            r3_why = "Why it changed: Your bottom-line capture remains solid, maintaining steady returns across cycles."
    else:
        r3_ans = f"No, growth is inefficient. Net margin fell to {margin:.1f}%, leaving you with ${p:,.0f} in profit from a large ${r:,.0f} sales volume."
        r3_class = "ratio-why-down"
        if margin < p_margin:
            r3_why = f"Why it changed: Fell from {p_margin:.1f}% last period. Operating expenses increased by ${e - pe:,.0f}, directly cutting into your revenue gains."
        else:
            r3_why = "Why it changed: Conversion efficiency remains low. Fulfillment costs are taking too big a bite out of sales."
    return {
        "margin": margin, "runway": runway,
        "r1_ans": r1_ans, "r1_why": r1_why, "r1_class": r1_class,
        "r2_ans": r2_ans, "r2_why": r2_why, "r2_class": r2_class,
        "r3_ans": r3_ans, "r3_why": r3_why, "r3_class": r3_class
    }

st.markdown("<div class='brief-header'><div class='brief-title'>💼 Business Pulse Live</div></div>", unsafe_allowed_html=True)

col1, col2 = st.columns(2)
pl_file = col1.file_uploader("Upload Profit & Loss (CSV)", type=["csv"])
bs_file = col2.file_uploader("Upload Balance Sheet (CSV)", type=["csv"])

rev_time, exp_time, prof_time = {}, {}, {}
cash_time, ar_time, liab_time = {}, {}, {}

if pl_file and bs_file:
    rev_time = load_financial_sheet(pl_file, ["total revenue", "total income", "gross sales"]) or {}
    exp_time = load_financial_sheet(pl_file, ["total expense", "total operating expenses"]) or {}
    prof_time = load_financial_sheet(pl_file, ["net income", "net profit", "bottom line"]) or {}
    cash_time = load_financial_sheet(bs_file, ["cash and cash equivalents", "total bank accounts", "cash at bank", "checking"]) or {}
    ar_time = load_financial_sheet(bs_file, ["accounts receivable", "trade debtors"]) or {}
    liab_time = load_financial_sheet(bs_file, ["total current liabilities", "accounts payable"]) or {}
else:
    st.warning("⚠️ Running default sandbox playground simulation values.")
    rev_time = {"Jan": 110000.0, "Feb": 135000.0, "Mar": 150000.0}
    exp_time = {"Jan": 90000.0, "Feb": 115000.0, "Mar": 125000.0}
    prof_time = {"Jan": 20000.0, "Feb": 20000.0, "Mar": 25000.0}
    cash_time = {"Jan": 45000.0, "Feb": 32000.0, "Mar": 55000.0}
    ar_time = {"Jan": 15000.0, "Feb": 35000.0, "Mar": 42000.0}
    liab_time = {"Jan": 25000.0, "Feb": 28000.0, "Mar": 18000.0}

periods = list(rev_time.keys())

if periods:
    sel_p = st.selectbox("🎯 Choose a tracking period:", reversed(periods))
    idx = periods.index(sel_p)
    p_period = periods[idx - 1] if idx > 0 else None
    c_data = {
        "revenue": rev_time.get(sel_p, 0.0), "expenses": exp_time.get(sel_p, 0.0), "profit": prof_time.get(sel_p, 0.0),
        "cash": cash_time.get(sel_p, 0.0), "ar": ar_time.get(sel_p, 0.0), "liabilities": liab_time.get(sel_p, 0.0)
    }
    p_data = {}
    if p_period:
        p_data = {
            "revenue": rev_time.get(p_period, 0.0), "expenses": exp_time.get(p_period, 0.0), "profit": prof_time.get(p_period, 0.0),
            "cash": cash_time.get(p_period, 0.0), "ar": ar_time.get(p_period, 0.0), "liabilities": liab_time.get(p_period, 0.0)
        }
    res = run_live_pulse_library(c_data, p_data)
    st.markdown("<div class='section-heading'>I. CFO Snapshot</div>", unsafe_allowed_html=True)
    snap_html = f"""
    <div class="snapshot-grid">
        <div class="snapshot-card"><div class="snapshot-label">Total Revenue</div><div class="snapshot-value">${c_data['revenue']:,.0f}</div></div>
        <div class="snapshot-card"><div class="snapshot-label">Take-Home Profit</div><div class="snapshot-value">${c_data['profit']:,.0f}</div></div>
        <div class="snapshot-card"><div class="snapshot-label">Cash in Bank</div><div class="snapshot-value">${c_data['cash']:,.0f}</div></div>
        <div class="snapshot-card"><div class="snapshot-label">Safety Net</div><div class="snapshot-value">{res['runway']:.1f} Mo</div></div>
    </div>
    """
    st.markdown(snap_html, unsafe_allowed_html=True)
    st.markdown("<div class='section-heading'>II. Explanations</div>", unsafe_allowed_html=True)
    st.markdown(f"""
    <div class="ratio-container">
        <div class="ratio-metric-line">Liquidity Index</div>
        <div class="ratio-question">1. Can we pay upcoming bills?</div>
        <p>Answer: {res['r1_ans']}</p>
        <div class="ratio-why {res['r1_class']}">Reason: {res['r1_why']}</div>
    </div>
    <div class="ratio-container">
        <div class="ratio-metric-line">AR Velocity</div>
        <div class="ratio-question">2. Where is all our money?</div>
        <p>Answer: {res['r2_ans']}</p>
        <div class="ratio-why {res['r2_class']}">Reason: {res['r2_why']}</div>
    </div>
    <div class="ratio-container">
        <div class="ratio-metric-line">Net Margin Conversion</div>
        <div class="ratio-question">3. Are we making real wealth?</div>
        <p>Answer: {res['r3_ans']}</p>
        <div class="ratio-why {res['r3_class']}">Reason: {res['r3_why']}</div>
    </div>
    """, unsafe_allowed_html=True)
