import streamlit as st
import openai
import os

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to call OpenAI API
def explain_kpi(selected_variables):
    prompt = f"""
    You are an expert on KPIs. Explain the following KPI configuration in strict detail:
    {selected_variables}
    Provide a thorough explanation of what each KPI measures, how it can be used, and strict guidelines for its use.
    """
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # OpenAI model
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"

# Streamlit app
def main():
    # Title
    st.title("KPI Creation Kit")
    st.write("Welcome to the KPI Creation Kit! Define variables and generate detailed KPI explanations.")

    # User inputs
    industry = st.selectbox("Select your industry:", [
        "Manufacturing", "Retail", "Technology", "Healthcare",
        "Transportation & Logistics", "Marketing & Advertising",
        "Finance & Insurance", "Consumer Goods"
    ])

    kpi_type = st.selectbox("Select KPI type:", [
        "Financial", "Operational", "Customer Satisfaction", "Employee Performance"
    ])

    target = st.number_input("Set a target value for this KPI:", value=100)

    # Generate explanation
    if st.button("Generate Explanation"):
        selected_variables = f"Industry: {industry}\nKPI Type: {kpi_type}\nTarget Value: {target}"
        explanation = explain_kpi(selected_variables)
        st.subheader("KPI Explanation")
        st.write(explanation)

if __name__ == "__main__":
    main()

