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
# INPUTS
# =====================================================

revenue = st.number_input("Revenue this month ($)", min_value=0.0)

expenses = st.number_input("Total expenses this month ($)", min_value=0.0)

profit_input = st.number_input(
    "Net profit (optional, leave 0 to calculate)",
    min_value=0.0
)

cash = st.number_input("Cash in bank ($)", min_value=0.0)

receivables = st.number_input("Money owed to you ($)", min_value=0.0)

liabilities = st.number_input("Total debt / liabilities ($)", min_value=0.0)

obligations = st.number_input("Big monthly obligations ($)", min_value=0.0)

business_type = st.text_input(
    "Business type (e.g. landscaping, trucking, consulting)"
)


# =====================================================
# CALCULATIONS
# =====================================================

profit = profit_input if profit_input > 0 else revenue - expenses


# =====================================================
# ANALYSIS ENGINE
# =====================================================

def analyze_profitability(profit):

    if profit > 0:
        return (
            "Your business is currently generating positive earnings. "
            "This indicates that your operations are producing more income "
            "than expenses, giving you a foundation to reinvest, reduce debt, "
            "or build reserves."
        )

    else:
        return (
            "Your business is currently operating at a loss, meaning expenses "
            "are exceeding revenue. If this trend continues, it may reduce "
            "available cash and limit your ability to invest or grow."
        )


def analyze_stability(cash, obligations):

    if obligations > 0:
        runway = cash / obligations
    else:
        runway = None


    if runway:

        if runway >= 12:
            return (
                f"Your current financial position provides a strong cushion. "
                f"Based on your reported obligations, your business has "
                f"approximately {runway:.0f} months of cash coverage if "
                f"conditions remain unchanged."
            )

        elif runway >= 6:
            return (
                f"Your business appears financially stable, with approximately "
                f"{runway:.0f} months of coverage based on current obligations. "
                f"Maintaining consistent cash flow will remain important."
            )

        else:
            return (
                f"Your available cash provides limited flexibility, with "
                f"approximately {runway:.0f} months of coverage based on "
                f"current obligations. Improving cash flow should be a priority."
            )

    else:

        return (
            "Your current cash position provides some financial flexibility, "
            "but additional information about monthly obligations would help "
            "determine how much operating cushion the business has."
        )


def analyze_obligations(liabilities, cash):

    if liabilities == 0:
        return (
            "Your business currently has no reported liabilities, which "
            "reduces financial pressure and provides additional flexibility."
        )

    ratio = liabilities / cash if cash > 0 else None


    if ratio and ratio < 1:

        return (
            "Your obligations appear manageable based on your current "
            "financial position. Your available resources provide a cushion "
            "against short-term financial pressure."
        )

    elif ratio and ratio < 3:

        return (
            "Your obligations appear manageable, but debt levels deserve "
            "ongoing attention. Maintaining consistent cash flow will help "
            "ensure these commitments remain comfortable."
        )

    else:

        return (
            "Your current obligations may create financial pressure if cash "
            "flow slows. Reducing liabilities or strengthening available cash "
            "could improve financial flexibility."
        )


def overall_health(profit, cash, liabilities):

    if profit > 0 and cash > liabilities:
        return "Stable"

    elif profit > 0:
        return "Watch"

    else:
        return "Needs Attention"



# =====================================================
# OUTPUT
# =====================================================

health = overall_health(profit, cash, liabilities)

st.header(f"Overall Financial Health: {health}")

if health == "Stable":

    st.write(
        "Your business appears financially healthy. You are generating profit "
        "and maintaining financial flexibility, which helps you handle "
        "obligations and unexpected expenses. The main opportunity is making "
        "sure your resources are being used effectively to support future growth."
    )

elif health == "Watch":

    st.write(
        "Your business shows positive signs, but some areas deserve attention. "
        "While operations may be generating profit, strengthening your financial "
        "position can provide more flexibility and reduce future risk."
    )

else:

    st.write(
        "Your business may be experiencing financial pressure. Reviewing "
        "profitability, cash flow, and obligations can help identify the areas "
        "that need attention first."
    )


st.header("Profitability")

st.write(analyze_profitability(profit))


st.header("Financial Stability")

st.write(analyze_stability(cash, obligations))


st.header("Obligations")

st.write(analyze_obligations(liabilities, cash))


st.header("Recommended Focus")

if profit > 0 and cash > liabilities:

    st.write(
        "Continue protecting profitability while evaluating whether available "
        "resources could be used to accelerate growth, reduce liabilities, "
        "or strengthen long-term financial health."
    )

elif profit > 0:

    st.write(
        "Focus on maintaining profitability while improving cash reserves "
        "and monitoring financial commitments."
    )

else:

    st.write(
        "Prioritize improving profitability and cash flow before taking on "
        "additional financial commitments."
    )


# =====================================================
# FEEDBACK
# =====================================================

st.divider()

st.subheader("Feedback")

feedback_text = st.text_area(
    "What should Business Pulse tell you that it didn’t?"
)

if st.button("Send Feedback"):

    if feedback_text.strip():

        st.session_state.feedback.append(feedback_text)

        st.success("Thanks — feedback saved!")

    else:

        st.warning("Please write something first.")


# =====================================================
# ADMIN
# =====================================================

if st.checkbox("Admin: View Feedback"):

    st.subheader("Collected Feedback")

    if not st.session_state.feedback:

        st.write("No feedback yet.")

    else:

        for i, f in enumerate(st.session_state.feedback, 1):
            st.write(f"{i}. {f}")


st.link_button(
    "Give Feedback",
    "https://forms.gle/12KE3QUUvvRBNJK36"
)
