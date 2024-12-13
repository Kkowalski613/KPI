import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

def load_kpi_data(uploaded_file):
    if uploaded_file is not None:
        # Attempt to read CSV
        try:
            df = pd.read_csv(uploaded_file)
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
    return None

def plot_kpi_graph(kpi_name, data_points):
    # Create a simple line chart for the KPI data
    fig, ax = plt.subplots()
    ax.plot(data_points, marker='o')
    ax.set_title(f"KPI: {kpi_name}")
    ax.set_xlabel("Time Period")
    ax.set_ylabel("Value")
    return fig

st.title("KPI Tracker")
st.write("Upload your previously configured KPIs and track their progress over time.")

uploaded_file = st.file_uploader("Upload KPI configuration CSV:", type=["csv"])
if uploaded_file:
    kpi_df = load_kpi_data(uploaded_file)
    if kpi_df is not None:
        st.write("KPI Configuration Loaded:")
        st.dataframe(kpi_df)

        # In a real scenario, you might have columns in `kpi_df` that define KPIs,
        # or you might let the user define KPI names and data here.
        
        # For demonstration, let's let the user define a KPI name and input some data points:
        kpi_name = st.text_input("Enter KPI Name to Track:")
        data_points_str = st.text_input("Enter KPI data points separated by commas (e.g. 10,20,30):")

        if kpi_name and data_points_str:
            try:
                data_points = [float(x.strip()) for x in data_points_str.split(",")]
                fig = plot_kpi_graph(kpi_name, data_points)
                st.pyplot(fig)

                # Export graph as PNG
                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                
                st.download_button(
                    label="Download KPI Graph as PNG",
                    data=buf,
                    file_name=f"{kpi_name}_graph.png",
                    mime="image/png"
                )

            except ValueError:
                st.error("Please enter valid numeric data points separated by commas.")
