# Sophikon

AI-powered project management platform with Gantt charts, Kanban boards, task scheduling, resource management, and an AI assistant that helps with estimation and risk analysis.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, Zustand, TanStack Query |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 18 |
| **AI Service** | FastAPI microservice with pluggable LLM providers (Anthropic, OpenAI, Gemini) |
| **Infrastructure** | Docker Compose, Redis, Nginx, Mailpit (dev email) |

## Project Structure

```
sophikon/
  backend/           FastAPI REST API (port 8000)
  frontend/          React SPA (port 5173)
  ai-service/        AI brain microservice (port 8010)
  nginx/             Reverse proxy configs
  docs/              Requirements, design, and implementation docs
  docker-compose.yml Database, Redis, AI service, Mailpit, Nginx
```

---

## Local Development Setup

### Prerequisites

Make sure you have these installed before starting:

| Tool | Version | Installation |
|------|---------|-------------|
| **Python** | 3.13+ | https://www.python.org/downloads/ |
| **uv** | latest | `pip install uv` or https://docs.astral.sh/uv/getting-started/installation/ |
| **Node.js** | 20+ | https://nodejs.org/ |
| **Docker Desktop** | latest | https://www.docker.com/products/docker-desktop/ |
| **Git** | latest | https://git-scm.com/ |

### Step 1: Clone the repository

```bash
git clone <repo-url>
cd sophikon
```

### Step 2: Start Docker services (PostgreSQL + Redis)

Docker Desktop must be running first. Then:

```bash
# Create the root .env file
cp .env.example .env
```

Open `.env` and set a password:

```
POSTGRES_PASSWORD=pick-any-dev-password
```

Then start the database and Redis:

```bash
docker compose up postgres redis -d
```

Verify they're running:

```bash
docker compose ps
```

You should see `sophikon-db` (healthy) and `sophikon-redis` (running).

### Step 3: Set up the backend

```bash
cd backend

# Create the backend .env file
cp .env.example .env
```

Open `backend/.env` and update these values:

```ini
# Use the same password you chose in Step 2
DATABASE_URL=postgresql+asyncpg://sophikon_user:pick-any-dev-password@localhost:5433/sophikon

# Generate a secret key (run this command and paste the output):
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-generated-key-here
```

The rest of the defaults are fine for local development. Email and Google OAuth are optional.

Now install dependencies and set up the database:

```bash
uv sync              # install Python dependencies
alembic upgrade head # create all database tables
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**. You can check the interactive API docs at **http://localhost:8000/docs**.

### Step 4: Set up the frontend

Open a new terminal:

```bash
cd frontend
npm install    # install dependencies
npm run dev    # start dev server
```

The app is now running at **http://localhost:5173**.

The Vite dev server automatically proxies `/api` requests to the backend at `localhost:8000`, so no additional frontend configuration is needed.

### Step 5 (Optional): Set up the AI service

The app works without the AI service, but AI features (chat assistant, task estimation, project suggestions) will be unavailable.

To run in **mock mode** (no API keys needed, returns synthetic responses):

```bash
cd ai-service
uv sync
```

Create `ai-service/.env`:

```ini
AI_MODE=mock
AI_SERVICE_SHARED_SECRET=dev-ai-shared-secret
```

Start the service:

```bash
uvicorn app.main:app --reload --port 8010
```

The AI service is now running at **http://localhost:8010**.

Make sure the backend `.env` has matching values:

```ini
AI_SERVICE_URL=http://localhost:8010
AI_SERVICE_SHARED_SECRET=dev-ai-shared-secret
```

### Step 6 (Optional): Dev email with Mailpit

To test email features (registration verification, password reset, project invitations):

```bash
docker compose --profile dev up mailpit -d
```

Update `backend/.env`:

```ini
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@sophikon.org
MAIL_STARTTLS=false
MAIL_SSL_TLS=false
```

Restart the backend, then open **http://localhost:8025** to see captured emails.

---

## Quick Start Summary

After setup is complete, here's what you run each time:

```bash
# Terminal 1 — Docker services (if not already running)
docker compose up postgres redis -d

# Terminal 2 — Backend
cd backend
uvicorn app.main:app --reload

# Terminal 3 — Frontend
cd frontend
npm run dev

# Terminal 4 — AI service (optional)
cd ai-service
uvicorn app.main:app --reload --port 8010
```

Then open **http://localhost:5173** in your browser and register a new account.

---

## Running Tests

```bash
# Backend tests
cd backend
uv run pytest                     # all tests
uv run pytest tests/unit          # unit + API contract tests only

# Frontend tests
cd frontend
npm test                          # unit tests (Vitest)
npm run test:e2e                  # E2E tests (Playwright)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `SECRET_KEY must be set` | You forgot to create `backend/.env` or left `SECRET_KEY` as the default. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| Docker containers won't start | Make sure Docker Desktop is running. On Windows, check it in the system tray |
| `connection refused` on port 5433 | PostgreSQL container isn't running. Run `docker compose up postgres -d` and wait for it to be healthy |
| Frontend shows network errors | Backend isn't running on port 8000. Check the backend terminal for errors |
| `alembic upgrade head` fails | Database isn't reachable. Verify `DATABASE_URL` in `backend/.env` matches your Docker password |
| AI features say "unavailable" | The AI service isn't running. See Step 5 above |
| Emails not arriving | Set up Mailpit (Step 6) or check `MAIL_*` settings in `backend/.env` |
