pip install fastapi
pip install pandas
pip install mysql-connector-python
pip install streamlit
pip install requests
pip install plotly
pip install uvicorn




from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector # Import MySQL connector
from mysql.connector import Error
from typing import List, Optional

app = FastAPI()

# --- Database Configuration ---
# !!! IMPORTANT: Replace with your actual MySQL connection details !!!
DB_CONFIG = {
    'host': 'localhost',        # Or your MySQL server IP/hostname
    'user': 'your_mysql_user',
    'password': 'your_mysql_password',
    'database': 'your_database_name' # The database where 'employee_data' table exists
}

# --- Pydantic Model (remains the same) ---
class EmployeeData(BaseModel):
    Employee_Id: int
    Employee_Name: str
    Leave_Taken: int
    Year: int
    Courses_Completed: int

# --- Helper function to get database connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        # In a real app, you might want to raise an HTTPException here
        # or have more robust error handling.
        return None

@app.get("/employee_ids", response_model=List[int])
async def get_employee_ids():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    cursor = conn.cursor()
    try:
        # Assuming your table is named 'employee_data' and column is 'Employee Id'
        cursor.execute("SELECT DISTINCT `Employee Id` FROM employee_data ORDER BY `Employee Id` ASC")
        ids = [row[0] for row in cursor.fetchall()]
        return ids
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.get("/employee/{employee_id}", response_model=List[EmployeeData])
async def get_employee_details(employee_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    cursor = conn.cursor(dictionary=True) # dictionary=True returns rows as dicts
    try:
        # Make sure column names in the query match your table exactly
        query = """
            SELECT 
                `Employee Id` as Employee_Id, 
                `Employee Name` as Employee_Name, 
                `Leave Taken` as Leave_Taken, 
                `Year`, 
                `Courses Completed` as Courses_Completed
            FROM employee_data 
            WHERE `Employee Id` = %s
        """
        cursor.execute(query, (employee_id,))
        records = cursor.fetchall()
        
        if not records:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return [EmployeeData(**record) for record in records]
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# To run (if you run this file directly):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)



