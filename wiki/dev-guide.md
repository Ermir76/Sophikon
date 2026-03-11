# Developer Guide

## Prerequisites

| Tool           | Version  | Purpose                          | Install                        |
| -------------- | -------- | -------------------------------- | ------------------------------ |
| Python         | 3.13+    | Backend runtime                  | [python.org](https://python.org) |
| uv             | latest   | Python package manager           | `pip install uv` or `curl` install |
| Node.js        | 20+      | Frontend runtime                 | [nodejs.org](https://nodejs.org) |
| npm            | 10+      | Frontend package manager         | Comes with Node.js              |
| Docker Desktop | latest   | PostgreSQL, Redis, and services  | [docker.com](https://docker.com) |
| Git            | latest   | Source control                   | [git-scm.com](https://git-scm.com) |

## Quick Start

### 1. Clone & Environment

```bash
git clone https://github.com/Ermir76/Sophikon.git
cd sophikon
cp .env.example .env          # Set POSTGRES_PASSWORD
```

### 2. Start Database & Redis

```bash
docker compose up postgres redis -d
```

PostgreSQL runs on port **5433** (to avoid conflicts with local installations). Redis on **6379**.

### 3. Backend

```bash
cd backend
cp .env.example .env          # Set DATABASE_URL, SECRET_KEY
uv sync                       # Install dependencies
alembic upgrade head          # Run migrations
uvicorn app.main:app --reload # http://localhost:8000
```

**Verify:** `curl http://localhost:8000/` → `{"message": "Welcome to Sophikon!"}`
**API docs:** `http://localhost:8000/docs` (Swagger UI)

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Vite dev server proxies `/api` requests to `localhost:8000`.

### 5. (Optional) AI Service

```bash
cd ai-service
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

Default mode: `AI_MODE=mock` (no API keys needed).

### 6. (Optional) Full Docker Stack

```bash
docker compose up --build                    # backend + db + redis + nginx + ai-service
docker compose --profile dev up mailpit -d   # Email testing UI at localhost:8025
```

## Common Commands

### Testing

```bash
# Backend
cd backend && uv run pytest                    # All tests
cd backend && uv run pytest tests/unit         # Unit + API contract
cd backend && uv run pytest tests/integration  # Integration tests

# Frontend
cd frontend && npm test                        # Unit tests (Vitest)
cd frontend && npm run test:e2e                # E2E tests (Playwright)

# AI Service
cd ai-service && uv run pytest
```

### Linting & Formatting

```bash
# Backend
cd backend && uv run ruff check .              # Lint
cd backend && uv run ruff format .             # Format

# Frontend
cd frontend && npm run lint                    # ESLint
cd frontend && npm run format                  # Prettier
```

### Database

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Note:** Alembic uses **psycopg2 (sync)** even though the app uses asyncpg. The `env.py` automatically converts the connection string.

### Docker

```bash
docker compose up -d                           # Start all services
docker compose ps                              # Check status
docker compose logs -f backend                 # Stream backend logs
docker compose down                            # Stop all services
docker compose down -v                         # Stop + delete volumes (data loss!)
```

## Project Structure Reference

```
sophikon/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routers, middleware
│   │   ├── core/                # config, database, security, exceptions, rate_limit
│   │   ├── models/              # SQLAlchemy ORM models (28 tables)
│   │   ├── schema/              # Pydantic request/response schemas
│   │   ├── service/             # Business logic (plain async functions)
│   │   ├── repository/          # SQLAlchemy query functions
│   │   ├── api/v1/endpoints/    # Route handlers (19 files)
│   │   ├── api/deps/            # Dependency injection
│   │   └── tasks/               # Celery background tasks
│   ├── alembic/                 # Database migrations
│   └── tests/                   # pytest (unit + integration)
├── frontend/
│   ├── src/
│   │   ├── app/                 # App shell, routing, guards
│   │   ├── features/            # 11 feature modules
│   │   ├── shared/              # Shared UI, layout, hooks, api, lib
│   │   ├── config/              # React Query config
│   │   └── index.css            # Design tokens (light + dark)
│   └── tests/                   # Playwright E2E tests
├── ai-service/                  # Standalone AI microservice
├── landing/                     # Static marketing page
├── nginx/                       # Nginx config (HTTP + SSL)
├── docs/                        # Requirements, design, implementation
├── wiki/                        # Product wiki (this!)
├── docker-compose.yml
├── CLAUDE.md                    # AI assistant context
├── CONVENTIONS.md               # Code review rules
└── CHANGES.md                   # Changelog with rationale
```

## Environment Variables

### Root `.env`

| Variable            | Example           | Purpose             |
| ------------------- | ----------------- | ------------------- |
| `POSTGRES_PASSWORD` | `mypassword`      | PostgreSQL password |

### Backend `.env`

| Variable           | Example                                                  | Purpose                |
| ------------------ | -------------------------------------------------------- | ---------------------- |
| `DATABASE_URL`     | `postgresql+asyncpg://sophikon_user:pass@localhost:5433/sophikon` | DB connection |
| `SECRET_KEY`       | `64-char-hex-string`                                     | JWT signing key        |
| `ENV`              | `development`                                            | Environment mode       |
| `CORS_ORIGINS`     | `["http://localhost:5173"]`                               | Allowed CORS origins   |
| `FRONTEND_URL`     | `http://localhost:5173`                                  | Email verification links |
| `BACKEND_URL`      | `http://localhost:8000`                                  | Email verification links |
| `AI_SERVICE_URL`   | `http://localhost:8010`                                  | AI service connection  |

### AI Service `.env`

| Variable                  | Example                 | Purpose              |
| ------------------------- | ----------------------- | -------------------- |
| `AI_MODE`                 | `mock`                  | mock or live         |
| `AI_SERVICE_SHARED_SECRET`| `dev-ai-shared-secret`  | Service auth         |
| `ANTHROPIC_API_KEY`       | `sk-...`                | Live mode (optional) |
| `OPENAI_API_KEY`          | `sk-...`                | Live mode (optional) |

## Gotchas

1. **PostgreSQL port is 5433**, not 5432 — avoids conflicts with local PostgreSQL installations.

2. **Alembic uses psycopg2 (sync)** while the app uses asyncpg. The `env.py` auto-converts `postgresql+asyncpg://` to `postgresql+psycopg2://`. Don't be surprised by the sync driver in migration logs.

3. **Circular FK between calendar and project:** Calendar is created first without project FK, then project is created, then the FK is added via `op.create_foreign_key()`. Keep this sequence in migrations.

4. **Email in tests:** A global autouse fixture in `conftest.py` mocks the mail client for all tests. Without it, registration tests would send real emails via SMTP.

5. **Pre-commit hooks:** Ruff (backend) and ESLint + Prettier (frontend) run automatically on commit. If a commit is rejected, run the lint/format commands above and retry.

6. **Frontend imports must be absolute:** Use `@/shared/ui/button`, never `../../../shared/ui/button`. The `@/` alias is configured in `tsconfig.app.json`.

7. **Services are functions, not classes:** Don't create `class TaskService`. Use `async def create_task(...)` in `task_service.py`.

8. **Don't delete models without endpoints:** Many models (TaskBaseline, TimeEntry, etc.) exist for future phases. Check `docs/03-implementation/project-plan.md` before removing anything.

---

*Evidence: [`README.md`](../README.md), [`CLAUDE.md`](../CLAUDE.md), [`CONVENTIONS.md`](../CONVENTIONS.md), [`docs/03-implementation/development-environment.md`](../docs/03-implementation/development-environment.md)*
