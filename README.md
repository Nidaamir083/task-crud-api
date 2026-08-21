# Task API

A small CRUD API built with **FastAPI** that manages a to-do list of tasks, now with **user authentication**. Built as part of the FlyRank Backend Internship — Week 1 (Assignment A1: in-memory version), Week 2 (Assignment A2: SQLite database version), Week 3 (Assignment A3: containerized PostgreSQL version), and Week 4 (Assignment A4: Supabase Auth — sign up, log in, log out, and protected routes, this one).

Data lives in a **PostgreSQL database**, running inside a **Docker container**. User accounts, passwords, and login tokens are managed by **Supabase Auth** — this app never stores or hashes a password itself.

## Why PostgreSQL + Docker?

SQLite worked well for a single file on one machine, but PostgreSQL is what real backends use in production — a proper database server that many programs can connect to at once. Docker means you don't install Postgres directly on your computer; instead you run its official image, and it behaves the same way on any machine. This is the same setup used by real companies, including FlyRank itself.

## Why Supabase Auth?

Rolling your own authentication — hashing passwords, signing tokens, checking expiry — is a well-known way to introduce security bugs. Instead, this app leans on **Supabase**, a trusted Identity Provider: Supabase stores accounts, hashes passwords, and issues signed **JSON Web Tokens (JWTs)**. This app's job is only to send credentials to Supabase, and to verify the tokens Supabase hands back.

## Where the data lives

- Task data is stored inside a Postgres database, in a Docker **volume** named `taskdata` — this means your rows survive even if the containers are stopped and removed.
- The `tasks` table is created automatically the first time the app starts, and seeded with 3 example tasks — only if the table is empty.
- User accounts and passwords live entirely in **Supabase** — this app's database never stores them.
- Secrets (database URL, Supabase URL, Supabase key) live in a `.env` file (git-ignored) — never hardcoded in the code. A `.env.example` file is committed so you know which variables to set.

## How to run this

**Requirements:** Docker Desktop (free), and a free [Supabase](https://supabase.com) project.

```bash
# 1. Clone this repo
git clone https://github.com/Nidaamir083/task-crud-api.git
cd task-crud-api

# 2. Copy the example env file
cp .env.example .env

# 3. Edit .env and fill in your own Supabase project URL and anon key
#    (Supabase Dashboard -> Project Settings -> API)

# 4. Start the whole stack - app and database - with one command
docker compose up
```

The API will be available at **http://localhost:8000**

> Note: on some Windows/Docker setups, `127.0.0.1` can hang due to a WSL2 networking quirk — use `localhost` instead, which works reliably. If a request ever hangs indefinitely with no response, check for a stuck leftover server process (`taskkill /F /IM python.exe` on Windows) before assuming it's a firewall issue.

On first run, the `tasks` table is created automatically with 3 seeded example tasks. Restarting the stack does not duplicate them, and your data survives a full `docker compose down` + `docker compose up` because of the `taskdata` volume.

Interactive API docs (Swagger UI) are available at **http://localhost:8000/docs** — protected routes show a lock icon, and you can paste a token via the "Authorize" button to test them directly in the browser.

To stop everything: press `Ctrl + C`, then run `docker compose down` (your task data stays safe in the volume; your Supabase account data stays safe in Supabase).

## Endpoints

| Method | Path               | Description                          | Auth required            | Success | Errors        |
|--------|--------------------|---------------------------------------|---------------------------|---------|---------------|
| GET    | `/`                | Basic info about this API             | none                      | 200     | –             |
| GET    | `/health`          | Check if the server is alive          | none                      | 200     | –             |
| GET    | `/tasks`           | List all tasks                        | none                      | 200     | –             |
| GET    | `/tasks/{id}`      | Get a single task by id               | none                      | 200     | 404           |
| POST   | `/tasks`           | Create a new task                     | none                      | 201     | 400           |
| PUT    | `/tasks/{id}`      | Update a task's title and/or done     | none                      | 200     | 400, 404      |
| DELETE | `/tasks/{id}`      | Delete a task                         | none                      | 204     | 404           |
| POST   | `/auth/signup`     | Create a new user account             | none                      | 201     | 400           |
| POST   | `/auth/login`      | Log in and receive an access token    | none                      | 200     | 400, 401      |
| POST   | `/auth/logout`     | End the current session               | `Authorization: Bearer`  | 204     | 401           |
| GET    | `/protected/profile`   | Read the logged-in user's own profile | `Authorization: Bearer`  | 200     | 401           |
| GET    | `/protected/dashboard` | A second protected route, reusing the same auth guard | `Authorization: Bearer`  | 200     | 401           |
| GET    | `/public/info`     | Open, unauthenticated info             | none                      | 200     | –             |

The task endpoints (`/tasks...`) and status codes are unchanged since Assignment 1 — only the storage underneath changed, first from an in-memory list to SQLite, then to PostgreSQL in Docker. The auth endpoints are new in Assignment 4.

## Example requests

**Task creation:**
```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

**Sign up:**
```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

**Log in:**
```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```

**Calling a protected route** (replace `<TOKEN>` with the `access_token` from the login response):
```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <TOKEN>"
```

## The auth flow, in short

1. A client sends an email + password to `/auth/signup` or `/auth/login`.
2. This app forwards those credentials to Supabase — it never stores or checks passwords itself.
3. On successful login, Supabase returns a signed **JWT** (access token). The client stores this token.
4. On every request to a protected route, the client attaches the token in the `Authorization: Bearer <token>` header.
5. A single reusable guard function (`get_current_user`, applied via FastAPI's `Depends(...)`) asks Supabase to verify the token before the route's own code runs. A missing, malformed, expired, or tampered token is rejected with `401` before any route logic executes.

## Exploring the database directly

You can look inside the running Postgres container using `psql`, the command-line SQL prompt:

```bash
docker exec -it mini_backend-db-1 psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```

![Database screenshot](db-screenshot.PNG)

## Swagger UI

All endpoints are documented and testable at `/docs`. Protected routes show a lock icon; click "Authorize" and paste an access token to test them directly in the browser:

![Swagger UI screenshot](swagger-screenshot.PNG)

## Notes

- Task data is stored in PostgreSQL, inside a Docker volume, and survives both server restarts and full container teardowns.
- User accounts, password hashing, and token signing are handled entirely by Supabase — this app never touches a raw password.
- Both `POST` and `PUT` on `/tasks` validate that `title` is not empty, returning `400 Bad Request` if it is. Signup and login validate that `email` and `password` are both present.
- Requesting a task id that doesn't exist returns `404 Not Found`; requesting a protected route without a valid token returns `401 Unauthorized`.
- All database queries use parameterized placeholders (`%s`) instead of inserting values directly into SQL strings, to keep the database safe from malformed or malicious input.
- Secrets are never hardcoded — the database URL and Supabase URL/key are read from `.env` (git-ignored) at startup. `.env.example` documents which variables are needed, with placeholder values only.

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
