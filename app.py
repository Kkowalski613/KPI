import streamlit as st
import openai
import os
import io
import pandas as pd
import matplotlib.pyplot as plt
import json
from fpdf import FPDF

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Initialize session state
if "kpi_suggestions" not in st.session_state:
    st.session_state.kpi_suggestions = []
if "selected_kpis" not in st.session_state:
    # Will store the raw chosen lines
    st.session_state.selected_kpis = []
if "selected_kpis_struct" not in st.session_state:
    # Will store structured data: [{"name":..., "description":..., "guidance":...}, ...]
    st.session_state.selected_kpis_struct = []
if "kpi_data" not in st.session_state:
    # Dictionary to hold KPI data points: {kpi_name: [values]}
    st.session_state.kpi_data = {}

def generate_kpis_from_openai(prompt_content):
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
    prompt = f"""
    You are an expert on KPIs. Provide a thorough explanation for each of the following KPIs:
    {kpi_list}
    For each KPI:
    - Explain what it measures in-depth.
    - How it can be practically applied.
    - Common benchmarks or targets.
    - Potential pitfalls or misinterpretations.
    Remember to consider the pilot stage mentioned previously and how that stage influences the KPI's usage.
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
    fig, ax = plt.subplots()
    ax.plot(data_points, marker='o')
    ax.set_title(f"KPI: {kpi_name}")
    ax.set_xlabel("Time Period")
    ax.set_ylabel("Value")
    fig.tight_layout()
    return fig

def parse_selected_kpis(kpi_lines):
    """
    Parse the selected KPI lines into a structured format:
    [{"name": <KPI_Name>, "description": <Desc>, "guidance": <Guidance>}]
    """
    kpis = []
    current_kpi = {}
    for line in kpi_lines:
        line_stripped = line.strip()
        if line_stripped.lower().startswith("description:"):
            current_kpi["description"] = line_stripped.split("Description:",1)[1].strip()
        elif line_stripped.lower().startswith("guidance:"):
            current_kpi["guidance"] = line_stripped.split("Guidance:",1)[1].strip()
        elif "KPI Name:" in line_stripped:
            # If there's an ongoing KPI, push it first
            if current_kpi:
                kpis.append(current_kpi)
                current_kpi = {}
            # Start a new KPI
            parts = line_stripped.split("KPI Name:",1)
            if len(parts) > 1:
                current_kpi["name"] = parts[1].strip()
        elif line_stripped[0].isdigit() and ". " in line_stripped:
            # Potential start line for a new KPI, already handled in KPI Name line
            continue
    # Add the last one if not empty
    if current_kpi:
        kpis.append(current_kpi)
    return kpis

def export_kpis_csv(kpi_list):
    df = pd.DataFrame(kpi_list)
    return df.to_csv(index=False)

def export_kpis_json(kpi_list):
    return json.dumps(kpi_list, indent=4)

def export_kpis_text(kpi_list):
    text_lines = []
    for kpi in kpi_list:
        text_lines.append(f"KPI: {kpi['name']}")
        text_lines.append(f"Description: {kpi['description']}")
        text_lines.append(f"Guidance: {kpi['guidance']}\n")
    return "\n".join(text_lines)

def export_kpis_pdf(kpi_list):
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

st.title("KPI Creation and Tracking Kit")
st.write("Generate meaningful KPIs tailored to your pilot phase, understand them with OpenAI, and track their progress over time. You can also export your KPIs in multiple formats.")

tabs = st.tabs(["KPI Builder", "KPI Tracker"])

# ------------------- KPI BUILDER TAB -------------------
with tabs[0]:
    st.header("KPI Builder")

    st.write("Provide context to generate meaningful KPIs, aligned with your pilot phase:")

    industry = st.selectbox("Industry:", [
        "Manufacturing", "Retail", "Technology", "Healthcare",
        "Transportation & Logistics", "Marketing & Advertising",
        "Finance & Insurance", "Consumer Goods", "Education",
        "Government & Public Sector", "Energy & Utilities",
        "Hospitality & Travel", "Other"
    ])
    product_audience = st.selectbox("Product Audience:", ["B2B", "B2C", "B2B2C", "Internal", "Other"])
    geography = st.selectbox("Target Launch Geography:", ["Local", "Regional", "National", "Global", "Other"])
    target_audience = st.text_input("Describe your target audience:")
    offering_type = st.selectbox("Offering Type:", [
        "Physical product", "Digital app", "SaaS", "Service",
        "Hybrid physical/digital product", "Subscription-based product", "Other"
    ])
    business_goal = st.selectbox("Primary Business Goal:", [
        "Revenue growth", "Improved profitability", "Market share expansion",
        "Customer acquisition", "Brand loyalty/engagement", "Sustainability or ESG-related goals",
        "Other"
    ])
    timeframe = st.selectbox("Timeframe for success:", ["1-3 months", "3-6 months", "6-12 months", "12+ months"])

    pilot_phase = st.selectbox("Where are you in your pilot journey?", [
        "Proof of Concept (POC)",
        "Closed Beta",
        "Public MVP",
    ])

    if st.button("Generate KPI Suggestions"):
        prompt_info = f"""
        Industry: {industry}
        Audience: {product_audience}, {target_audience}
        Geography: {geography}
        Offering: {offering_type}
        Business Goal: {business_goal}
        Timeframe: {timeframe}
        Pilot Phase: {pilot_phase}
        """
        suggestions = generate_kpis_from_openai(prompt_info)
        st.session_state.kpi_suggestions = suggestions.split("\n") if suggestions else []
    
    if st.session_state.kpi_suggestions:
        st.subheader("Suggested KPIs")
        for line in st.session_state.kpi_suggestions:
            st.write(line)
        
        user_input = st.text_input("Select KPI indices to adopt (e.g. '1,2' to pick the first two KPIs):")

        if st.button("Adopt Selected KPIs"):
            chosen = []
            try:
                indices = [int(x.strip()) for x in user_input.split(",")]
                for idx in indices:
                    collecting = False
                    kpi_block = []
                    for line in st.session_state.kpi_suggestions:
                        if line.strip().startswith(f"{idx}."):
                            collecting = True
                            kpi_block.append(line)
                        elif collecting and (line.strip().startswith(tuple(str(i)+"." for i in range(1,20))) and not line.strip().startswith(f"{idx}.")):
                            # Next KPI number found, stop collecting
                            break
                        elif collecting:
                            kpi_block.append(line)
                    if kpi_block:
                        chosen.extend(kpi_block)
            except:
                st.error("Could not parse your selection. Please try something like '1,2'.")

            if chosen:
                st.session_state.selected_kpis = chosen
                # Parse them into structured format
                st.session_state.selected_kpis_struct = parse_selected_kpis(chosen)
                st.success("Selected KPIs adopted!")
    
    if st.session_state.selected_kpis_struct:
        st.subheader("Selected KPIs")
        for k in st.session_state.selected_kpis_struct:
            st.markdown(f"**KPI:** {k['name']}")
            st.markdown(f"**Description:** {k['description']}")
            st.markdown(f"**Guidance:** {k['guidance']}")
            st.write("---")

        if st.button("Explain Selected KPIs with OpenAI"):
            lines_for_explanation = []
            for i, k in enumerate(st.session_state.selected_kpis_struct, start=1):
                lines_for_explanation.append(f"{i}. KPI Name: {k['name']}\n   Description: {k['description']}\n   Guidance: {k['guidance']}")
            explanation = explain_kpis("\n".join(lines_for_explanation))
            st.subheader("Detailed KPI Explanation")
            st.write(explanation)

        st.subheader("Export Selected KPIs")
        # Export CSV
        csv_data = export_kpis_csv(st.session_state.selected_kpis_struct)
        st.download_button("Download as CSV", data=csv_data, file_name="selected_kpis.csv", mime="text/csv")

        # Export JSON
        json_data = export_kpis_json(st.session_state.selected_kpis_struct)
        st.download_button("Download as JSON", data=json_data, file_name="selected_kpis.json", mime="application/json")

        # Export TXT
        text_data = export_kpis_text(st.session_state.selected_kpis_struct)
        st.download_button("Download as TXT", data=text_data, file_name="selected_kpis.txt", mime="text/plain")

        # Export PDF
        pdf_data = export_kpis_pdf(st.session_state.selected_kpis_struct)
        st.download_button("Download as PDF", data=pdf_data, file_name="selected_kpis.pdf", mime="application/pdf")

# ------------------- KPI TRACKER TAB -------------------
with tabs[1]:
    st.header("KPI Tracker")
    st.write("Input time-series data for your selected KPIs and visualize their trends.")

    if not st.session_state.selected_kpis_struct:
        st.info("No KPIs selected yet. Go to the 'KPI Builder' tab to generate and select KPIs first.")
    else:
        st.subheader("Manage Your KPI Data")
        kpi_names = [k["name"] for k in st.session_state.selected_kpis_struct]
        
        selected_kpi_name = st.selectbox("Select a KPI to input data for:", kpi_names)
        data_input = st.text_input("Enter data points separated by commas (e.g., 10,20,30):")

        if st.button("Add Data Points"):
            if data_input:
                try:
                    values = [float(x.strip()) for x in data_input.split(",")]
                    if selected_kpi_name not in st.session_state.kpi_data:
                        st.session_state.kpi_data[selected_kpi_name] = values
                    else:
                        st.session_state.kpi_data[selected_kpi_name].extend(values)
                    st.success("Data added successfully!")
                except ValueError:
                    st.error("Please enter only numeric values separated by commas.")

        # Display charts for KPIs that have data
        for kpi_name, data_points in st.session_state.kpi_data.items():
            if data_points:
                st.write(f"## {kpi_name} Trend")
                fig = plot_kpi_chart(kpi_name, data_points)
                st.pyplot(fig)

                # Export chart as PNG
                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                st.download_button(
                    label=f"Download {kpi_name} Chart as PNG",
                    data=buf,
                    file_name=f"{kpi_name}_chart.png",
                    mime="image/png"
                )
