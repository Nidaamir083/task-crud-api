# Task API

A small CRUD API built with **FastAPI** that manages a to-do list of tasks. Built as part of the FlyRank Backend Internship, Week 2, Assignment A1.

Data is stored **in memory** (a Python list) — this means all tasks reset every time the server restarts. A real database is coming in Week 3.

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

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

All endpoints are documented and testable at `/docs`:

![Swagger UI screenshot](swagger-screenshot.png)

## Notes

- No database is used yet — all data lives in memory and is lost on restart. This is intentional for this stage of the assignment.
- Both `POST` and `PUT` validate that `title` is not empty, returning `400 Bad Request` if it is.
- Requesting a task id that doesn't exist returns `404 Not Found` with a JSON error message.
