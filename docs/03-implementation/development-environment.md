# Development Environment Setup

**Version:** 1.0
**Date:** 2026-02-09

---

## Prerequisites

| Tool           | Version | Purpose                       |
| -------------- | ------- | ----------------------------- |
| Git            | 2.40+   | Version control               |
| Docker Desktop | 4.x+    | PostgreSQL & Redis containers |
| Python         | 3.13+   | Backend runtime               |
| uv             | 0.4+    | Python package manager        |
| Node.js        | 20+     | Frontend runtime (Phase 2)    |

### Installing Prerequisites

**Git:** https://git-scm.com/downloads

**Docker Desktop:** https://www.docker.com/products/docker-desktop/

**Python 3.13:**

```bash
# Windows (winget)
winget install Python.Python.3.13

# macOS (Homebrew)
brew install python@3.13

# Linux (Ubuntu/Debian)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv
```

**uv (Python package manager):**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/sophikon.git
cd sophikon

# 2. Start infrastructure services
docker compose up -d

# 3. Set up the backend
cd backend
uv sync
cp .env.example .env   # Then edit .env if needed

# 4. Run the backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000** and interactive docs at **http://localhost:8000/docs**.

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/sophikon.git
cd sophikon
```

### 2. Start Infrastructure (Docker)

The project uses Docker Compose for PostgreSQL and Redis:

```bash
docker compose up -d
```

This starts:

| Service    | Container Name | Host Port | Image              |
| ---------- | -------------- | --------- | ------------------ |
| PostgreSQL | sophikon-db    | 5433      | postgres:18-alpine |
| Redis      | sophikon-redis | 6379      | redis:7-alpine     |

> **Note:** PostgreSQL runs on port **5433** (not the default 5432) to avoid conflicts with any local PostgreSQL installation.

Verify the containers are running:

```bash
docker compose ps
```

You should see both `sophikon-db` and `sophikon-redis` with status "Up" and "healthy".

### 3. Backend Setup

```bash
cd backend
```

#### Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Create virtual environment and install all dependencies (including dev)
uv sync
```

This reads `pyproject.toml` and `uv.lock` to install exact, reproducible dependency versions.

#### Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

If `.env.example` doesn't exist, create `.env` with the following:

```env
# Database (Docker PostgreSQL on port 5433)
DATABASE_URL=postgresql+asyncpg://sophikon_user:Soph1k0n_Dev_2026!@localhost:5433/sophikon

# Security - generate your own key with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here

# Environment
ENV=development
```

> **Important:** The `.env` file is gitignored and must not be committed.

#### Environment Variables Reference

| Variable                      | Required | Default                                              | Description                        |
| ----------------------------- | -------- | ---------------------------------------------------- | ---------------------------------- |
| `DATABASE_URL`                | Yes      | -                                                    | PostgreSQL async connection string |
| `SECRET_KEY`                  | Yes      | -                                                    | JWT signing key (hex, 32+ bytes)   |
| `ENV`                         | No       | `development`                                        | `development` or `production`      |
| `REDIS_URL`                   | No       | `redis://localhost:6379/0`                           | Redis connection string            |
| `CORS_ORIGINS`                | No       | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No       | `30`                                                 | JWT access token lifetime          |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | No       | `7`                                                  | Refresh token lifetime             |
| `ANTHROPIC_API_KEY`           | No       | `None`                                               | For AI features (optional for MVP) |
| `OPENAI_API_KEY`              | No       | `None`                                               | For AI features (optional for MVP) |

#### Run the Backend

```bash

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **`--reload`** — auto-restart on code changes (development only)
- **API root:** http://localhost:8000
- **Swagger docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Verify by visiting http://localhost:8000 — you should see:

```json
{ "message": "Welcome to Sophikon!" }
```

### 4. Database Migrations (Alembic)

[Alembic](https://github.com/sqlalchemy/alembic) is the database migration tool for SQLAlchemy. It tracks schema changes and applies them to PostgreSQL. Configuration lives in `backend/alembic.ini` and `backend/alembic/`.

```bash
cd backend

# Apply all pending migrations
uv run alembic upgrade head

# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "description of changes"

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

> **Note:** Always run `alembic upgrade head` after pulling new changes that include migrations.

### 5. Frontend Setup

The frontend consists of two parts:

#### React SPA (Application)

```bash
cd frontend
npm install
npm run dev
```

The app dev server runs at **http://localhost:5173**.

| Package      | Version | Purpose                                |
| ------------ | ------- | -------------------------------------- |
| React        | 19.2.4  | UI library                             |
| Vite         | 7.3.1   | Build tool                             |
| TypeScript   | 5.9.3   | Language                               |
| Tailwind CSS | 4.x     | Styling (via @tailwindcss/vite plugin) |
| React Router | 7.x     | Client-side routing                    |

#### Static Landing Page

The landing page (`docs/02-design/landing-page-mockup.html`) is a standalone static HTML file — **not part of the React app**. This is intentional:

- **SEO-friendly** — crawlers see content immediately, no JS rendering
- **Fast** — no React bundle to load for first-time visitors
- **Independent** — can be deployed/updated without rebuilding the app

**Architecture:**

| Route    | Served By           | Purpose                              |
| -------- | ------------------- | ------------------------------------ |
| `/`      | Static HTML (Nginx) | Landing page, marketing, SEO         |
| `/app/*` | React SPA (Vite)    | Application (login, dashboard, etc.) |
| `/api/*` | FastAPI             | Backend API                          |

Landing page CTAs ("Start Planning Free", "Login") link to `/app/login` which loads the React app.

---

## Project Structure

```
sophikon/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── api/v1/           # API route handlers
│   │   ├── core/
│   │   │   ├── config.py     # Settings (reads from .env)
│   │   │   └── database.py   # SQLAlchemy async engine & session
│   │   ├── models/           # SQLAlchemy ORM models (25 models)
│   │   ├── schema/           # Pydantic request/response schemas
│   │   ├── service/          # Business logic layer
│   │   └── ai/               # AI integration services
│   ├── tests/                # pytest test suite
│   ├── pyproject.toml        # Dependencies & project config
│   ├── uv.lock               # Locked dependency versions
│   └── .env                  # Local environment variables (gitignored)
├── frontend/                 # React + TypeScript SPA (behind /app)
│   └── src/
│       ├── components/       # Reusable UI components
│       ├── hooks/            # Custom React hooks
│       ├── pages/            # Page-level components
│       ├── services/         # API client & utilities
│       ├── store/            # State management
│       ├── lib/              # Utilities
│       ├── types/            # Shared TypeScript types
│       └── assets/           # Static assets
├── ai-services/              # Standalone AI microservices
│   ├── assistant/
│   ├── estimation/
│   └── planning/
├── docs/                     # Project documentation
│   ├── 01-requirements/
│   ├── 02-design/
│   └── 03-implementation/
├── scripts/                  # Automation scripts
└── docker-compose.yml        # Infrastructure services
```

---

## Common Commands

### Docker

```bash
# Start all infrastructure services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v

# View logs
docker compose logs -f postgres
docker compose logs -f redis

# Connect to PostgreSQL directly
docker exec -it sophikon-db psql -U sophikon_user -d sophikon
```

### Backend

```bash
# Install/update dependencies
uv sync

# Run the development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --group dev <package-name>
```

### Database

```bash
# Connect to the database via psql
docker exec -it sophikon-db psql -U sophikon_user -d sophikon

# List all tables
\dt

# Describe a table
\d+ <table_name>

# Exit psql
\q
```

---

## Ports Summary

| Service      | Port | URL                        |
| ------------ | ---- | -------------------------- |
| FastAPI      | 8000 | http://localhost:8000      |
| Swagger Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL   | 5433 | localhost:5433             |
| Redis        | 6379 | localhost:6379             |
| Frontend SPA | 5173 | http://localhost:5173      |

---

## Troubleshooting

### Port 5433 already in use

Another process is using port 5433. Find and stop it, or change the port in `docker-compose.yml`:

```bash
# Windows
netstat -ano | findstr :5433

# macOS/Linux
lsof -i :5433
```

### Docker containers won't start

```bash
# Check container logs for errors
docker compose logs

# Ensure Docker Desktop is running
docker info

# Reset containers and volumes
docker compose down -v
docker compose up -d
```

### Backend can't connect to database

1. Verify Docker containers are running: `docker compose ps`
2. Check that `sophikon-db` is healthy (not just "Up")
3. Verify `DATABASE_URL` in `.env` uses port **5433** and matches docker-compose credentials
4. Test the connection directly:
   ```bash
   docker exec -it sophikon-db psql -U sophikon_user -d sophikon -c "SELECT 1;"
   ```

### `uv sync` fails

```bash
# Ensure uv is installed
uv --version

# Ensure Python 3.13 is available
python --version

# Try removing the virtual environment and recreating
rm -rf .venv
uv sync
```

### Module not found errors

Make sure you're running commands from the `backend/` directory and using `uv run` to activate the virtual environment:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

---

## IDE Setup (Recommended)

### VS Code

Recommended extensions:

- **Python** (ms-python.python) — Python language support
- **Pylance** (ms-python.vscode-pylance) — Type checking & IntelliSense
- **Ruff** (charliermarsh.ruff) — Fast Python linting & formatting
- **Docker** (ms-azuretools.vscode-docker) — Docker support
- **Thunder Client** or **REST Client** — API testing

Workspace settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/Scripts/python",
  "python.analysis.extraPaths": ["${workspaceFolder}/backend"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

> **Note:** On macOS/Linux, replace `Scripts` with `bin` in the interpreter path.

---

## Document History

| Version | Date       | Author | Changes       |
| ------- | ---------- | ------ | ------------- |
| 1.0     | 2026-02-09 | -      | Initial draft |
