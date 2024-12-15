import streamlit as st
import openai
import os
import io
import pandas as pd
import matplotlib.pyplot as plt
import json
from fpdf import FPDF

# Load OpenAI API key from secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OpenAI API key not found in secrets. Please configure it before running the app.")
    st.stop()
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state variables
if "survey_completed" not in st.session_state:
    st.session_state.survey_completed = False
st.session_state.kpi_suggestions = st.session_state.get("kpi_suggestions", [])
st.session_state.selected_kpis = st.session_state.get("selected_kpis", [])
st.session_state.selected_kpis_struct = st.session_state.get("selected_kpis_struct", [])
st.session_state.kpi_data = st.session_state.get("kpi_data", {})
st.session_state.kpi_explanations = st.session_state.get("kpi_explanations", {})
st.session_state.phase_outputs = st.session_state.get("phase_outputs", {})

# Helper Functions

def generate_kpis_from_openai(prompt_content):
    """Generate KPIs using OpenAI API based on user-provided context."""
    if not prompt_content:
        st.error("Prompt content is empty. Please provide valid inputs.")
        return []

    prompt = f"""
    You are an expert on KPIs. Based on the following business scenario, 
    suggest at least 5 relevant KPIs that align with the indicated pilot stage.

    **Instructions:**
    - **Output Format:** JSON array.
    - **Structure:** Each KPI should be a JSON object with the following keys:
      - "name": The name of the KPI.
      - "description": What it measures and why it's important.
      - "guidance": How to set targets and use it.
    - **No Additional Text:** The response should contain only the JSON array without any additional explanations, text, or annotations.

    **Business Scenario:**
    {prompt_content}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )

        # Extract content from the response
        content = response.choices[0].message.content.strip()

        # Attempt to parse JSON from the content
        kpi_list = json.loads(content)
        return kpi_list

    except json.JSONDecodeError as e:
        st.error(f"JSON decode error: {e}")
        st.error("The response from OpenAI was not valid JSON. Please check the raw response above.")
        return []
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return []

def generate_phase_outputs(survey_responses):
    """Generate detailed outputs for each pilot phase based on survey responses."""
    phases = ["POC", "Closed Beta", "Public MVP"]
    phase_outputs = {}

    for phase in phases:
        prompt = f"""
        You are a business strategy expert. Based on the following survey responses, provide detailed outputs for the {phase} phase of a pilot project.

        **Survey Responses:**
        Industry: {survey_responses['Industry']}
        Product Audience: {survey_responses['Product Audience']}
        Geography: {survey_responses['Geography']}
        Target Audience: {survey_responses['Target Audience']}
        Existing Customer Base: {survey_responses['Existing Customer Base']}
        Offering Type: {survey_responses['Offering Type']}
        Business Goal: {survey_responses['Business Goal']}
        Benefit Statement: {survey_responses['Benefit Statement']}
        Timeframe: {survey_responses['Timeframe']}
        Budget: {survey_responses['Budget']}

        **For the {phase} phase, provide the following:**
        1. **Primary Objective:** The main goal for this phase.
        2. **Top 3 KPIs:** The three most important KPIs to determine success.
        3. **Benchmarks/Targets:** Targets to hit for success.
        4. **Similar Companies’ Results:** Examples of companies that have undertaken similar phases and their outcomes.
        5. **Risk Radar:** (Only for POC phase) Potential risks or failure points and mitigation strategies.
        6. **Additional Creative Outputs:** As specified per phase.

        **Include citations for benchmarks and data sources.**
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            phase_outputs[phase] = content

        except openai.error.OpenAIError as e:
            phase_outputs[phase] = f"OpenAI API error: {e}"
        except Exception as e:
            phase_outputs[phase] = f"Unexpected error: {e}"

    return phase_outputs

def generate_focused_fake_data(industry, product_audience, kpi_name):
    """
    Generate fake data based on Industry, Product Audience, and KPI.
    Returns a pandas DataFrame with 'Time Period' and 'Value'.
    """
    # Define the number of time periods (e.g., months)
    time_periods = [f"Month {i}" for i in range(1, 13)]

    # Initialize empty list for values
    values = []

    # Example logic based on KPI and industry/product audience
    # This can be expanded with more sophisticated logic or mappings

    if kpi_name.lower() == "user engagement":
        if product_audience.startswith("B2B"):
            # Example for B2B or B2B2C digital apps
            base = 1000
            growth = 1.05
            for i in range(12):
                values.append(int(base * (growth ** i)))
        elif product_audience.startswith("B2C"):
            # Example for B2C digital apps
            base = 500
            growth = 1.1
            for i in range(12):
                values.append(int(base * (growth ** i)))
        else:
            # Generic engagement metrics
            base = 800
            growth = 1.07
            for i in range(12):
                values.append(int(base * (growth ** i)))

    elif kpi_name.lower() == "revenue growth":
        base = 10000
        growth = 1.08
        for i in range(12):
            values.append(int(base * (growth ** i)))

    elif kpi_name.lower() == "customer acquisition":
        base = 200
        growth = 1.1
        for i in range(12):
            values.append(int(base * (growth ** i)))

    elif kpi_name.lower() == "conversion rate":
        base = 2.5  # in percentage
        growth = 0.05
        for i in range(12):
            values.append(round(base + (growth * i), 2))

    elif kpi_name.lower() == "churn rate":
        base = 5.0  # in percentage
        growth = 0.1
        for i in range(12):
            values.append(round(base + (growth * i), 2))

    else:
        # Default fake data
        for _ in range(12):
            values.append(int(1000 + 500 * pd.np.random.rand()))

    data = {
        "Time Period": time_periods,
        "Value": values
    }

    return pd.DataFrame(data)

def explain_kpis(kpi_structs):
    """Generate detailed explanations for each KPI using OpenAI."""
    explanations = {}
    for kpi in kpi_structs:
        prompt = f"""
        Provide a detailed explanation for the following KPI:

        KPI Name: {kpi['name']}
        Description: {kpi['description']}
        Guidance: {kpi['guidance']}
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.4
            )
            content = response.choices[0].message.content.strip()
            explanations[kpi['name']] = content
        except openai.error.OpenAIError as e:
            explanations[kpi['name']] = f"Error generating explanation: {e}"
        except Exception as e:
            explanations[kpi['name']] = f"Unexpected error: {e}"
    return explanations

def plot_kpi_chart(kpi_name, data_points):
    """Generate a trend chart for a specific KPI."""
    fig, ax = plt.subplots()
    ax.plot(data_points['Time Period'], data_points['Value'], marker='o')
    ax.set_title(f"KPI: {kpi_name}")
    ax.set_xlabel("Time Period")
    ax.set_ylabel("Value")
    fig.tight_layout()
    return fig

def export_kpis_csv(kpi_list):
    """Export KPIs as a CSV file."""
    df = pd.DataFrame(kpi_list)
    return df.to_csv(index=False)

def export_kpis_json(kpi_list):
    """Export KPIs as JSON file."""
    return json.dumps(kpi_list, indent=4)

def export_kpis_text(kpi_list):
    """Export KPIs as a plain text file."""
    text_lines = []
    for kpi in kpi_list:
        text_lines.append(f"KPI: {kpi['name']}")
        text_lines.append(f"Description: {kpi['description']}")
        text_lines.append(f"Guidance: {kpi['guidance']}\n")
    return "\n".join(text_lines)

def export_kpis_pdf(kpi_list):
    """Export KPIs as a PDF file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Selected KPIs", ln=True, align='C')
    pdf.ln(10)
    for kpi in kpi_list:
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, f"KPI: {kpi['name']}")
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, f"Description: {kpi['description']}")
        pdf.multi_cell(0, 10, f"Guidance: {kpi['guidance']}\n")
    pdf_output = pdf.output(dest='S').encode('latin-1')  # Return as bytes
    return pdf_output

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
        ])

        if industry == "Other (open-ended)":
            industry = st.text_input("Please specify your industry")

        st.markdown("---")

        # Question 2
        st.markdown("### **2. What is your product audience?**")
        product_audience = st.selectbox("", [
            "B2B (Business-to-Business)",
            "B2C (Business-to-Consumer)",
            "B2B2C (Business-to-Business-to-Consumer)",
            "Internal (Employee-focused initiatives)",
            "Other (open-ended)",
        ])

        if product_audience == "Other (open-ended)":
            product_audience = st.text_input("Please specify your product audience")

        st.markdown("---")

        # Question 3
        st.markdown("### **3. What is your target launch geography or market?**")
        geography = st.selectbox("", [
            "Local (City or single region)",
            "Regional (Multiple regions within a country)",
            "National (Entire country)",
            "Global (Multiple countries)",
            "Other (open-ended)",
        ])

        if geography == "Other (open-ended)":
            geography = st.text_input("Please specify your target launch geography")

        st.markdown("---")

        # Question 4
        st.markdown("### **4. In one phrase, describe your target audience.**")
        target_audience = st.text_input("Provide a phrase (e.g., 'Small business owners', 'Millennial travelers')")

        st.markdown("---")

        # Question 5
        st.markdown("### **5. Do you already sell other products or services to your target audience?**")
        sell_to_audience = st.radio("", ["Yes", "No"])

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
        ])

        if offering_type == "Other (open-ended)":
            offering_type = st.text_input("Please specify what you are piloting")

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
        ])

        if business_goal == "Other (open-ended)":
            business_goal = st.text_input("Please specify your primary business goal")

        st.markdown("---")

        # Question 8
        st.markdown("### **8. In one sentence, explain what customer problem your pilot is trying to solve.**")
        benefit_statement = st.text_area("Provide a sentence (e.g., 'Help small business owners manage their finances more effectively.')")

        st.markdown("---")

        # Question 9
        st.markdown("### **9. When do you need to see success of your pilot by?**")
        timeframe = st.selectbox("", [
            "1–3 months",
            "3–6 months",
            "6–12 months",
            "12+ months",
            "I don't know yet",
        ])

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
        ])

        if budget == "Other (open-ended)":
            budget = st.text_input("Please specify your approximate budget")

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

            with st.spinner("Generating phase outputs..."):
                phase_outputs = generate_phase_outputs(st.session_state.survey_responses)
                st.session_state.phase_outputs = phase_outputs
            st.success("Phase outputs generated successfully! You can now access the KPI tools.")

# Main App Logic
def main():
    st.set_page_config(page_title="KPI Creation and Tracking Kit", layout="wide")

    if not st.session_state.survey_completed:
        survey_page()
    else:
        st.title("KPI Creation and Tracking Kit")
        st.write("Generate meaningful KPIs tailored to your pilot phase, understand them with OpenAI, and track their progress over time.")

        # Phase Selection
        st.markdown("### **Select a phase to focus on:**")
        phase = st.selectbox("", ["POC", "Closed Beta", "Public MVP"], index=0)

        st.markdown("---")

        # Display Phase Outputs
        if phase in st.session_state.phase_outputs:
            st.markdown(f"## **{phase} Phase**")
            st.markdown(st.session_state.phase_outputs[phase])

            # Additional Creative Outputs
            if phase == "POC":
                st.markdown("### **Creative Outputs for POC Phase**")
                st.markdown("""
                **Risk Radar:** Highlight potential risks or failure points for the POC stage and mitigation strategies tailored to your inputs.

                **Time-to-Impact Analysis:** Suggest an ideal timeline for reaching key milestones, with breakdowns of expected progress (e.g., weeks 1–4: concept validation, weeks 5–8: user testing).

                **Cost vs. ROI Model:** Provide a basic estimation of the cost-efficiency of pursuing the POC, factoring in industry norms and your inputs (e.g., budget, timeframe).

                **Hypothesis Tracker:** Generate a template for tracking and validating key assumptions about the offer or audience during the POC.
                """)

            elif phase == "Closed Beta":
                st.markdown("### **Creative Outputs for Closed Beta Phase**")
                st.markdown("""
                **Feedback Collection Blueprint:** Offer customizable templates or survey frameworks for collecting user feedback, tailored to your product audience (e.g., B2B, B2C).

                **Iterative Improvement Suggestions:** Based on historical data, propose actionable adjustments businesses can make based on common beta-stage findings in similar scenarios.

                **Competitive Gap Analysis:** Identify how competitors’ betas succeeded or failed, emphasizing lessons learned.

                **Scalability Checklist:** Generate a readiness assessment for moving from beta to public MVP, with a focus on scalability and operational readiness.
                """)

            elif phase == "Public MVP":
                st.markdown("### **Creative Outputs for Public MVP Phase**")
                st.markdown("""
                **Launch Readiness Dashboard:** Provide a customizable checklist to ensure the MVP is ready for public launch, including logistics, marketing, and customer support readiness.

                **Adoption Pathways:** Suggest strategies to maximize early adoption based on benchmarks and audience insights (e.g., discounts, referral programs, exclusive access).

                **Failure Indicator Alerts:** Highlight early warning signs that the MVP might not perform as expected, based on benchmarks and historical insights.

                **Market Resonance Insights:** Recommend tools or surveys to measure how well the MVP resonates with the target audience, beyond traditional KPIs.
                """)

            st.markdown("---")

            # Display Suggested KPIs and Explanations
            if st.session_state.kpi_suggestions:
                st.subheader("Suggested KPIs")
                # Allow users to select KPIs
                kpi_options = [f"{kpi['name']}: {kpi['description']}" for kpi in st.session_state.kpi_suggestions]
                selected = st.multiselect("Select KPIs you want to track:", options=kpi_options)

                # Map selected options back to KPI structures
                selected_struct = []
                for sel in selected:
                    kpi_name = sel.split(":")[0]
                    for kpi in st.session_state.kpi_suggestions:
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
                with st.form("kpi_builder_form"):
                    # Use survey responses to pre-fill or influence KPI generation
                    survey = st.session_state.get("survey_responses", {})
                    prompt_info = "\n".join([f"{key}: {value}" for key, value in survey.items()])

                    st.write("Based on your survey responses, generate KPI suggestions.")

                    # Submit Button
                    submitted = st.form_submit_button("Generate KPI Suggestions")
                    if submitted:
                        with st.spinner("Generating KPIs..."):
                            suggestions = generate_kpis_from_openai(prompt_info)
                        if suggestions:
                            st.session_state.kpi_suggestions = suggestions
                            st.success("KPIs generated successfully!")
                        else:
                            st.error("Failed to generate KPIs. Please try again.")

                # Display Suggested KPIs
                if st.session_state.kpi_suggestions:
                    st.subheader("Suggested KPIs")
                    # Allow users to select KPIs
                    kpi_options = [f"{kpi['name']}: {kpi['description']}" for kpi in st.session_state.kpi_suggestions]
                    selected = st.multiselect("Select KPIs you want to track:", options=kpi_options)

                    # Map selected options back to KPI structures
                    selected_struct = []
                    for sel in selected:
                        kpi_name = sel.split(":")[0]
                        for kpi in st.session_state.kpi_suggestions:
                            if kpi['name'] == kpi_name:
                                selected_struct.append(kpi)
                                break

                    # Update session state with selected KPIs
                    st.session_state.selected_kpis_struct = selected_struct

                    # Save selected KPIs
                    if selected:
                        st.session_state.selected_kpis = selected
                        st.success("Selected KPIs have been saved to the tracker.")

            # KPI Tracker Tab
            with tabs[1]:
                st.header("KPI Tracker")
                if not st.session_state.selected_kpis_struct:
                    st.info("No KPIs selected yet. Go to the 'KPI Builder' tab to generate and select KPIs first.")
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
                            uploaded_file = st.file_uploader(f"Upload data for '{kpi['name']}'", type=["csv", "xlsx"], key=f"upload_{kpi['name']}")
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
                            if "survey_responses" in st.session_state:
                                industry = st.session_state.survey_responses.get("Industry", "Unknown Industry")
                                product_audience = st.session_state.survey_responses.get("Product Audience", "Unknown Audience")
                            else:
                                industry = "Unknown Industry"
                                product_audience = "Unknown Audience"

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
                                            st.session_state.kpi_data[kpi['name']] = pd.concat([st.session_state.kpi_data[kpi['name']], new_data], ignore_index=True)
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
                            # Plotting
                            fig, ax = plt.subplots()
                            ax.plot(df['Time Period'], df['Value'], marker='o')
                            ax.set_title(f"Trend for '{kpi['name']}'")
                            ax.set_xlabel("Time Period")
                            ax.set_ylabel("Value")
                            plt.xticks(rotation=45)
                            st.pyplot(fig)

            # KPI Explanations Tab
            with tabs[2]:
                st.header("KPI Explanations")

                if not st.session_state.get("selected_kpis_struct"):
                    st.info("No KPIs selected yet. Go to the 'KPI Builder' tab to generate and select KPIs first.")
                else:
                    try:
                        if not st.session_state.get("kpi_explanations"):
                            with st.spinner("Generating KPI explanations..."):
                                explanations = explain_kpis(st.session_state.selected_kpis_struct)
                                st.session_state.kpi_explanations = explanations
                        # Display explanations
                        for kpi_name, explanation in st.session_state.kpi_explanations.items():
                            st.markdown(f"### {kpi_name}")
                            st.write(explanation)
                    except NameError as e:
                        st.error(f"Function not defined: {e}")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

            # Export KPIs Tab
            with tabs[3]:
                st.header("Export KPIs")
                if not st.session_state.selected_kpis_struct:
                    st.info("No KPIs selected yet. Go to the 'KPI Builder' tab to generate and select KPIs first.")
                else:
                    st.subheader("Download KPIs")
                    kpi_list = st.session_state.selected_kpis_struct
                    # Export options
                    csv = export_kpis_csv(kpi_list)
                    json_data = export_kpis_json(kpi_list)
                    text = export_kpis_text(kpi_list)
                    pdf = export_kpis_pdf(kpi_list)

                    st.download_button(
                        label="Download KPIs as CSV",
                        data=csv,
                        file_name="kpis.csv",
                        mime="text/csv"
                    )
                    st.download_button(
                        label="Download KPIs as JSON",
                        data=json_data,
                        file_name="kpis.json",
                        mime="application/json"
                    )
                    st.download_button(
                        label="Download KPIs as Text",
                        data=text,
                        file_name="kpis.txt",
                        mime="text/plain"
                    )
                    st.download_button(
                        label="Download KPIs as PDF",
                        data=pdf,
                        file_name="kpis.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
