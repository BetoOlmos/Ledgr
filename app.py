import streamlit as st

st.set_page_config(page_title="Business Pulse", layout="centered")

st.title("Business Pulse")
st.subheader("Quick Business Check-in")

# =====================================================
# SESSION STORAGE
# =====================================================

if "feedback" not in st.session_state:
    st.session_state.feedback = []

# =====================================================
# INPUTS (8 QUESTIONS)
# =====================================================

revenue = st.number_input("Revenue this month ($)", min_value=0.0)
expenses = st.number_input("Total expenses this month ($)", min_value=0.0)

profit_input = st.number_input("Net profit (optional, you can leave 0)", min_value=0.0)

cash = st.number_input("Cash in bank ($)", min_value=0.0)
receivables = st.number_input("Money owed to you ($)", min_value=0.0)

liabilities = st.number_input("Total debt / liabilities ($)", min_value=0.0)
obligations = st.number_input("Big monthly obligations ($)", min_value=0.0)

business_type = st.text_input("Business type (e.g. landscaping, trucking, consulting)")

# =====================================================
# AUTO CALC (if user didn't input profit)
# =====================================================

profit = profit_input if profit_input > 0 else (revenue - expenses)

# =====================================================
# INSIGHT ENGINE
# =====================================================

def level(value):
    if value is None:
        return "unknown"
    if value > 0:
        return "positive"
    return "negative"

# -----------------------------
# 1. MAKING MONEY
# -----------------------------

st.header("1. Am I making money?")

st.write(f"Profit: ${profit:,.0f}")

if profit > 0:
    st.success("Yes — your business is generating profit.")
else:
    st.error("No — your expenses are exceeding your revenue.")

# -----------------------------
# 2. FINANCIAL STABILITY
# -----------------------------

st.header("2. Am I financially stable right now?")

st.write(f"Cash: ${cash:,.0f}")
st.write(f"Receivables: ${receivables:,.0f}")

if cash > 0 and cash > expenses:
    st.success("Your cash position looks stable.")
elif cash > 0:
    st.warning("You have cash, but it may be tight relative to expenses.")
else:
    st.error("Cash position looks weak.")

# -----------------------------
# 3. DEBT PRESSURE
# -----------------------------

st.header("3. Can I handle my obligations?")

st.write(f"Liabilities: ${liabilities:,.0f}")
st.write(f"Monthly obligations: ${obligations:,.0f}")

if liabilities < cash:
    st.success("Debt level looks manageable compared to cash.")
else:
    st.warning("Debt may be putting pressure on your cash position.")

# =====================================================
# FEEDBACK SECTION
# =====================================================

st.divider()
st.subheader("Feedback")

st.write("Tell us what Business Pulse is missing or what would make it more useful:")

st.link_button(
    "Give Feedback",
    "https://forms.gle/12KE3QUUvvRBNJK36"
)
