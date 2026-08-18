# Task API

A small CRUD API built with **FastAPI** that manages a to-do list of tasks. Built as part of the FlyRank Backend Internship — Week 2 (Assignment A1: in-memory version) and Week 3 (Assignment A2: SQLite database version).

Data is now stored in a **SQLite database** (`tasks.db`) instead of a Python list — this means tasks now survive a server restart.

## Why SQLite?

SQLite was chosen because it needs no separate server or installation — the entire database is just one file (`tasks.db`) that lives in this project folder. It's the simplest possible way to add real, persistent storage to a small API like this one, without the setup overhead of something like PostgreSQL.

## Where the database lives

- The database file is `tasks.db`, in the root of this project.
- It is created **automatically** the first time the app starts — you don't need to create it manually.
- It is git-ignored (see `.gitignore`), so every fresh clone of this repo starts with a clean, empty database that gets seeded with 3 example tasks on first run.

## How to run this

**Requirements:** Python 3.10 or higher

```bash
# 1. Clone this repo
git clone https://github.com/Nidaamir083/task-crud-api.git
cd task-crud-api

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install fastapi uvicorn

# 4. Run the server
uvicorn main:app --reload
```

The server will start at **http://127.0.0.1:8000**

On first run, `tasks.db` is created automatically with 3 seeded example tasks. Restarting the server does not duplicate them.

Interactive API docs (Swagger UI) are available at **http://127.0.0.1:8000/docs**

## Endpoints

| Method | Path            | Description                        | Success | Errors        |
|--------|-----------------|-------------------------------------|---------|---------------|
| GET    | `/`             | Basic info about this API           | 200     | –             |
| GET    | `/health`       | Check if the server is alive        | 200     | –             |
| GET    | `/tasks`        | List all tasks                      | 200     | –             |
| GET    | `/tasks/{id}`   | Get a single task by id             | 200     | 404           |
| POST   | `/tasks`        | Create a new task                   | 201     | 400           |
| PUT    | `/tasks/{id}`   | Update a task's title and/or done   | 200     | 400, 404      |
| DELETE | `/tasks/{id}`   | Delete a task                       | 204     | 404           |

These endpoints and status codes are unchanged from Assignment 1 — only the storage underneath changed from an in-memory list to SQLite.

## Example request

```bash
curl -i -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

**Response:**

```
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":0}
```

## Exploring the database directly

You can open `tasks.db` in [DB Browser for SQLite](https://sqlitebrowser.org) to view and edit the data directly — any change made there shows up instantly through the API, with no restart needed, since both are reading the same file.

Example query I ran in DB Browser:

```sql
DELETE FROM tasks WHERE done = 1;
```

This deleted all tasks that were marked as completed — after first running `UPDATE tasks SET done = 1;`, every task had been marked done, so this query deleted all 3 rows in the table.

![Database screenshot](db-screenshot.PNG)

## Swagger UI

All endpoints are documented and testable at `/docs`:

![Swagger UI screenshot](swagger-screenshot.PNG)

## Notes

- Data is stored in `tasks.db` (SQLite) and survives server restarts.
- Both `POST` and `PUT` validate that `title` is not empty, returning `400 Bad Request` if it is.
- Requesting a task id that doesn't exist returns `404 Not Found` with a JSON error message.
- All database queries use parameterized placeholders (`?`) instead of inserting values directly into SQL strings, to keep the database safe from malformed or malicious input.

## AI vs me (Assignment 1 bonus)

**My prompt to the AI:**

> This is built in python in vs code, i have used fast api and import it first, the doors in my api are tasks, put, update, delete basically there are 7 doors. the url path is task 1, 2, all tasks and docs. 200 is the number for successful creation while 404 is for successful delete. 404 is when something not found. If I do not write anything in between "" this it remains empty and return invalid. The data lives in database, it should not survive when server restarts. Yes there is an interactive docs page and it should be found on the link given.

**What the AI did better:**
Nothing structurally — it produced a much simpler, shorter file than mine, but that's not "better," it's because it followed my prompt literally, gaps and all. I fully understand the AI's version; it's actually simpler than mine because it skips validation status codes and Pydantic models.

**What it got wrong or quietly ignored:**
- I told it 200 for "successful creation" and 404 for "successful delete" — both are backwards from real convention (should be 201 and 204). The AI didn't correct me, it just followed my mistake, which means a *successful* delete and a *not found* error now return the exact same status code.
- I never gave a status code for invalid (empty) input, so the AI just returned a normal 200 response with an error message buried inside it — the same "polite lie" problem I fixed back in Stage 2 of my own build.
- I said data "lives in a database" but also "should not survive restart" — a real contradiction. The AI silently picked in-memory storage and ignored the word "database" without telling me it was resolving a contradiction.
- It skipped the `/` and `/health` endpoints entirely, since I never mentioned them in this prompt.

**What my prompt forgot to specify — and what the AI silently decided:**
- I never said how data should arrive (JSON body vs. query parameter) — the AI chose to accept `title` as a raw parameter instead of a proper JSON body.
- I never asked for validation error *messages*, so it returned a bare `{"error": "invalid"}` instead of a helpful message.
- I never mentioned docstrings/descriptions, so none were added, even though my real Swagger docs have them.

**One-sentence takeaway after improving the prompt:**
When I rewrote the prompt with the *correct* status codes (201 create, 204 delete, 400 invalid, 404 not found) and specified JSON body input, the regenerated version matched my hand-built logic almost exactly — proving the original gap was entirely due to my prompt, not the AI's capability.

## Database Run Postgres locally with: docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks -p 5432:5432 -v taskdata:/var/lib/postgresql/data -d postgres:16