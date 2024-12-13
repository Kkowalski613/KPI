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

# Helper Functions
def generate_kpis_from_openai(prompt_content):
    """Generate KPIs using OpenAI API based on user-provided context."""
    prompt = f"""
    You are an expert on KPIs. Based on the following business scenario, 
    suggest at least 5 relevant KPIs that align with the indicated pilot stage.
    Format each KPI as follows:
    <index>. KPI Name: <KPI_Name>
       Description: <What it measures and why it's important>
       Guidance: <How to set targets and use it>

    Scenario:
    {prompt_content}

    Consider the pilot phase and ensure KPIs are appropriate for the stage:
    - Proof of Concept (POC): Focus on feasibility, early validation.
    - Closed Beta: Focus on user feedback, product refinement.
    - Public MVP: Focus on market adoption, scalability, revenue.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def explain_kpis(kpi_list):
    """Provide detailed explanations for selected KPIs."""
    prompt = f"""
    You are an expert on KPIs. Provide a thorough explanation for each of the following KPIs:
    {kpi_list}
    For each KPI:
    - Explain what it measures in-depth.
    - How it can be practically applied.
    - Common benchmarks or targets.
    - Potential pitfalls or misinterpretations.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def plot_kpi_chart(kpi_name, data_points):
    """Generate a trend chart for a specific KPI."""
    fig, ax = plt.subplots()
    ax.plot(data_points, marker='o')
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
st.title("KPI Creation and Tracking Kit")
st.write("Generate meaningful KPIs tailored to your pilot phase, understand them with OpenAI, and track their progress over time.")

tabs = st.tabs(["KPI Builder", "KPI Tracker"])

# KPI Builder Tab
with tabs[0]:
    st.header("KPI Builder")
    with st.form("kpi_builder_form"):
        industry = st.selectbox("Industry:", ["Manufacturing", "Retail", "Technology", "Healthcare", "Other"])
        pilot_phase = st.selectbox("Pilot Phase:", ["Proof of Concept (POC)", "Closed Beta", "Public MVP"])
        target_audience = st.text_input("Describe your target audience:")
        business_goal = st.selectbox("Primary Business Goal:", ["Revenue growth", "Market share expansion", "Other"])
        
        submitted = st.form_submit_button("Generate KPI Suggestions")
        if submitted:
            prompt_info = f"Industry: {industry}\nPilot Phase: {pilot_phase}\nAudience: {target_audience}\nGoal: {business_goal}"
            with st.spinner("Generating KPIs..."):
                suggestions = generate_kpis_from_openai(prompt_info)
            st.session_state.kpi_suggestions = suggestions.split("\n") if suggestions else []
    
    if st.session_state.kpi_suggestions:
        st.subheader("Suggested KPIs")
        for line in st.session_state.kpi_suggestions:
            st.write(line)

# KPI Tracker Tab
with tabs[1]:
    st.header("KPI Tracker")
    if not st.session_state.selected_kpis_struct:
        st.info("No KPIs selected yet. Go to the 'KPI Builder' tab to generate and select KPIs first.")
    else:
        st.write("Track KPI performance here.")
