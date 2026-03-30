# Sophikon

AI-powered project management platform. Full-stack: React 19 + FastAPI + PostgreSQL + Celery + Redis.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0 async (asyncpg), Alembic (psycopg2), PostgreSQL 18, Redis 7, Celery
- **AI Service**: FastAPI microservice (port 8010) — LLM provider adapter. Future: MCP, A2A, agent registry.
- **Frontend**: React 19, TypeScript 5.9, Vite, Tailwind CSS 4.1, shadcn/ui, Zustand, TanStack Query, React Router 7
- **Infra**: Docker Compose, Nginx, Mailpit (dev)

## Dev Commands

```bash
# Database & Redis
docker compose up -d

# Backend
cd backend && uv sync
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm run dev

# Tests
cd backend && uv run pytest
cd frontend && npm test
cd frontend && npm run test:e2e

# Linting
cd backend && uv run ruff check . && uv run ruff format .
cd frontend && npm run lint && npm run format
```

## Discord Session Rules

- When a Discord message arrives (a `<channel source="discord" ...>` tag is present), immediately write the `chat_id` to `~/.claude/channels/discord/active_session` before doing anything else.
- Never `git push` or `git reset --hard` during a Discord session without saying what you're about to do first.

## Hard Rules — Never Break These

### SDLC Autopilot Closure Gate
- "Autopilot" means full SDLC completion, not just build + tests.
- Never end a feature task after BUILD only. You must run REVIEW and SYNC phases.
- Manual checks do not replace required close-out skills.
- Required close-out skills by change type (spawned as parallel agents from dev-lifecycle):
  - Backend changed: agent loads `dev-lifecycle/phases/review-backend.md` checklist → `/phase-reviewer`
  - Backend schema changed: `/pydantic-audit` also
  - Frontend changed: agent loads `dev-lifecycle/phases/review-frontend.md` checklist → `/consistency-review`
  - After review passes: `/done`
  - Commit with `/cc` when user asked to finalize with commit
- Before final handoff, include a short closure receipt listing which close-out skills ran (or why a step was intentionally skipped).

### General
- Never delete models that have no endpoints yet — they are planned for future phases.
- Never remove dependencies (redis, celery, fastapi-mail, recharts, etc.) without checking `docs/ROADMAP.md` first.
- Never call something "unused" without checking the roadmap.
- Before creating a new file, check if an existing file already handles it.
- Don't add comments, docstrings, or type annotations to code you didn't change.
- Don't create helpers or abstractions for things used only once.

### Backend
- Services are **plain async functions**, never classes.
- All DB queries use `select()` style, never `session.query()`.
- All endpoints require auth via `Depends(get_current_user)` or `get_project_or_404`.
- Domain exceptions only — never raise raw `HTTPException` from service layer.
- Models define indexes and constraints in `__table_args__`, not in migrations.
- Layer direction is `api → service → repository → models/db`. Never skip layers.

### Frontend
- Organize by feature, not by file type.
- Absolute imports only (`@/shared/ui/button`, never `../../../`).
- `shared/` is for code used by 2+ features. Feature-specific code stays in its feature folder.
- Use `getErrorMessage(error)` in catch blocks — never hardcoded error strings.
- Use `shared/api/api.ts` for all standard API calls. Raw fetch only for streaming.
- Never use ad-hoc global CSS hooks, glassmorphism/glow effects, or duplicate color logic in feature files.

## Documentation

Read what you need, when you need it.

### Planning

- `docs/00-planning/backlog.md` — all backlog items with points and priority
- `docs/ROADMAP.md` — V1.0 through V2.0+ feature roadmap

### Requirements

- `docs/01-requirements/` — functional requirements, user stories, non-functional requirements

### Design

- `docs/02-design/01-architecture-overview.md` — system overview and boundaries
- `docs/02-design/02-backend-architecture.md` — backend layer model
- `docs/02-design/03-frontend-architecture.md` — frontend feature structure, state model, routing
- `docs/02-design/04-agent-platform-architecture.md` — PM agent loop, tools, SSE contract
- `docs/02-design/05-deployment-topology.md` — infrastructure and deployment decisions
- `docs/02-design/06-data-flow.md` — key data flows (CRUD, AI, realtime, notifications)
- `docs/02-design/07-database-schema.md` — data model and relationships
- `docs/02-design/08-api-specification.md` — API contract reference
- `docs/02-design/09-module-design.md` — module responsibilities
- `docs/02-design/10-security-design.md` — auth, tokens, authorization
- `docs/02-design/11-observability-design.md` — logging, metrics, health

### Implementation

- `docs/03-implementation/sprint-plan.md` — current sprint and history
- `docs/03-implementation/workboard.md` — active mini-tasks
- `docs/03-implementation/requirements-traceability.md` — FR status tracking

### Testing

- `docs/04-testing/01-test-architecture.md` — test layers, tools, isolation strategy
- `docs/04-testing/02-test-strategy.md` — risk priority, coverage targets, CI gates

### Standards

- `docs/05-standards/01-backend-standards.md`
- `docs/05-standards/02-frontend-standards.md`
- `docs/05-standards/03-ai-agent-standards.md`
- `docs/05-standards/04-testing-standards.md`
- `docs/05-standards/05-ux-standards.md`
