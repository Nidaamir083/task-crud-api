import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

# ---------- Supabase setup (NEW - Stage 0) ----------
# This one "client" object is how our code talks to Supabase.
# We will reuse it for signup, login, logout, and token verification.
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)
# ---------- END NEW CODE ----------

class NewTask(BaseModel): title: str
class UpdateTask(BaseModel): title: str | None = None; done: bool | None = None

# ---------- Auth request shapes (NEW - Stage 1) ----------
# This describes what a signup/login request body must look like:
# a JSON object with "email" and "password" fields.
class AuthRequest(BaseModel):
    email: str
    password: str
# ---------- END NEW CODE ----------

# ---------- Database setup ----------

def get_db_connection():
    """Open a connection to our Postgres database using thr URL from .env."""
    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    # lets us read columns by name, like a dictionary
    return conn

def init_db():
    """Create the tasks table if it's missing, and seed 3 example tasks only if the table is empty."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    cur.execute("SELECT COUNT(*) AS count FROM tasks")
    count = cur.fetchone()["count"]
    if count == 0:
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Buy milk", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Walk the dog", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Finish homework", True))

    conn.commit()
    cur.close()
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
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows #already a list of dictionaries because of dict_row

@app.get("/tasks/{task_id}")
def get_one_task(task_id: int):
    """Get a single task by its ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row

@app.post("/tasks", status_code=201)
def create_task(new_task: NewTask):
     """Create a new task with the given title. The task will be marked as not done by default."""
     if new_task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Task title cannot be empty")

     conn = get_db_connection()
     cur = conn.cursor()
     cur.execute(
         "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
         (new_task.title, False)
     )
     row = cur.fetchone() # RETURNING * gives us the new row
     conn.commit()
     conn.close()
     return row


@app.put("/tasks/{task_id}")
def update_task(task_id: int, changes: UpdateTask):
    """Update an existing task's title and/or done status."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()

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
        new_done = changes.done 

    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (new_title, new_done, task_id)
    )
    conn.commit()

    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    updated_row = cur.fetchone()
    conn.close()
    return updated_row

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by its ID."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return


# ---------- Auth routes (NEW - Stage 1) ----------

@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthRequest):
    """Create a new user account via Supabase. The server never stores
    or hashes the password itself - Supabase handles that."""
    if credentials.email.strip() == "" or credentials.password.strip() == "":
        raise HTTPException(status_code=400, detail="Email and password are required")

    result = supabase.auth.sign_up({
        "email": credentials.email,
        "password": credentials.password
    })
    return result.user


@app.post("/auth/login")
def login(credentials: AuthRequest):
    """Log a user in via Supabase and return their access token (JWT)
    and refresh token."""
    if credentials.email.strip() == "" or credentials.password.strip() == "":
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }

# ---------- END NEW CODE ----------


# ---------- Public & protected gates (NEW - Stage 2) ----------

# ---------- Reusable auth guard (NEW - Stage 4) ----------
# Any route that adds "current_user = Depends(get_current_user)" to its
# parameters gets this check run automatically BEFORE its own code runs.
# One guard, reused everywhere - instead of pasting this logic into
# every protected route.
def get_current_user(authorization: str | None = Header(default=None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")

    token = authorization.removeprefix("Bearer ").strip()
    if token == "":
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        result = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if result is None or result.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result.user
# ---------- END NEW CODE ----------


@app.get("/public/info")
def public_info():
    """Anyone can call this - no ticket (token) required."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(current_user = Depends(get_current_user)):
    """Only real, verified users reach this point - the guard
    (get_current_user) already checked the token before this code runs."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@app.get("/protected/dashboard")
def protected_dashboard(current_user = Depends(get_current_user)):
    """A second protected route, reusing the SAME guard as /protected/profile.
    No new auth code was written - that's the whole point of middleware."""
    return {"message": f"Welcome to your dashboard, {current_user.email}!"}


@app.post("/auth/logout", status_code=204)
def logout(current_user = Depends(get_current_user)):
    """End the user's session via Supabase. Protected: you must present
    a valid token to log yourself out."""
    supabase.auth.sign_out()
    return

# ---------- END NEW CODE ----------