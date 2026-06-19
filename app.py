import io
import pandas as pd
import streamlit as st
st.set_page_config(
page_title="Pulse Engine",
layout="centered",
)
st.markdown(
"""

html, body {
font-family: 'Inter', sans-serif;
background-color: #FAFAFA;
}
.brief-header {
margin-bottom: 30px;
border-bottom: 1px solid #E2E8F0;
padding-bottom: 20px;
}
.brief-title {
font-size: 32px;
font-weight: 700;
color: #0F172A;
}
.section-heading {
font-size: 20px;
font-weight: 700;
color: #0F172A;
margin: 30px 0 15px 0;
}
.snapshot-grid {
display: grid;
grid-template-columns: repeat(2, 1fr);
gap: 16px;
margin-bottom: 25px;
}
.snapshot-card {
background: #FFFFFF;
border: 1px solid #E2E8F0;
border-radius: 8px;
padding: 16px 20px;
}
.snapshot-label {
font-size: 13px;
font-weight: 500;
color: #64748B;
text-transform: uppercase;
}
.snapshot-value {
font-size: 26px;
font-weight: 700;
color: #0F172A;
margin-top: 4px;
}
.ratio-container {
background-color: #FFFFFF;
border: 1px solid #E2E8F0;
border-radius: 8px;
padding: 24px;
margin-bottom: 20px;
}
.ratio-metric-line {
font-size: 13px;
font-weight: 600;
color: #2563EB;
text-transform: uppercase;
}
.ratio-question {
font-size: 18px;
font-weight: 600;
color: #0F172A;
margin: 8px 0;
}
.ratio-why {
font-size: 14px;
color: #475569;
background-color: #F8FAFC;
border-left: 3px solid #10B981;
padding: 12px 16px;
}
.ratio-why-down {
border-left-color: #EF4444;
}
.ratio-why-neutral {
border-left-color: #64748B;
}

""",
unsafe_allowed_html=True,
) [1]
def clean_numeric_cell(val):
if pd.isna(val) or val == "":
return 0.0
try:
s = str(val).strip()
s = s.replace("$", "")
s = s.replace(",", "")
if "(" in s and ")" in s:
s = "-" + s.replace("(", "").replace(")", "")
return float(s.split()[0])
except:
return 0.0
def parse_accounting_csv(file_obj, keywords):
try:
raw_text = file_obj.getvalue().decode("utf-8")
lines = [
line.split(",")
for line in raw_text.split("\n")
if line.strip()
]
h_idx = None
p_names = []
months = [
"jan", "feb", "mar", "apr", "may", "jun",
"jul", "aug", "sep", "oct", "nov", "dec", "total"
]
for idx, cells in enumerate(lines):
joined = " ".join([c.lower() for c in cells])
if any(m in joined for m in months):
h_idx = idx
p_names = [
c.strip()
for c in cells
if c.strip() and not any(
x in c.lower()
for x in ["account", "description", "row", "label"]
)
]
break
if h_idx is None:
return None
file_obj.seek(0)
df = pd.read_csv(file_obj, skiprows=h_idx).fillna("")
df.columns = [str(c).strip() for c in df.columns]
l_col = df.columns[0]
df[l_col] = df[l_col].astype(str).str.lower().str.strip()
v_cols = [
c for c in df.columns
if c in p_names or any(p in c for p in p_names)
]
t_data = {col: 0.0 for col in v_cols}
for index, row in df.iterrows():
row_label = str(row[l_col])
if any(kw in row_label for kw in keywords):
for col in v_cols:
num = clean_numeric_cell(row[col])
if num != 0.0:
t_data[col] = num
break
return t_data
except:
return None
def run_live_pulse_library(current, prior):
r = current["revenue"]
p = current["profit"]
c = current["cash"]
e = current["expenses"]
liab = current["liabilities"]
ar = current["ar"]
pr = prior.get("revenue", 0)
pp = prior.get("profit", 0)
pc = prior.get("cash", 0)
pe = prior.get("expenses", 0)
pliab = prior.get("liabilities", 0)
par = prior.get("ar", 0)
margin = (p / r * 100) if r else 0
p_margin = (pp / pr * 100) if pr else 0
runway = (c / (e / 12)) if e else 0
c_ratio = (c / liab) if liab else 0
p_ratio = (pc / pliab) if pliab else 0
r1_class = "ratio-why-neutral"
if c_ratio >= 1.5:
r1_ans = f"Yes. You hold ${c:,.0f} in capital against liab:,.0f in liabilities. You have {c_ratio:.2f} for every $1.00 of bills."
if c_ratio > p_ratio and p_ratio > 0:
r1_class = "ratio-why"
r1_why = f"Why it changed: Your cushion improved from \({p_ratio:.2f} last period because you reduced liabilities by\){pliab - liab:,.0f}."
else:
r1_why = "Why it changed: Your bill-paying balance remains steady. Cash keeps pace with liabilities."
else:
r1_ans = f"No, tight. You have ${c_ratio:.2f} for every $1.00 of upcoming bills. Total debt is liab:,.0f against {c:,.0f} in cash."
r1_class = "ratio-why-down"
if c_ratio < p_ratio:
r1_why = f"Why it changed: Dropped from \({p_ratio:.2f}. Your accounts payable grew by\){liab - pliab:,.0f}, outpacing your available cash reserves."
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
r3_ans = f"No, growth is inefficient. Net margin fell to {margin:.1f}%, leaving you with p:,.0f in profit from a large {r:,.0f} sales volume."
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
st.markdown(
"""

Business Pulse Live

""",
unsafe_allowed_html=True,
)
col1, col2 = st.columns(2)
pl_file = col1.file_uploader("Upload Profit & Loss (CSV)", type=["csv"])
bs_file = col2.file_uploader("Upload Balance Sheet (CSV)", type=["csv"])
rev_time, exp_time, prof_time = {}, {}, {}
cash_time, ar_time, liab_time = {}, {}, {}
if pl_file and bs_file:
rev_time = parse_accounting_csv(pl_file, ["total revenue", "total income", "gross sales"]) or {}
exp_time = parse_accounting_csv(pl_file, ["total expense", "total operating expenses"]) or {}
prof_time = parse_accounting_csv(pl_file, ["net income", "net profit", "bottom line"]) or {}
cash_time = parse_accounting_csv(bs_file, ["cash and cash equivalents", "total bank accounts"]) or {}
ar_time = parse_accounting_csv(bs_file, ["accounts receivable", "trade debtors"]) or {}
liab_time = parse_accounting_csv(bs_file, ["total current liabilities", "accounts payable"]) or {}
else:
rev_time = {"Jan": 110000.0, "Feb": 135000.0, "Mar": 150000.0}
exp_time = {"Jan": 90000.0, "Feb": 115000.0, "Mar": 125000.0}
prof_time = {"Jan": 20000.0, "Feb": 20000.0, "Mar": 25000.0}
cash_time = {"Jan": 45000.0, "Feb": 32000.0, "Mar": 55000.0}
ar_time = {"Jan": 15000.0, "Feb": 35000.0, "Mar": 42000.0}
liab_time = {"Jan": 25000.0, "Feb": 28000.0, "Mar": 18000.0}
periods = list(rev_time.keys())
if periods:
sel_p = st.selectbox("Choose a period:", reversed(periods))
idx = periods.index(sel_p)
p_period = periods[idx - 1] if idx > 0 else None
c_data = {
"revenue": rev_time.get(sel_p, 0.0),
"expenses": exp_time.get(sel_p, 0.0),
"profit": prof_time.get(sel_p, 0.0),
"cash": cash_time.get(sel_p, 0.0),
"ar": ar_time.get(sel_p, 0.0),
"liabilities": liab_time.get(sel_p, 0.0)
}
p_data = {}
if p_period:
p_data = {
"revenue": rev_time.get(p_period, 0.0),
"expenses": exp_time.get(p_period, 0.0),
"profit": prof_time.get(p_period, 0.0),
"cash": cash_time.get(p_period, 0.0),
"ar": ar_time.get(p_period, 0.0),
"liabilities": liab_time.get(p_period, 0.0)
}
res = run_live_pulse_library(c_data, p_data)
st.markdown("I. CFO Snapshot", unsafe_allowed_html=True)
snap_html = f"""


Total Revenue
${c_data['revenue']:,.0f}


Take-Home Profit
${c_data['profit']:,.0f}


Cash in Bank
${c_data['cash']:,.0f}


Safety Net
{res['runway']:.1f} Mo


"""
st.markdown(snap_html, unsafe_allowed_html=True)
st.markdown("II. Explanations", unsafe_allowed_html=True)
st.markdown(
f"""

Liquidity Index
1. Can we pay upcoming bills?
Answer: {res['r1_ans']}
Reason: {res['r1_why']}

""",
unsafe_allowed_html=True,
)
st.markdown(
f"""

AR Velocity
2. Where is all our money?
Answer: {res['r2_ans']}
Reason: {res['r2_why']}

""",
unsafe_allowed_html=True,
)
st.markdown(
f"""

Net Margin Conversion
3. Are we making real wealth?
Answer: {res['r3_ans']}
Reason: {res['r3_why']}

""",
unsafe_allowed_html=True,
)
