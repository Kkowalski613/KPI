import streamlit as st

def main():
    # Title and Description
    st.title("KPI Creation Kit")
    st.write("Welcome to the KPI Creation Kit! This tool helps you define the key metrics and benchmarks for your pilot across different phases: POC, Closed Beta, and Public MVP.")

    # Intake Survey
    st.header("Step 1: Survey")

    industry = st.selectbox("What industry are you in?", [
        "Manufacturing",
        "Retail",
        "Technology",
        "Healthcare",
        "Transportation & Logistics",
        "Marketing & Advertising",
        "Finance & Insurance",
        "Consumer Goods",
        "Education",
        "Government & Public Sector",
        "Energy & Utilities",
        "Hospitality & Travel",
        "Other (Please Specify)",
    ])

    product_audience = st.selectbox("What is your product audience?", ["B2B", "B2C", "B2B2C", "Internal", "Other"])
    geography = st.selectbox("What is your target launch geography?", ["Local", "Regional", "National", "Global", "Other"])
    target_audience = st.text_input("In one phrase, describe your target audience (e.g., small business owners, millennial travelers)")
    sell_to_audience = st.radio("Do you already sell other products/services to your target audience?", ["Yes", "No"])
    offering_type = st.selectbox("What are you offering?", [
        "Physical product",
        "Digital app",
        "SaaS",
        "Service",
        "Hybrid physical/digital product",
        "Subscription-based product",
        "Other",
    ])
    business_goal = st.selectbox("What is your primary business goal?", [
        "Revenue growth",
        "Improved profitability",
        "Market share expansion",
        "Customer acquisition",
        "Brand loyalty/engagement",
        "Sustainability or ESG-related goals",
        "Other",
    ])
    benefit_statement = st.text_input("What problem is your offer trying to solve?")
    timeframe = st.selectbox("When do you need to see success by?", ["1-3 months", "3-6 months", "6-12 months", "12+ months"])
    budget = st.selectbox("What’s your approximate budget for launching and running the pilot?", [
        "Less than $1m",
        "$1m–$5m",
        "$5m–$10m",
        "$10m–$20m",
        "> $20m",
    ])

    pilot_phase = st.radio("Where are you in your pilot journey?", [
        "Proof of Concept (POC)",
        "Closed Beta",
        "Public MVP",
    ])

    # Generate Outputs
    if st.button("Generate Insights"):
        st.header("Step 2: Insights")
        
        phases = ["Proof of Concept (POC)", "Closed Beta", "Public MVP"]
        selected_phase = st.selectbox("Select a phase to focus on:", phases, index=phases.index(pilot_phase))

        # Phase Outputs
        if selected_phase == "Proof of Concept (POC)":
            generate_poc_outputs(industry, product_audience, offering_type, budget)
        elif selected_phase == "Closed Beta":
            generate_beta_outputs(product_audience, geography, target_audience)
        elif selected_phase == "Public MVP":
            generate_mvp_outputs(business_goal, timeframe, geography)


def generate_poc_outputs(industry, product_audience, offering_type, budget):
    st.subheader("Proof of Concept (POC) Phase")
    st.write("**Primary Objective:** Validate feasibility and core value proposition.")
    st.write("**Top 3 KPIs:**")
    st.write("1. Feasibility success rate (e.g., technical or operational success)")
    st.write("2. Preliminary user interest or intent to adopt")
    st.write("3. Cost-to-benefit ratio of prototype execution")
    st.write("**Benchmarks:** Industry-specific adoption or feasibility success rates.")
    st.write("**Risk Radar:** High R&D costs, lack of internal alignment, or unclear value propositions.")
    st.write(f"**Sources:** Data sourced from industry reports and case studies in the {industry} sector.")


def generate_beta_outputs(product_audience, geography, target_audience):
    st.subheader("Closed Beta Phase")
    st.write("**Primary Objective:** Refine the offer based on real user feedback.")
    st.write("**Top 3 KPIs:**")
    st.write("1. User satisfaction score (e.g., NPS or CSAT)")
    st.write("2. Feature adoption rate (by core audience)")
    st.write("3. Bug or issue resolution time")
    st.write("**Benchmarks:** Industry averages for closed beta adoption and satisfaction rates.")
    st.write(f"**Risk Radar:** Challenges in feedback collection or representative user selection for {product_audience} in {geography}.")
    st.write(f"**Sources:** Feedback analysis from successful beta launches for similar audiences like {target_audience}.")


def generate_mvp_outputs(business_goal, timeframe, geography):
    st.subheader("Public MVP Phase")
    st.write("**Primary Objective:** Achieve initial market adoption and validate scalability.")
    st.write("**Top 3 KPIs:**")
    st.write("1. Market adoption rate (e.g., % of target audience using the MVP)")
    st.write("2. Revenue or profitability (aligned with primary business goal)")
    st.write(f"3. Retention rate over initial time period ({timeframe})")
    st.write("**Benchmarks:** Market penetration rates and revenue targets for public MVPs in similar geographies.")
    st.write(f"**Risk Radar:** Scaling challenges, regulatory issues in {geography}, or failure to meet {business_goal} expectations.")
    st.write("**Sources:** Market analysis and benchmark studies.")


if __name__ == "__main__":
    main()
