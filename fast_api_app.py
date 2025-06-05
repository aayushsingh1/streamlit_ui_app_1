from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from typing import List, Optional

app = FastAPI()


DB_CONFIG = {
    'host': 'localhost',        # Or your MySQL server IP/hostname
    'user': 'root',
    'password': 'current_password_here',
    'database': 'db' # The database where 'Employee_details' table exists
}

# --- Pydantic Models ---
class EmployeeData(BaseModel):
    Employee_Id: int
    Employee_Name: str
    Leave_Taken: int
    Year: int
    Courses_Completed: int

class EmployeeUpdatePayload(BaseModel):
    Employee_Name: Optional[str] = None
    Leave_Taken: Optional[int] = None
    Courses_Completed: Optional[int] = None

# --- Helper function to get database connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# --- API Endpoints ---
@app.get("/employee_ids", response_model=List[int])
async def get_employee_ids():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT `EmployeeId` FROM Employee_details ORDER BY `EmployeeId` ASC")
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
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                `EmployeeId` as Employee_Id, 
                `EmployeeName` as Employee_Name, 
                `LeaveTaken` as Leave_Taken, 
                `Year`, 
                `CoursesCompleted` as Courses_Completed
            FROM Employee_details 
            WHERE `EmployeeId` = %s
            ORDER BY `Year` DESC
        """
        cursor.execute(query, (employee_id,))
        records = cursor.fetchall()
        if not records:
            # Return empty list if no records, let frontend decide how to handle
            return [] 
            # raise HTTPException(status_code=404, detail="Employee not found") # Or raise error
        return [EmployeeData(**record) for record in records]
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.delete("/employee_delete/{employee_id}", status_code=200)
async def delete_Employee_details(employee_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    cursor = conn.cursor()
    try:
        # Check if employee has any records
        cursor.execute("SELECT `EmployeeId` FROM Employee_details WHERE `EmployeeId` = %s LIMIT 1", (employee_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"No records found for EmployeeId {employee_id} to delete.")

        query = "DELETE FROM Employee_details WHERE `EmployeeId` = %s"
        cursor.execute(query, (employee_id,))
        conn.commit() 

        if cursor.rowcount == 0:
            # Should have been caught by the check above, but as a safeguard
            raise HTTPException(status_code=404, detail=f"No records were deleted for EmployeeId {employee_id} (they might have been deleted by another process).")
        
        return {"message": f"Successfully deleted {cursor.rowcount} record(s) for EmployeeId {employee_id}"}
    except Error as e:
        if conn.is_connected():
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during deletion: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.put("/employee/{employee_id}/year/{year}", response_model=EmployeeData)
async def update_employee_record(employee_id: int, year: int, payload: EmployeeUpdatePayload):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    cursor = conn.cursor(dictionary=True)
    
    set_clauses = []
    params = []

    if payload.Employee_Name is not None:
        set_clauses.append("`EmployeeName` = %s")
        params.append(payload.Employee_Name)
    
    if payload.Leave_Taken is not None:
        set_clauses.append("`LeaveTaken` = %s")
        params.append(payload.Leave_Taken)

    if payload.Courses_Completed is not None:
        set_clauses.append("`CoursesCompleted` = %s")
        params.append(payload.Courses_Completed)
    
    if not set_clauses:
        raise HTTPException(status_code=400, detail="No update fields provided in the payload.")

    params.extend([employee_id, year])
    
    try:
        # First, check if the record exists
        check_query = "SELECT `EmployeeId` FROM Employee_details WHERE `EmployeeId` = %s AND `Year` = %s"
        cursor.execute(check_query, (employee_id, year))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Record for EmployeeId {employee_id} and Year {year} not found.")

        update_query = f"UPDATE Employee_details SET {', '.join(set_clauses)} WHERE `EmployeeId` = %s AND `Year` = %s"
        cursor.execute(update_query, tuple(params))
        conn.commit()

        if cursor.rowcount == 0:
             raise HTTPException(status_code=404, detail=f"Record for EmployeeId {employee_id} and Year {year} found but not updated (data might be the same or issue occurred).")

        # Fetch the updated record to return
        select_query = """
            SELECT 
                `EmployeeId` as Employee_Id, 
                `EmployeeName` as Employee_Name, 
                `LeaveTaken` as Leave_Taken, 
                `Year`, 
                `CoursesCompleted` as Courses_Completed
            FROM Employee_details 
            WHERE `EmployeeId` = %s AND `Year` = %s
        """
        cursor.execute(select_query, (employee_id, year))
        updated_record = cursor.fetchone()
        if not updated_record:
             raise HTTPException(status_code=500, detail="Failed to retrieve the updated record.")
        
        return EmployeeData(**updated_record)

    except Error as e:
        if conn.is_connected():
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during update: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



