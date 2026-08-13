import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class NewTask(BaseModel): title: str
class UpdateTask(BaseModel): title: str | None = None; done: bool | None = None

# ---------- Database setup ----------

def get_db_connection():
    """Open a connection to our tasks.db file. Creates the file if it doesn't exist yet."""
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row  # lets us read columns by name, like a dictionary
    return conn

def init_db():
    """Create the tasks table if it's missing, and seed 3 example tasks only if the table is empty."""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy milk", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Walk the dog", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Finish homework", 1))

    conn.commit()
    conn.close()

init_db()  # runs once, every time the app starts

# ---------- END NEW CODE ----------

@app.get("/")
def read_root():
    """Show basic information about the API."""
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get("/health")
def health_check():
    """Check if the service is running."""
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    """Get a list of all tasks."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    # convert database rows into plain dictionaries, like your old list had
    return [dict(row) for row in rows]

@app.get("/tasks/{task_id}")
def get_one_task(task_id: int):
    """Get a single task by its ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return dict(row)

@app.post("/tasks", status_code=201)
def create_task(new_task: NewTask):
     """Create a new task with the given title. The task will be marked as not done by default."""
     if new_task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

     conn = get_db_connection()
     cursor = conn.execute(
         "INSERT INTO tasks (title, done) VALUES (?, ?)",
         (new_task.title, 0)
     )
     new_id = cursor.lastrowid  # the id the database just assigned
     conn.commit()

     row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
     conn.close()
     return dict(row)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, changes: UpdateTask):
    """Update an existing task's title and/or done status."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # start with the existing values, then apply any changes that were sent
    new_title = row["title"]
    new_done = row["done"]

    if changes.title is not None:
        if changes.title.strip() == "":
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        new_title = changes.title

    if changes.done is not None:
        new_done = 1 if changes.done else 0

    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, task_id)
    )
    conn.commit()

    updated_row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(updated_row)

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return