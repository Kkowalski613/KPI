import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import json
import openai
import re

# -------------------- Configuration --------------------

# Define benchmark ranges for KPIs based on industry
BENCHMARKS = {
    "Real Estate": {
        "User Engagement": {"base": 60, "growth": 5, "std_dev": 5},
        "Home Clicks": {"base": 1000, "growth": 200, "std_dev": 100},
        "Accounts Activated": {"base": 500, "growth": 50, "std_dev": 30},
        "Subscriptions Renewed": {"base": 400, "growth": 40, "std_dev": 25}
    },
    # Add other industries similarly
    "General": {
        "User Engagement": {"base": 50, "growth": 4, "std_dev": 4},
        "Home Clicks": {"base": 800, "growth": 150, "std_dev": 80},
        "Accounts Activated": {"base": 400, "growth": 40, "std_dev": 25},
        "Subscriptions Renewed": {"base": 300, "growth": 30, "std_dev": 20}
    }
}

# Initialize session state variables
if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False
st.session_state.kpi_suggestions = st.session_state.get("kpi_suggestions", {})
st.session_state.selected_kpis = st.session_state.get("selected_kpis", [])
st.session_state.kpi_data = st.session_state.get("kpi_data", {})
st.session_state.kpi_explanations = st.session_state.get("kpi_explanations", {})
st.session_state.phase_outputs = st.session_state.get("phase_outputs", {})

# -------------------- Export Functions --------------------

def export_kpis_csv(kpi_list):
    """Export KPIs as a CSV file."""
    df = pd.DataFrame(kpi_list)
    return df.to_csv(index=False).encode('utf-8')

def export_kpis_json(kpi_list):
    """Export KPIs as JSON file."""
    try:
        json_str = json.dumps(kpi_list, indent=4)
        return json_str.encode('utf-8')
    except TypeError as e:
        st.error(f"Error exporting KPIs to JSON: {e}")
        return b""

def export_kpis_text(kpi_list):
    """Export KPIs as a plain text file."""
    text_lines = []
    for kpi in kpi_list:
        text_lines.append(f"KPI: {kpi['name']}")
        text_lines.append(f"Description: {kpi['description']}")
        text_lines.append(f"Guidance: {kpi['guidance']}\n")
    return "\n".join(text_lines).encode('utf-8')

# -------------------- Plotting Function --------------------

def plot_kpi_chart(kpi_name, data_points):
    """Generate an interactive and enhanced trend chart for a specific KPI using Plotly."""
    # Ensure 'Time Period' is sorted
    data_points = data_points.sort_values('Time Period')

    # Calculate scenarios
    scenarios = {
        "Weak Scenario": data_points['Value'] * 0.8,
        "Medium Scenario": data_points['Value'],
        "High Scenario": data_points['Value'] * 1.2
    }

    # Create DataFrame for scenarios
    scenario_df = pd.DataFrame(scenarios, index=data_points['Time Period'])

    # Melt the DataFrame for Plotly
    melted_df = scenario_df.reset_index().melt(id_vars='Time Period', var_name='Scenario', value_name='Value')

    # Create the line chart
    fig = px.line(
        melted_df,
        x='Time Period',
        y='Value',
        color='Scenario',
        title=f"KPI: {kpi_name} - Scenarios",
        markers=True,
        labels={"Value": kpi_name}
    )

    # Update layout for better aesthetics
    fig.update_layout(
        xaxis_title="Time Period",
        yaxis_title=kpi_name,
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Update hover template for clarity
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y}"
    )

    # Customize the layout for better spacing and readability
    fig.update_layout(
        autosize=True,
        width=800,
        height=600
    )

    return fig

# -------------------- OpenAI Data Generation --------------------

def get_openai_api_key():
    try:
        return st.secrets["openai_api_key"]
    except KeyError:
        try:
            return st.secrets["openai"]["api_key"]
        except KeyError:
            st.error(
                "OpenAI API key not found. Please set `openai_api_key` or `openai.api_key` in Streamlit's secrets."
            )
            st.stop()

def generate_focused_fake_data(industry, product_audience, kpi_name, kpi_description):
    """
    Generate fake data based on Industry, Product Audience, and KPI using OpenAI.
    Returns a pandas DataFrame with 'Time Period' and 'Value'.
    """
    # Initialize OpenAI API key
    openai_api_key = get_openai_api_key()
    openai.api_key = openai_api_key
    
    # Define the number of time periods (e.g., months)
    time_periods = [f"Month {i}" for i in range(1, 13)]
    
    # Create a prompt for OpenAI to generate data
    prompt = (
        f"Generate a realistic set of monthly KPI values for the next 12 months based on the following details:\n\n"
        f"Industry: {industry}\n"
        f"Product Audience: {product_audience}\n"
        f"KPI Name: {kpi_name}\n"
        f"KPI Description: {kpi_description}\n\n"
        f"Assume the company operates similarly to Zillow. Provide the data in a JSON format with 'Time Period' and 'Value' keys."
    )
    
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates realistic KPI data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        # Extract the generated JSON
        generated_text = response.choices[0].message['content']
        
        # Attempt to parse the JSON
        try:
            generated_data = json.loads(generated_text)
        except json.JSONDecodeError:
            # If JSON is not properly formatted, extract JSON manually
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if json_match:
                generated_data = json.loads(json_match.group(0))
            else:
                st.error("Failed to parse generated data from OpenAI.")
                return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(generated_data)
        
        # Validate 'Time Period' and 'Value' columns
        if not {'Time Period', 'Value'}.issubset(df.columns):
            st.error("Generated data must contain 'Time Period' and 'Value' columns.")
            return pd.DataFrame()
        
        return df
    
    except openai.error.RateLimitError:
        st.error("OpenAI API rate limit exceeded. Please try again later.")
        return pd.DataFrame()
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

# -------------------- KPI Explanation Function --------------------

def explain_kpis(kpi_list):
    """
    Generates explanations for each KPI.
    """
    explanations = {}
    for kpi in kpi_list:
        explanations[kpi['name']] = f"{kpi['description']} ({kpi['guidance']})"
    return explanations

# -------------------- Pre-Defined KPIs per Phase --------------------

def get_predefined_kpis(phase, survey_responses):
    """
    Returns a list of practical KPIs based on the phase and survey responses.
    """
    industry = survey_responses.get("Industry", "General")
    product_audience = survey_responses.get("Product Audience", "General")
    
    predefined_kpis = {
        "POC": [
            {
                "name": "User Engagement",
                "description": "Measures the level of user interaction with the product during the POC phase.",
                "guidance": "Aim for ≥ 60% engagement rate."
            },
            {
                "name": "Home Clicks",
                "description": "Tracks the number of clicks on home listings within the platform.",
                "guidance": "Aim for ≥ 1000 clicks per month."
            },
            {
                "name": "Accounts Activated",
                "description": "Number of new user accounts activated during the POC phase.",
                "guidance": "Aim for ≥ 500 activations."
            }
        ],
        "Closed Beta": [
            {
                "name": "User Engagement",
                "description": "Measures the continued interaction of users with the product during the Closed Beta phase.",
                "guidance": "Aim for ≥ 70% engagement rate."
            },
            {
                "name": "Subscriptions Renewed",
                "description": "Tracks the number of user subscriptions that are renewed during the beta period.",
                "guidance": "Aim for ≥ 400 renewals."
            },
            {
                "name": "Home Clicks",
                "description": "Monitors the engagement with home listings within the platform.",
                "guidance": "Aim for ≥ 1200 clicks per month."
            }
        ],
        "Public MVP": [
            {
                "name": "User Engagement",
                "description": "Assessing user interaction and activity levels post-launch of the MVP.",
                "guidance": "Aim for ≥ 80% engagement rate."
            },
            {
                "name": "Subscriptions Renewed",
                "description": "Measures the retention of user subscriptions over time.",
                "guidance": "Aim for ≥ 500 renewals."
            },
            {
                "name": "Accounts Activated",
                "description": "Number of new user accounts activated after MVP launch.",
                "guidance": "Aim for ≥ 600 activations."
            }
        ]
    }
    
    return predefined_kpis.get(phase, [])

# -------------------- Survey Page --------------------

def survey_page():
    st.title("KPI Creation and Tracking Kit - Survey")

    st.markdown("""
    Please answer the following questions to help us tailor the KPI suggestions to your needs.
    """)

    with st.form("survey_form"):
        # Question 1
        st.markdown("### **1. What industry are you in?**")
        industry = st.selectbox("", [
            "Real Estate",
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
            "Other (open-ended)",
        ], key="industry_select")

        if industry == "Other (open-ended)":
            industry = st.text_input("Please specify your industry", key="industry_other")

        st.markdown("---")

        # Question 2
        st.markdown("### **2. What is your product audience?**")
        product_audience = st.selectbox("", [
            "B2B (Business-to-Business)",
            "B2C (Business-to-Consumer)",
            "B2B2C (Business-to-Business-to-Consumer)",
            "Internal (Employee-focused initiatives)",
            "Other (open-ended)",
        ], key="product_audience_select")

        if product_audience == "Other (open-ended)":
            product_audience = st.text_input("Please specify your product audience", key="product_audience_other")

        st.markdown("---")

        # Question 3
        st.markdown("### **3. What is your target launch geography or market?**")
        geography = st.selectbox("", [
            "Local (City or single region)",
            "Regional (Multiple regions within a country)",
            "National (Entire country)",
            "Global (Multiple countries)",
            "Other (open-ended)",
        ], key="geography_select")

        if geography == "Other (open-ended)":
            geography = st.text_input("Please specify your target launch geography", key="geography_other")

        st.markdown("---")

        # Question 4
        st.markdown("### **4. In one phrase, describe your target audience.**")
        target_audience = st.text_input("Provide a phrase (e.g., 'Small business owners', 'Millennial travelers')", key="target_audience")

        st.markdown("---")

        # Question 5
        st.markdown("### **5. Do you already sell other products or services to your target audience?**")
        sell_to_audience = st.radio("Do you already sell other products or services to your target audience?", ["Yes", "No"], key="sell_to_audience_radio")

        st.markdown("---")

        # Question 6
        st.markdown("### **6. What are you piloting?**")
        offering_type = st.selectbox("", [
            "Physical product",
            "Digital app",
            "SaaS (Software-as-a-Service)",
            "Service",
            "Hybrid physical/digital product",
            "Subscription-based product",
            "Other (open-ended)",
        ], key="offering_type_select")

        if offering_type == "Other (open-ended)":
            offering_type = st.text_input("Please specify what you are piloting", key="offering_type_other")

        st.markdown("---")

        # Question 7
        st.markdown("### **7. What is your primary business goal in launching this new offer?**")
        business_goal = st.selectbox("", [
            "Revenue growth",
            "Improved profitability",
            "Market share expansion",
            "Customer acquisition",
            "Brand loyalty/engagement",
            "Sustainability or ESG-related goals",
            "Other (open-ended)",
        ], key="business_goal_select")

        if business_goal == "Other (open-ended)":
            business_goal = st.text_input("Please specify your primary business goal", key="business_goal_other")

        st.markdown("---")

        # Question 8
        st.markdown("### **8. In one sentence, explain what customer problem your pilot is trying to solve.**")
        benefit_statement = st.text_area("Provide a sentence (e.g., 'Help small business owners manage their finances more effectively.')", key="benefit_statement")

        st.markdown("---")

        # Question 9
        st.markdown("### **9. When do you need to see success of your pilot by?**")
        timeframe = st.selectbox("", [
            "1–3 months",
            "3–6 months",
            "6–12 months",
            "12+ months",
            "I don't know yet",
        ], key="timeframe_select")

        st.markdown("---")

        # Question 10
        st.markdown("### **10. What’s your approximate budget for launching and running the pilot?**")
        budget = st.selectbox("", [
            "Less than $1m",
            "$1m–$5m",
            "$5m–$10m",
            "$10m–$20m",
            "Greater than $20m",
            "Other (open-ended)",
        ], key="budget_select")

        if budget == "Other (open-ended)":
            budget = st.text_input("Please specify your approximate budget", key="budget_other")

        st.markdown("---")

        # Submit Button
        submitted = st.form_submit_button("Submit Survey")
        if submitted:
            # Store survey responses in session state
            st.session_state.survey_responses = {
                "Industry": industry,
                "Product Audience": product_audience,
                "Geography": geography,
                "Target Audience": target_audience,
                "Existing Customer Base": sell_to_audience,
                "Offering Type": offering_type,
                "Business Goal": business_goal,
                "Benefit Statement": benefit_statement,
                "Timeframe": timeframe,
                "Budget": budget,
            }
            st.session_state.survey_completed = True
            st.success("Survey submitted successfully! Generating phase outputs...")

            # Generate phase outputs based on pre-defined templates
            phase_outputs = {}
            phases = ["POC", "Closed Beta", "Public MVP"]
            for phase in phases:
                kpis = get_predefined_kpis(phase, st.session_state.survey_responses)
                phase_outputs[phase] = {
                    "Primary Objective": f"Define the primary objective for the {phase} phase based on your survey inputs.",
                    "Top 3 KPIs": [kpi['name'] for kpi in kpis[:3]],
                    "Benchmarks/Targets": [kpi['guidance'] for kpi in kpis[:3]],
                    "Similar Companies’ Results": f"Provide examples of companies that have undertaken similar {phase} phases and their outcomes.",
                    "Additional Creative Outputs": f"Provide additional creative outputs tailored to the {phase} phase."
                }

                # Add Risk Radar for POC phase
                if phase == "POC":
                    phase_outputs[phase]["Risk Radar"] = f"Identify potential risks or failure points for the {phase} phase and suggest mitigation strategies."

            st.session_state.phase_outputs = phase_outputs
            # Store actual KPIs separately
            st.session_state.kpi_suggestions = {
                phase: get_predefined_kpis(phase, st.session_state.survey_responses)
                for phase in phases
            }
            # Generate explanations for all KPIs
            all_kpis = []
            for kpi_list in st.session_state.kpi_suggestions.values():
                all_kpis.extend(kpi_list)
            st.session_state.kpi_explanations = explain_kpis(all_kpis)
            st.success("Phase outputs generated successfully! You can now access the KPI tools.")

# -------------------- Main App Logic --------------------

def main():
    st.set_page_config(page_title="KPI Creation and Tracking Kit", layout="wide")

    if not st.session_state.survey_completed:
        survey_page()
    else:
        st.title("KPI Creation and Tracking Kit")
        st.write("Generate meaningful KPIs tailored to your pilot phase, understand them with detailed insights, and track their progress over time.")

        # Phase Selection
        st.markdown("### **Select a phase to focus on:**")
        phase = st.selectbox("", ["POC", "Closed Beta", "Public MVP"], index=0, key="phase_select")

        st.markdown("---")

        # Display Phase Outputs
        if phase in st.session_state.phase_outputs:
            st.markdown(f"## **{phase} Phase**")
            phase_info = st.session_state.phase_outputs[phase]
            st.markdown(f"**Primary Objective:** {phase_info['Primary Objective']}")
            st.markdown("**Top 3 KPIs:**")
            for kpi in phase_info["Top 3 KPIs"]:
                st.markdown(f"- {kpi}")
            st.markdown("**Benchmarks/Targets:**")
            for target in phase_info["Benchmarks/Targets"]:
                st.markdown(f"- {target}")
            st.markdown(f"**Similar Companies’ Results:** {phase_info['Similar Companies’ Results']}")
            st.markdown(f"**Additional Creative Outputs:** {phase_info['Additional Creative Outputs']}")
            
            # Display Risk Radar for POC phase
            if phase == "POC":
                st.markdown(f"**Risk Radar:** {phase_info['Risk Radar']}")

        st.markdown("---")

        # Display Suggested KPIs and Explanations
        if st.session_state.kpi_suggestions:
            st.subheader("Suggested KPIs")
            # Allow users to select KPIs
            kpi_options = [f"{kpi['name']}: {kpi['description']}" for kpi in st.session_state.kpi_suggestions.get(phase, [])]
            selected = st.multiselect(
                "Select KPIs you want to track:",
                options=kpi_options,
                key=f"kpi_multiselect_{phase}"
            )

            # Map selected options back to KPI structures
            selected_struct = []
            for sel in selected:
                kpi_name = sel.split(":")[0]
                for kpi in st.session_state.kpi_suggestions.get(phase, []):
                    if kpi['name'] == kpi_name:
                        selected_struct.append(kpi)
                        break

            # Update session state with selected KPIs
            st.session_state.selected_kpis_struct = selected_struct

            # Save selected KPIs
            if selected:
                st.session_state.selected_kpis = selected
                st.success("Selected KPIs have been saved to the tracker.")

        st.markdown("---")

        # KPI Builder Section
        st.header("KPI Builder")
        st.write("Based on your survey responses, the KPIs have been pre-defined for consistency. You can adjust or add new KPIs as needed.")

        # KPI Tracker Section
        st.header("KPI Tracker")
        if not st.session_state.selected_kpis_struct:
            st.info("No KPIs selected yet. Go to the 'Suggested KPIs' section above to select KPIs to track.")
        else:
            for idx, kpi in enumerate(st.session_state.selected_kpis_struct, 1):
                st.markdown(f"### {idx}. {kpi['name']}")
                st.write(f"**Description:** {kpi['description']}")
                st.write(f"**Guidance:** {kpi['guidance']}")

                # Data Management Options
                data_option = st.radio(
                    f"How would you like to manage data for '{kpi['name']}'?",
                    ["Upload Data", "Generate Imaginary Data", "Manually Add Data"],
                    key=f"data_option_{kpi['name']}"
                )

                # Upload Data
                if data_option == "Upload Data":
                    uploaded_file = st.file_uploader(
                        f"Upload data for '{kpi['name']}'",
                        type=["csv", "xlsx"],
                        key=f"upload_{kpi['name']}"
                    )
                    if uploaded_file:
                        try:
                            if uploaded_file.name.endswith(".csv"):
                                df = pd.read_csv(uploaded_file)
                            else:
                                df = pd.read_excel(uploaded_file)
                            # Validate required columns
                            if set(['time_period', 'value']).issubset([col.lower() for col in df.columns]):
                                df.columns = [col.lower() for col in df.columns]
                                st.session_state.kpi_data[kpi['name']] = df.rename(columns={'value': 'Value'})
                                st.success(f"Data uploaded successfully for '{kpi['name']}'")
                                st.dataframe(df)
                            else:
                                st.error("Uploaded file must contain 'time_period' and 'value' columns.")
                        except Exception as e:
                            st.error(f"Error reading uploaded file: {e}")

                # Generate Imaginary Data with OpenAI
                elif data_option == "Generate Imaginary Data":
                    # Retrieve survey responses
                    survey = st.session_state.survey_responses
                    industry = survey.get("Industry", "General")
                    product_audience = survey.get("Product Audience", "General")

                    if st.button(f"Generate Data for '{kpi['name']}'", key=f"generate_{kpi['name']}"):
                        with st.spinner("Generating data with OpenAI..."):
                            df = generate_focused_fake_data(
                                industry=industry,
                                product_audience=product_audience,
                                kpi_name=kpi['name'],
                                kpi_description=kpi['description']
                            )
                        if not df.empty:
                            st.session_state.kpi_data[kpi['name']] = df
                            st.success(f"Imaginary data generated successfully for '{kpi['name']}'")
                            st.dataframe(df)

                # Manually Add Data
                elif data_option == "Manually Add Data":
                    with st.expander(f"Add Data for {kpi['name']}"):
                        time_period = st.text_input(f"Time Period for {kpi['name']} (e.g., Q1 2024)", key=f"time_{kpi['name']}")
                        value = st.number_input(f"Value for {kpi['name']}", key=f"value_{kpi['name']}")
                        if st.button(f"Add Data Point for '{kpi['name']}'", key=f"add_{kpi['name']}"):
                            if time_period and value is not None:
                                new_data = pd.DataFrame({"Time Period": [time_period], "Value": [value]})
                                if kpi['name'] in st.session_state.kpi_data:
                                    st.session_state.kpi_data[kpi['name']] = pd.concat(
                                        [st.session_state.kpi_data[kpi['name']], new_data],
                                        ignore_index=True
                                    )
                                else:
                                    st.session_state.kpi_data[kpi['name']] = new_data
                                st.success(f"Data point added for '{kpi['name']}'")
                            else:
                                st.error("Please provide both Time Period and Value.")

                # Display Data and Plot
                if kpi['name'] in st.session_state.kpi_data:
                    df = st.session_state.kpi_data[kpi['name']]
                    st.write(f"### Data for '{kpi['name']}'")
                    st.dataframe(df)
                    # Plotting with Plotly
                    fig = plot_kpi_chart(kpi['name'], df)
                    st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # KPI Explanations Section
        st.header("KPI Explanations")

        if not st.session_state.get("selected_kpis_struct"):
            st.info("No KPIs selected yet. Go to the 'Suggested KPIs' section above to select KPIs to track.")
        else:
            # Generate explanations if not already done
            if not st.session_state.get("kpi_explanations"):
                explanations = explain_kpis(st.session_state.selected_kpis_struct)
                st.session_state.kpi_explanations = explanations

            # Display explanations
            for kpi_name, explanation in st.session_state.kpi_explanations.items():
                st.markdown(f"### {kpi_name}")
                st.write(explanation)

        st.markdown("---")

        # Export KPIs Section
        st.header("Export KPIs")
        if not st.session_state.selected_kpis_struct:
            st.info("No KPIs selected yet. Go to the 'Suggested KPIs' section above to select KPIs to track.")
        else:
            st.subheader("Download KPIs")
            kpi_list = st.session_state.selected_kpis_struct
            # Export options
            csv = export_kpis_csv(kpi_list)
            json_data = export_kpis_json(kpi_list)
            text = export_kpis_text(kpi_list)

            if csv:
                st.download_button(
                    label="Download KPIs as CSV",
                    data=csv,
                    file_name="kpis.csv",
                    mime="text/csv"
                )
            if json_data:
                st.download_button(
                    label="Download KPIs as JSON",
                    data=json_data,
                    file_name="kpis.json",
                    mime="application/json"
                )
            if text:
                st.download_button(
                    label="Download KPIs as Text",
                    data=text,
                    file_name="kpis.txt",
                    mime="text/plain"
                )

# -------------------- Run the App --------------------

if __name__ == "__main__":
    main()
