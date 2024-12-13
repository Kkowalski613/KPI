import streamlit as st
import openai
import os
import io
import csv
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def explain_kpi(prompt_content):
    prompt = f"""
    You are an expert on KPIs. Consider the following KPI configuration and pilot phase details:
    {prompt_content}
    Provide a thorough explanation of what each KPI measures, how it can be used, and strict guidelines for its use.
    """
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"

def main():
    st.title("KPI Creation Kit")
    st.write("Welcome to the KPI Creation Kit! This tool helps you define key metrics for your pilot phases.")

    # Step 1: Survey
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
    target_audience = st.text_input("Describe your target audience")
    sell_to_audience = st.radio("Do you already sell other products/services to this audience?", ["Yes", "No"])
    offering_type = st.selectbox("What are you offering?", [
        "Physical product",
        "Digital app",
        "SaaS",
        "Service",
        "Hybrid physical/digital product",
        "Subscription-based product",
        "Other",
    ])
    business_goal = st.selectbox("Primary business goal:", [
        "Revenue growth",
        "Improved profitability",
        "Market share expansion",
        "Customer acquisition",
        "Brand loyalty/engagement",
        "Sustainability or ESG-related goals",
        "Other",
    ])
    benefit_statement = st.text_input("What problem does your offer solve?")
    timeframe = st.selectbox("Timeframe for success:", ["1-3 months", "3-6 months", "6-12 months", "12+ months"])
    budget = st.selectbox("Approximate budget:", [
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

    if st.button("Generate Insights"):
        st.header("Step 2: Insights")
        
        phases = ["Proof of Concept (POC)", "Closed Beta", "Public MVP"]
        selected_phase = st.selectbox("Select a phase to focus on:", phases, index=phases.index(pilot_phase))

        # Show phase-specific insights
        st.markdown("### Phase-Specific KPIs and Insights")
        if selected_phase == "Proof of Concept (POC)":
            generate_poc_outputs(industry, product_audience, offering_type, budget)
        elif selected_phase == "Closed Beta":
            generate_beta_outputs(product_audience, geography, target_audience)
        elif selected_phase == "Public MVP":
            generate_mvp_outputs(business_goal, timeframe, geography)

        # Integrate OpenAI Explanation
        st.markdown("### Detailed Explanation from OpenAI")
        selected_variables = f"""
        Industry: {industry}
        Product Audience: {product_audience}
        Target Geography: {geography}
        Target Audience: {target_audience}
        Already Selling to Audience: {sell_to_audience}
        Offering Type: {offering_type}
        Business Goal: {business_goal}
        Benefit Statement: {benefit_statement}
        Timeframe: {timeframe}
        Budget: {budget}
        Pilot Phase: {selected_phase}
        """

        if st.button("Explain These KPIs with OpenAI"):
            explanation = explain_kpi(selected_variables)
            st.subheader("KPI Explanation from OpenAI")
            st.write(explanation)

        # Allow user to save the KPI configuration as CSV or JSON for future use
        st.markdown("### Export KPI Configuration")
        kpi_data = {
            "Industry": industry,
            "Product_Audience": product_audience,
            "Geography": geography,
            "Target_Audience": target_audience,
            "Already_Selling": sell_to_audience,
            "Offering_Type": offering_type,
            "Business_Goal": business_goal,
            "Benefit_Statement": benefit_statement,
            "Timeframe": timeframe,
            "Budget": budget,
            "Pilot_Phase": selected_phase
        }

        # Export as CSV
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(kpi_data.keys())
        writer.writerow(kpi_data.values())
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download KPIs as CSV",
            data=csv_data,
            file_name="kpi_configuration.csv",
            mime="text/csv"
        )

        # Export as JSON
        json_data = json.dumps(kpi_data, indent=4)
        st.download_button(
            label="Download KPIs as JSON",
            data=json_data,
            file_name="kpi_configuration.json",
            mime="application/json"
        )

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
