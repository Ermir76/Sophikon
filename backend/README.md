# Sophikon Backend

FastAPI REST API with async SQLAlchemy, PostgreSQL, and Redis.

## Structure

```
app/
  api/v1/endpoints/   Route handlers (auth, projects, tasks, organizations, etc.)
  core/               Config, database, security, rate limiting
  models/             SQLAlchemy models (25 tables)
  schema/             Pydantic request/response schemas
  service/            Business logic layer
alembic/              Database migrations
tests/                Pytest test suite (integration + unit)
```

## API Endpoints

| Prefix | Description |
|---|---|
| `/api/v1/auth` | Register, login, logout, refresh, email verification |
| `/api/v1/organizations` | Organization CRUD |
| `/api/v1/organizations/.../members` | Organization membership + roles |
| `/api/v1/projects` | Project CRUD (scoped to organizations) |
| `/api/v1/projects/.../tasks` | Task CRUD with hierarchy |
| `/api/v1/projects/.../resources` | Resource management |
| `/api/v1/projects/.../dependencies` | Task dependencies |
| `/api/v1/projects/.../assignments` | Task assignments |

Swagger docs available at `/docs` in development mode (`ENV=development`).

## Setup

```bash
cp .env.example .env    # configure DATABASE_URL, SECRET_KEY, MAIL_* settings
uv sync                 # install dependencies (uses uv.lock)
alembic upgrade head    # apply migrations
uvicorn app.main:app --reload
```

## Running Tests

```bash
uv run pytest                    # all tests with coverage
uv run pytest tests/api/         # API tests only
uv run pytest tests/integration/ # integration flows
uv run pytest -k "test_auth"     # specific tests
```

Tests use savepoint-based rollback — each test runs in a transaction that gets rolled back, so no test data persists.

## Docker

The `Dockerfile` uses a multi-stage build with `uv` for dependency installation. The `start.sh` entrypoint runs `alembic upgrade head` before starting uvicorn.

```bash
docker compose up backend --build
```

## Linting

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
```
