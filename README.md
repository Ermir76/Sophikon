# Sophikon

AI-powered project management platform with Gantt charts, task scheduling, and resource management.

## Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy (async), PostgreSQL, Redis
- **Frontend:** React 19, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS, shadcn/ui
- **Infrastructure:** Docker Compose, Nginx reverse proxy, Alembic migrations

## Project Structure

```
sophikon/
  backend/         FastAPI application
  frontend/        React SPA (Vite)
  landing/         Static marketing page
  nginx/           Nginx configs (HTTP + SSL)
  docs/            Requirements, design, implementation docs
  docker-compose.yml
```

## Local Development

### Prerequisites

- Python 3.13+
- Node.js 20+
- Docker Desktop (for PostgreSQL + Redis)

### 1. Start the database and Redis

```bash
cp .env.example .env          # set POSTGRES_PASSWORD
docker compose up postgres redis -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env          # set DATABASE_URL, SECRET_KEY
uv sync                       # install dependencies
alembic upgrade head          # run migrations
uvicorn app.main:app --reload # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

The Vite dev server proxies `/api` requests to `localhost:8000`.

### 4. (Optional) Full Docker stack

```bash
docker compose up --build                    # backend + db + redis + nginx
docker compose --profile dev up mailpit -d   # email testing UI at localhost:8025
```

## Testing

```bash
cd backend && uv run pytest        # backend tests
cd frontend && npm test            # frontend tests
```
