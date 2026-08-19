import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DB_URL = "postgresql://postgres:dev@localhost:5432/tasks"

class Task(BaseModel):
    title: str
    done: bool = False

def get_connection():
    return psycopg.connect(DB_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            done BOOLEAN
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": row[0], "title": row[1], "done": row[2]}

@app.post("/tasks")
def create_task(task: Task):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", (task.title, task.done))
    conn.commit()
    conn.close()
    return {"message": "Task created"}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s", (task.title, task.done, task_id))
    conn.commit()
    conn.close()
    return {"message": "Task updated"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "Task deleted"}
