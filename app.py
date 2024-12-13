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
st.session_state.kpi_suggestions = st.session_state.get("kpi_suggestions", [])
st.session_state.selected_kpis = st.session_state.get("selected_kpis", [])
st.session_state.selected_kpis_struct = st.session_state.get("selected_kpis_struct", [])
st.session_state.kpi_data = st.session_state.get("kpi_data", {})
st.session_state.kpi_explanations = st.session_state.get("kpi_explanations", {})

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
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )

        # Debugging: Log the raw API response
        # st.write("Raw API Response:", response)  # Uncomment for debugging

        # Extract content from the response
        content = response.choices[0].message.content.strip()
        # st.write("Processed Content:", content)  # Uncomment for debugging

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

def generate_imaginary_data(kpi_name, scenario_strength):
    """Generate imaginary data for a KPI based on a scenario strength."""
    prompt = f"""
You are an expert on competitive benchmarking in the industry selected. You know what good results look like for companies attempting pilots like this. Please generate benchmarks that we should compare our pilot to in order to determine whether the pilot is succeeding or not
    [
        {{"time_periodcomp1": "Q1 2024", "10%": <numeric_value>}},
        {{"time_periodcomp1": "Q2 2024", "15%": <numeric_value>}},
        ...
    ]
    Ensure the values align with a {scenario_strength} performance.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        # Convert JSON response to DataFrame
        data = json.loads(content)
        return pd.DataFrame.from_records(data)
    except json.JSONDecodeError as e:
        st.error(f"JSON decode error while generating imaginary data: {e}")
        return pd.DataFrame(columns=["time_period", "value"])
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API error while generating imaginary data: {e}")
        return pd.DataFrame(columns=["time_period", "value"])
    except Exception as e:
        st.error(f"Unexpected error while generating imaginary data: {e}")
        return pd.DataFrame(columns=["time_period", "value"])

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
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
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
    ax.plot(data_points['Value'], marker='o')
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
    """Export KPIs as a JSON file."""
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

# Main Streamlit App
st.set_page_config(page_title="KPI Creation and Tracking Kit", layout="wide")
st.title("KPI Creation and Tracking Kit")
st.write("Generate meaningful KPIs tailored to your pilot phase, understand them with OpenAI, and track their progress over time.")

# Tabs
tabs = st.tabs(["KPI Builder", "KPI Tracker", "KPI Explanations", "Export KPIs"])

# KPI Builder Tab
with tabs[0]:
    st.header("KPI Builder")
    with st.form("kpi_builder_form"):
        # Industry Selection
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
        
        if industry == "Other (Please Specify)":
            industry = st.text_input("Please specify your industry:")
        
        # Product Audience
        product_audience = st.selectbox("What is your product audience?", ["B2B", "B2C", "B2B2C", "Internal", "Other"])
        if product_audience == "Other":
            product_audience = st.text_input("Please specify your product audience:")
        
        # Geography
        geography = st.selectbox("What is your target launch geography?", ["Local", "Regional", "National", "Global", "Other"])
        if geography == "Other":
            geography = st.text_input("Please specify your target launch geography:")
        
        # Target Audience Description
        target_audience = st.text_input("In one phrase, describe your target audience (e.g., small business owners, millennial travelers)")
        
        # Existing Customer Base
        sell_to_audience = st.radio("Do you already sell other products/services to your target audience?", ["Yes", "No"])
        
        # Offering Type
        offering_type = st.selectbox("What are you offering?", [
            "Physical product",
            "Digital app",
            "SaaS",
            "Service",
            "Hybrid physical/digital product",
            "Subscription-based product",
            "Other",
        ])
        if offering_type == "Other":
            offering_type = st.text_input("Please specify your offering type:")
        
        # Business Goal
        business_goal = st.selectbox("What is your primary business goal?", [
            "Revenue growth",
            "Improved profitability",
            "Market share expansion",
            "Customer acquisition",
            "Brand loyalty/engagement",
            "Sustainability or ESG-related goals",
            "Other",
        ])
        if business_goal == "Other":
            business_goal = st.text_input("Please specify your primary business goal:")
        
        # Benefit Statement
        benefit_statement = st.text_input("What problem is your offer trying to solve?")
        
        # Timeframe
        timeframe = st.selectbox("When do you need to see success by?", ["1-3 months", "3-6 months", "6-12 months", "12+ months"])
        
        # Budget
        budget = st.selectbox("What’s your approximate budget for launching and running the pilot?", [
            "Less than $1m",
            "$1m–$5m",
            "$5m–$10m",
            "$10m–$20m",
            "> $20m",
        ])
        
        # Pilot Phase
        pilot_phase = st.radio("Where are you in your pilot journey?", [
            "Proof of Concept (POC)",
            "Closed Beta",
            "Public MVP",
        ])
        
        # Submit Button
        submitted = st.form_submit_button("Generate KPI Suggestions")
        if submitted:
            prompt_info = f"""
            Industry: {industry}
            Product Audience: {product_audience}
            Geography: {geography}
            Target Audience: {target_audience}
            Existing Customer Base: {sell_to_audience}
            Offering Type: {offering_type}
            Business Goal: {business_goal}
            Benefit Statement: {benefit_statement}
            Timeframe: {timeframe}
            Budget: {budget}
            Pilot Phase: {pilot_phase}
            """
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
                        if set(['time_period', 'value']).issubset(df.columns.str.lower()):
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
                scenario_strength = st.selectbox(
                    f"Select a scenario strength for '{kpi['name']}'",
                    ["Weak", "Medium", "Strong"],
                    key=f"scenario_strength_{kpi['name']}"
                )
                if st.button(f"Generate Data for '{kpi['name']}'", key=f"generate_{kpi['name']}"):
                    with st.spinner("Generating data..."):
                        df = generate_imaginary_data(kpi['name'], scenario_strength)
                    if not df.empty:
                        df.columns = ['Time Period', 'Value']
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
    
    # Debugging: Check if selected_kpis_struct is populated
    # st.write("Selected KPIs Struct:", st.session_state.get("selected_kpis_struct", "Not Set"))  # Uncomment for debugging
    
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
