import streamlit as st
import requests
import pandas as pd
import plotly.express as px

FASTAPI_URL = "http://127.0.0.1:8000"

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
        if not data: # Handle case where employee exists but has no records
            return pd.DataFrame(columns=["Employee Id", "Employee Name", "Leave Taken", "Year", "Courses Completed"])
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
st.title("Employee Dashboard")

# Top Section
st.markdown("---")
top_section = st.container()
with top_section:
    employee_ids_list = fetch_employee_ids()
    
    if not employee_ids_list:
        st.warning("No Employee IDs found or unable to connect to the backend.")
        selected_employee_id_input = st.number_input(
            "Enter Employee ID (if known):", 
            min_value=0, 
            step=1, 
            key="manual_emp_id_input_top"
        )
        selected_employee_id = selected_employee_id_input if selected_employee_id_input > 0 else None
    else:
        selected_employee_id = st.selectbox(
            "Select Employee ID:",
            options=[""] + employee_ids_list, # Add an empty option
            index=0,
            format_func=lambda x: "Select an ID" if x == "" else f"{x}",
            key="emp_id_select_top"
        )
    
    employee_df = fetch_employee_data(selected_employee_id)

    st.subheader(f"Details for Employee ID: {selected_employee_id if selected_employee_id else 'N/A'}")
    if selected_employee_id and not employee_df.empty:
        st.dataframe(employee_df[["Employee Id", "Employee Name", "Leave Taken", "Year", "Courses Completed"]], use_container_width=True)
    elif selected_employee_id and employee_df.empty:
        st.info(f"No data found for Employee ID: {selected_employee_id}. The employee might exist but have no records, or the ID is incorrect.")
    else:
        st.info("Select an Employee ID to see details.")

st.markdown("---")

# Bottom Section
bottom_section = st.container()
with bottom_section:
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📊 Year-wise Leave Taken")
        if selected_employee_id and not employee_df.empty and 'Leave Taken' in employee_df.columns and 'Year' in employee_df.columns:
            leave_data = employee_df.groupby("Year")["Leave Taken"].sum().reset_index()
            if not leave_data.empty:
                fig_pie = px.pie(leave_data, values="Leave Taken", names="Year", title="Leave Distribution by Year")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No leave data to display for pie chart.")
        else:
            st.info("Select an employee with data to see their leave chart.")

        # Update Record Section (below pie chart)
        if selected_employee_id and not employee_df.empty:
            st.markdown("---")
            st.subheader(f"✏️ Update Record for Employee ID: {selected_employee_id}")
            available_years = sorted(employee_df["Year"].unique())
            if not available_years:
                st.info("No specific yearly records found for this employee to update.")
            else:
                selected_year_to_update = st.selectbox(
                    "Select Year of Record to Update:",
                    options=available_years,
                    key=f"update_year_select_{selected_employee_id}" # Dynamic key
                )
                if selected_year_to_update:
                    record_to_update_df = employee_df[employee_df["Year"] == selected_year_to_update]
                    if not record_to_update_df.empty:
                        current_record = record_to_update_df.iloc[0]
                        with st.form(key=f"update_employee_form_{selected_employee_id}_{selected_year_to_update}"): # Dynamic key
                            st.write(f"Updating record for Year: {selected_year_to_update}")
                            updated_employee_name = st.text_input(
                                "Employee Name:",
                                value=current_record["Employee Name"],
                                key=f"update_name_{selected_employee_id}_{selected_year_to_update}"
                            )
                            updated_leave_taken = st.number_input(
                                "Leave Taken:",
                                min_value=0,
                                value=int(current_record["Leave Taken"]),
                                key=f"update_leave_{selected_employee_id}_{selected_year_to_update}"
                            )
                            updated_courses_completed = st.number_input(
                                "Courses Completed:",
                                min_value=0,
                                value=int(current_record["Courses Completed"]),
                                key=f"update_courses_{selected_employee_id}_{selected_year_to_update}"
                            )
                            # Yellow color hint in text, actual button is standard
                            submit_update_button = st.form_submit_button(label="💾 Submit Update (Yellow Theme)")

                            if submit_update_button:
                                payload = {}
                                if updated_employee_name != current_record["Employee Name"]:
                                    payload["Employee_Name"] = updated_employee_name
                                if updated_leave_taken != current_record["Leave Taken"]:
                                    payload["Leave_Taken"] = updated_leave_taken
                                if updated_courses_completed != current_record["Courses Completed"]:
                                    payload["Courses_Completed"] = updated_courses_completed
                                
                                if not payload:
                                    st.warning("No changes detected to submit.")
                                else:
                                    try:
                                        update_url = f"{FASTAPI_URL}/employee/{selected_employee_id}/year/{selected_year_to_update}"
                                        response = requests.put(update_url, json=payload)
                                        if response.status_code == 200:
                                            st.success(f"Successfully updated record. Refreshing data...")
                                            st.experimental_rerun()
                                        else:
                                            st.error(f"Failed to update: {response.status_code} - {response.json().get('detail', 'Unknown error')}")
                                    except requests.exceptions.RequestException as e:
                                        st.error(f"Error connecting to API for update: {e}")
                    else:
                        st.warning("Could not load current data for the selected year.")
        elif selected_employee_id:
             st.info("No data loaded for this employee to enable updates.")


    with right_col:
        st.subheader("📈 Year-wise Courses Completed")
        if selected_employee_id and not employee_df.empty and 'Courses Completed' in employee_df.columns and 'Year' in employee_df.columns:
            courses_data = employee_df.sort_values("Year")
            if not courses_data.empty:
                fig_bar = px.bar(courses_data, x="Year", y="Courses Completed", title="Courses Completed Over Years",
                                 labels={"Year": "Year", "Courses Completed": "Number of Courses Completed"})
                fig_bar.update_xaxes(type='category')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No course data to display for bar chart.")
        else:
            st.info("Select an employee with data to see their course chart.")

        # Delete Employee Data Section (below bar graph)
        if selected_employee_id: # Show delete option if an ID is selected
            st.markdown("---")
            st.subheader("🗑️ Delete Employee Records")
            # Red color hint in text
            if st.button(f"🚨 Delete ALL Records for Employee ID: {selected_employee_id}", key=f"delete_employee_btn_{selected_employee_id}"): # Dynamic key
                confirmation = st.empty() # Placeholder for confirmation
                # Simple confirmation, could be more robust with st.expander or modal
                st.warning(f"Are you sure you want to delete all records for Employee ID {selected_employee_id}?")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("YES, DELETE", key=f"confirm_delete_{selected_employee_id}"):
                        try:
                            response = requests.delete(f"{FASTAPI_URL}/employee/{selected_employee_id}")
                            if response.status_code == 200:
                                st.success(f"Successfully deleted records. Refreshing data...")
                                # Clear selection or rerun
                                st.experimental_rerun()
                            elif response.status_code == 404:
                                st.error(f"Employee ID {selected_employee_id} not found for deletion or no records existed.")
                            else:
                                st.error(f"Failed to delete: {response.status_code} - {response.json().get('detail', 'Unknown error')}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error connecting to API for deletion: {e}")
                        confirmation.empty() # Clear confirmation message
                with col_cancel:
                    if st.button("CANCEL", key=f"cancel_delete_{selected_employee_id}"):
                        confirmation.empty() # Clear confirmation message
                        st.info("Deletion cancelled.")
            
        elif selected_employee_id and employee_df.empty:
             st.info("No data loaded for this employee to enable deletion.")


# Ensure to run FastAPI backend first: uvicorn fastapi_app:app --reload
# Then run Streamlit: streamlit run streamlit_app.py
