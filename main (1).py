from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

DB_NAME = "tasks.db"


# ---------- Helper function to connect to the database ----------
def get_connection():
    # This opens a connection to our database file
    conn = sqlite3.connect(DB_NAME)
    # This lets us get results back as dictionaries (with column names)
    # instead of plain tuples, which makes the code easier to read
    conn.row_factory = sqlite3.Row
    return conn


# ---------- This runs once, when the app starts ----------
@app.on_event("startup")
def startup():
    conn = get_connection()
    cursor = conn.cursor()

    # Create the "tasks" table if it doesn't already exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Check how many rows are already in the table
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    # Only add example tasks if the table is currently empty
    if count == 0:
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy groceries", 0))
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Finish homework", 0))
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Read a book", 1))

    conn.commit()
    conn.close()


# ---------- This describes what data a task looks like ----------
# Used for creating and updating tasks (the user doesn't send the id)
class TaskInput(BaseModel):
    title: str
    done: bool = False


# ---------- GET /tasks - get all tasks ----------
@app.get("/tasks")
def get_all_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()

    # Turn each database row into a normal dictionary
    tasks = [dict(row) for row in rows]
    return tasks


# ---------- GET /tasks/{id} - get one task ----------
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return dict(row)


# ---------- POST /tasks - create a new task ----------
@app.post("/tasks", status_code=201)
def create_task(task: TaskInput):
    # Check the title isn't empty (after removing extra spaces)
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, int(task.done))
    )
    conn.commit()

    new_id = cursor.lastrowid  # this gives us the id SQLite just created

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)


# ---------- PUT /tasks/{id} - update an existing task ----------
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskInput):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_connection()
    cursor = conn.cursor()

    # First check the task actually exists
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    # Now update it
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (task.title, int(task.done), task_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)


# ---------- DELETE /tasks/{id} - delete a task ----------
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # First check the task actually exists
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return None
