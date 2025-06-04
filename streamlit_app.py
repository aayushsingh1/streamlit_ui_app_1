import streamlit as st
import requests
import pandas as pd
import plotly.express as px

FASTAPI_URL = "http://127.0.0.1:8000" # Make sure this matches your FastAPI server address

st.set_page_config(layout="wide")

# --- Helper Functions ---
def fetch_employee_ids():
    try:
        response = requests.get(f"{FASTAPI_URL}/employee_ids")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching employee IDs: {e}")
        return []

def fetch_employee_data(employee_id):
    if not employee_id:
        return pd.DataFrame()
    try:
        response = requests.get(f"{FASTAPI_URL}/employee/{employee_id}")
        response.raise_for_status()
        data = response.json()
        # Rename columns to match the original data for display consistency
        df = pd.DataFrame(data).rename(columns={
            "Employee_Id": "Employee Id",
            "Employee_Name": "Employee Name",
            "Leave_Taken": "Leave Taken",
            "Year": "Year",
            "Courses_Completed": "Courses Completed"
        })
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for employee {employee_id}: {e}")
        return pd.DataFrame()

# --- UI Sections ---

# Top Section
st.markdown("---") # Horizontal line
top_section = st.container()
with top_section:
    col1, col2 = st.columns([1, 3]) # Adjust ratios as needed
    with col1:
        employee_ids = fetch_employee_ids()
        if employee_ids:
            selected_employee_id = st.selectbox(
                "Select Employee ID:",
                options=employee_ids,
                index=0, # Default to the first ID or handle empty list
                format_func=lambda x: f"{x}"
            )
        else:
            selected_employee_id = st.number_input("Enter Employee ID:", min_value=0, step=1)
            if not employee_ids:
                st.warning("Could not load employee IDs from backend. Please enter manually.")


    employee_df = fetch_employee_data(selected_employee_id)

    with col2:
        st.subheader(f"Details for Employee ID: {selected_employee_id}")
        if not employee_df.empty:
            st.dataframe(employee_df[["Employee Id", "Employee Name", "Leave Taken", "Year", "Courses Completed"]], use_container_width=True)
        elif selected_employee_id:
            st.warning("No data found for the selected Employee ID.")
        else:
            st.info("Enter or select an Employee ID to see details.")


st.markdown("---") # Horizontal line

# Bottom Section
bottom_section = st.container()
with bottom_section:
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Year-wise Leave Taken")
        if not employee_df.empty and 'Leave Taken' in employee_df.columns and 'Year' in employee_df.columns:
            leave_data = employee_df.groupby("Year")["Leave Taken"].sum().reset_index()
            if not leave_data.empty:
                fig_pie = px.pie(leave_data, values="Leave Taken", names="Year", title="Leave Distribution by Year")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No leave data to display for pie chart.")
        else:
            st.info("Select an employee to see their leave data.")

    with right_col:
        st.subheader("Year-wise Courses Completed")
        if not employee_df.empty and 'Courses Completed' in employee_df.columns and 'Year' in employee_df.columns:
            courses_data = employee_df.sort_values("Year")
            if not courses_data.empty:
                fig_bar = px.bar(courses_data, x="Year", y="Courses Completed", title="Courses Completed Over Years",
                                 labels={"Year": "Year", "Courses Completed": "Number of Courses Completed"})
                fig_bar.update_xaxes(type='category') # Treat year as categorical for distinct bars
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No course data to display for bar chart.")
        else:
            st.info("Select an employee to see their course data.")
