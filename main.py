import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class NewTask(BaseModel): title: str
class UpdateTask(BaseModel): title: str | None = None; done: bool | None = None

tasks = [
    {"id": 1, "title": "Buy Milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Finish homework", "done": True},
]
"""New DataBase Setup"""

def get_db_connection():
    """Open a connection to our tasks.db file. Create a file if it doesn't exist yet"""
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create a task table if it is missing, and seed 3 examples tasks only if the table is empty"""
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
        )
    """)
    count = conn.execute("SELECT COUNT (*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks(title, done) VALUES(?, ?)", ("Buy milk", 0))
        conn.execute("INSERT INTO tasks(title, done) VALUES(?, ?)", ("Walk the dog", 0))
        conn.execute("INSERT INTO tasks(title, done) VALUES(?, ?)", ("Finish homework", 1))

    conn.commit()
    conn.close()

init_db() 

"""END NEW CODE"""

@app.get("/")
def read_root():
    """Show basic information about the API"""
    return { "name": "Task API", "version" : "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    """Check if the service is running."""
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    """Get a list of all tasks."""
    return tasks

@app.get("/tasks/{task_id}")
def get_one_task(task_id: int):
    """Get a single task by its ID."""
    for task in tasks:
        if task["id"] == task_id:
            return task
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=201)
def create_task(new_task: NewTask):
    """Create a new task with the given title. The task will be marked as not done by default."""
    if new_task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Task title can not be empty")

    next_id = max(task["id"] for task in tasks) + 1
    task = {"id": next_id, "title": new_task.title, "done": False }
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, changes: UpdateTask):
    """Update an existing task's title and/or done status."""
    for task in tasks:
        if task["id"] == task_id:
            if changes.title is not None:
                if changes.title.strip() == "":
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = changes.title
            if changes.done is not None:
                task["done"] = changes.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
 
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its ID."""
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


            

