import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF  # Ensure using fpdf2
import numpy as np
import json

# Define benchmark ranges for KPIs based on industry
BENCHMARKS = {
    "Technology": {
        "User Engagement Score": {"base": 65, "growth": 1.5, "std_dev": 2},
        "Feedback Implementation Rate": {"base": 70, "growth": 1.2, "std_dev": 1},
        "Bug Fix Rate": {"base": 85, "growth": 1.0, "std_dev": 1},
        "Net Promoter Score (NPS)": {"base": 40, "growth": 2.0, "std_dev": 5},
        "Zillow Home Click Rate": {"base": 600, "growth": 30, "std_dev": 20},
        "Adoption Rate": {"base": 25, "growth": 0.5, "std_dev": 0.3},
        "Customer Satisfaction Score (CSAT)": {"base": 4.0, "growth": 0.05, "std_dev": 0.1},
        "Retention Rate": {"base": 50, "growth": 1.0, "std_dev": 2},
        "Churn Rate": {"base": 5.0, "growth": 0.1, "std_dev": 0.3},
        "Conversion Rate": {"base": 3.0, "growth": 0.05, "std_dev": 0.1}
    },
    "Healthcare": {
        "User Engagement Score": {"base": 55, "growth": 1.3, "std_dev": 2},
        "Feedback Implementation Rate": {"base": 75, "growth": 1.1, "std_dev": 1},
        "Bug Fix Rate": {"base": 90, "growth": 0.8, "std_dev": 1},
        "Net Promoter Score (NPS)": {"base": 35, "growth": 1.8, "std_dev": 5},
        "Zillow Home Click Rate": {"base": 500, "growth": 25, "std_dev": 20},
        "Adoption Rate": {"base": 20, "growth": 0.5, "std_dev": 0.3},
        "Customer Satisfaction Score (CSAT)": {"base": 3.5, "growth": 0.05, "std_dev": 0.1},
        "Retention Rate": {"base": 45, "growth": 1.0, "std_dev": 2},
        "Churn Rate": {"base": 6.0, "growth": 0.1, "std_dev": 0.3},
        "Conversion Rate": {"base": 2.5, "growth": 0.05, "std_dev": 0.1}
    },
    # Add other industries similarly
    "General": {
        "User Engagement Score": {"base": 60, "growth": 1.0, "std_dev": 2},
        "Feedback Implementation Rate": {"base": 70, "growth": 1.0, "std_dev": 1},
        "Bug Fix Rate": {"base": 85, "growth": 1.0, "std_dev": 1},
        "Net Promoter Score (NPS)": {"base": 40, "growth": 1.5, "std_dev": 5},
        "Zillow Home Click Rate": {"base": 550, "growth": 27, "std_dev": 20},
        "Adoption Rate": {"base": 25, "growth": 0.5, "std_dev": 0.3},
        "Customer Satisfaction Score (CSAT)": {"base": 4.0, "growth": 0.05, "std_dev": 0.1},
        "Retention Rate": {"base": 50, "growth": 1.0, "std_dev": 2},
        "Churn Rate": {"base": 5.0, "growth": 0.1, "std_dev": 0.3},
        "Conversion Rate": {"base": 3.0, "growth": 0.05, "std_dev": 0.1}
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

# Export Functions
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

def export_kpis_pdf(kpi_list):
    """Export KPIs as a PDF file using fpdf2 with UTF-8 support."""
    pdf = FPDF()
    pdf.add_page()
    
    # Optional: Add a Unicode font (requires the TTF file in your project directory)
    # Uncomment the lines below if you wish to use a Unicode font
    # pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    # pdf.set_font("DejaVu", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Selected KPIs", ln=True, align='C')
    pdf.ln(10)
    
    for kpi in kpi_list:
        # KPI Name
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, f"KPI: {kpi['name']}")
        
        # KPI Description
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, f"Description: {kpi['description']}")
        
        # KPI Guidance
        pdf.multi_cell(0, 10, f"Guidance: {kpi['guidance']}\n")
    
    try:
        # Generate PDF as bytes
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')  # Handle non-latin1 chars
    except UnicodeEncodeError as e:
        st.error(f"Error encoding PDF: {e}")
        return b""
    
    return pdf_output

# Revised Plotting Function
def plot_kpi_chart(kpi_name, data_points):
    """Generate an interactive and enhanced trend chart for a specific KPI using Plotly."""
    # Ensure 'Time Period' is sorted
    data_points = data_points.sort_values('Time Period')

    # Calculate a 3-month moving average
    data_points['Moving Average'] = data_points['Value'].rolling(window=3, min_periods=1).mean()
    
    # Create the primary line chart with markers
    fig = px.line(
        data_points,
        x='Time Period',
        y='Value',
        title=f"KPI: {kpi_name}",
        markers=True,
        labels={"Value": kpi_name}
    )
    
    # Generate the moving average line as a separate figure
    moving_avg_fig = px.line(
        data_points,
        x='Time Period',
        y='Moving Average',
        markers=False,
        labels={"Moving Average": "3-Month Moving Avg"}
    )
    
    # Modify the moving average trace's line properties
    for trace in moving_avg_fig.data:
        trace.update(line=dict(dash='dash', color='orange'))
    
    # Add the moving average trace to the primary figure
    fig.add_traces(moving_avg_fig.data)
    
    # Optional: Add annotations (e.g., Mid-year Review)
    if 'Month 6' in data_points['Time Period'].values:
        month6_value = data_points[data_points['Time Period'] == 'Month 6']['Value'].values[0]
        fig.add_annotation(
            x='Month 6',
            y=month6_value,
            text="Mid-year Review",
            showarrow=True,
            arrowhead=1,
            bgcolor="yellow",
            opacity=0.7
        )
    
    # Add shapes (e.g., threshold line)
    threshold = 1500  # Example threshold value; adjust based on KPI
    fig.add_shape(
        dict(
            type="line",
            x0="Month 1",
            y0=threshold,
            x1="Month 12",
            y1=threshold,
            line=dict(
                color="Red",
                width=2,
                dash="dash",
            ),
        )
    )
    fig.add_annotation(
        x="Month 12",
        y=threshold,
        xref="x",
        yref="y",
        text="Target Threshold",
        showarrow=False,
        yanchor="bottom",
        bgcolor="red",
        opacity=0.7,
        font=dict(color="white")
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

# Function to explain KPIs
def explain_kpis(kpi_list):
    """
    Generates explanations for each KPI. This function can be customized or expanded.
    For now, it returns a placeholder explanation.
    """
    explanations = {}
    for kpi in kpi_list:
        explanations[kpi['name']] = f"{kpi['description']} ({kpi['guidance']})"
    return explanations

# Revised Pre-Defined KPIs per Phase
def get_predefined_kpis(phase, survey_responses):
    """
    Returns a list of KPIs based on the phase and survey responses.
    Adjust KPIs as needed based on industry and product audience.
    """
    industry = survey_responses.get("Industry", "General")
    product_audience = survey_responses.get("Product Audience", "General")
    
    # Example KPI templates; expand as needed
    predefined_kpis = {
        "POC": [
            {
                "name": "Concept Validation Rate",
                "description": "Percentage of key features or concepts validated through initial testing or stakeholder feedback.",
                "guidance": "Aim for ≥ 80% validation rate."
            },
            {
                "name": "Stakeholder Satisfaction Score",
                "description": "Average satisfaction rating from stakeholders involved in the POC.",
                "guidance": "Aim for ≥ 4 out of 5."
            },
            {
                "name": "Technical Feasibility Index",
                "description": "Percentage of technical requirements met without major issues.",
                "guidance": "Aim for ≥ 90% feasibility."
            },
            {
                "name": "Resource Utilization Efficiency",
                "description": "Ratio of actual resource usage to planned resource allocation.",
                "guidance": "Aim for ≥ 95% efficiency."
            },
            {
                "name": "POC Completion Rate",
                "description": "Percentage of POC milestones achieved within the planned timeframe.",
                "guidance": "Aim for ≥ 100% completion."
            }
        ],
        "Closed Beta": [
            {
                "name": "User Engagement Score",
                "description": "Measures active user interactions, such as daily/monthly active users.",
                "guidance": "Aim for ≥ 60% active user rate."
            },
            {
                "name": "Feedback Implementation Rate",
                "description": "Percentage of user feedback items that are addressed and implemented.",
                "guidance": "Aim for ≥ 75% implementation."
            },
            {
                "name": "Bug Fix Rate",
                "description": "Percentage of reported bugs resolved within the beta period.",
                "guidance": "Aim for ≥ 90% fix rate."
            },
            {
                "name": "Net Promoter Score (NPS)",
                "description": "Measures user willingness to recommend the product to others.",
                "guidance": "Aim for ≥ 50 NPS."
            },
            {
                "name": "Zillow Home Click Rate",
                "description": "Tracks the number of clicks on Zillow home listings within the app.",
                "guidance": "Aim for ≥ 500 clicks per month."
            }
        ],
        "Public MVP": [
            {
                "name": "Adoption Rate",
                "description": "Percentage of target users who adopt the MVP within a specific timeframe.",
                "guidance": "Aim for ≥ 25% within the first quarter."
            },
            {
                "name": "Customer Satisfaction Score (CSAT)",
                "description": "Average satisfaction rating from users post-interaction or usage.",
                "guidance": "Aim for ≥ 4 out of 5."
            },
            {
                "name": "Retention Rate",
                "description": "Percentage of users who continue using the MVP over a set period.",
                "guidance": "Aim for ≥ 50% after six months."
            },
            {
                "name": "Churn Rate",
                "description": "Percentage of users who stop using the MVP within a specific period.",
                "guidance": "Aim for ≤ 5% per month."
            },
            {
                "name": "Conversion Rate",
                "description": "Percentage of users who take a desired action (e.g., sign-up, purchase).",
                "guidance": "Aim for ≥ 3%."
            }
        ]
    }
    
    # Customize KPIs based on Industry and Product Audience
    # Example: If B2B2C and Digital App, adjust descriptions or add specific KPIs
    if (phase == "Closed Beta" and 
        product_audience == "B2B2C (Business-to-Business-to-Consumer)" and 
        "digital app" in survey_responses.get("Offering Type", "").lower()):
        predefined_kpis["Closed Beta"].append({
            "name": "Zillow Home Click Rate",
            "description": "Tracks the number of clicks on Zillow home listings within the app.",
            "guidance": "Aim for ≥ 500 clicks per month."
        })
    
    return predefined_kpis.get(phase, [])

# Revised Data Generation Function
def generate_focused_fake_data(industry, product_audience, kpi_name):
    """
    Generate fake data based on Industry, Product Audience, and KPI.
    Returns a pandas DataFrame with 'Time Period' and 'Value'.
    """
    # Define the number of time periods (e.g., months)
    time_periods = [f"Month {i}" for i in range(1, 13)]
    
    # Initialize empty list for values
    values = []
    
    # Retrieve benchmarks based on industry
    industry_benchmarks = BENCHMARKS.get(industry, BENCHMARKS["General"])
    
    # Get benchmark data for the KPI
    benchmark = industry_benchmarks.get(kpi_name, {"base": 1000, "growth": 1.0, "std_dev": 2})
    base = benchmark["base"]
    growth = benchmark["growth"]
    std_dev = benchmark.get("std_dev", 2)
    
    # Generate data based on KPI type
    if "score" in kpi_name.lower() or "rate" in kpi_name.lower() or "index" in kpi_name.lower():
        for i in range(12):
            value = base + (growth * i) + np.random.normal(0, std_dev)
            # Handle percentage KPIs
            if "score" in kpi_name.lower() or "rate" in kpi_name.lower() or "index" in kpi_name.lower():
                value = max(min(value, 100), 0)  # Clamp between 0 and 100
            values.append(round(value, 2))
    else:
        for i in range(12):
            value = base * (growth ** i) + np.random.normal(0, std_dev)
            values.append(int(value))
    
    data = {
        "Time Period": time_periods,
        "Value": values
    }
    
    df = pd.DataFrame(data)
    
    # Validate 'Time Period' format
    expected_periods = [f"Month {i}" for i in range(1, 13)]
    if not all(period in expected_periods for period in df['Time Period']):
        st.error("Error: 'Time Period' entries must be in the format 'Month 1' to 'Month 12'.")
        return pd.DataFrame()  # Return empty DataFrame on error
    
    # Handle missing values
    df['Value'] = df['Value'].fillna(0)
    
    return df

# Survey Page
def survey_page():
    st.title("KPI Creation and Tracking Kit - Survey")

    st.markdown("""
    Please answer the following questions to help us tailor the KPI suggestions to your needs.
    """)

    with st.form("survey_form"):
        # Question 1
        st.markdown("### **1. What industry are you in?**")
        industry = st.selectbox("", [
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

# Main App Logic
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

            # Tabs for Further Functionalities
            tabs = st.tabs(["KPI Builder", "KPI Tracker", "KPI Explanations", "Export KPIs"])

            # KPI Builder Tab
            with tabs[0]:
                st.header("KPI Builder")
                st.write("Based on your survey responses, the KPIs have been pre-defined for consistency. You can adjust or add new KPIs as needed.")

            # KPI Tracker Tab
            with tabs[1]:
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

                        # Generate Imaginary Data
                        elif data_option == "Generate Imaginary Data":
                            # Retrieve survey responses
                            survey = st.session_state.survey_responses
                            industry = survey.get("Industry", "General")
                            product_audience = survey.get("Product Audience", "General")

                            if st.button(f"Generate Data for '{kpi['name']}'", key=f"generate_{kpi['name']}"):
                                with st.spinner("Generating data..."):
                                    df = generate_focused_fake_data(industry, product_audience, kpi['name'])
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

            # KPI Explanations Tab
            with tabs[2]:
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

            # Export KPIs Tab
            with tabs[3]:
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
                    pdf = export_kpis_pdf(kpi_list)

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
                    if pdf:
                        st.download_button(
                            label="Download KPIs as PDF",
                            data=pdf,
                            file_name="kpis.pdf",
                            mime="application/pdf"
                        )

if __name__ == "__main__":
    main()
