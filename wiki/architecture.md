# Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Nginx (Reverse Proxy)                          │
│                        Ports 80 (→HTTPS redirect) + 443                     │
└────────────┬───────────────────────────────────────────────┬─────────────────┘
             │ /api/*                                       │ /
             ▼                                              ▼
┌────────────────────────────┐              ┌───────────────────────────┐
│   FastAPI Backend (:8000)  │              │  Static Landing Page      │
│   ─────────────────────    │              │  (HTML, served by Nginx   │
│   • REST API (v1)          │              │   or S3 + CloudFront)     │
│   • WebSocket (/ws)        │              └───────────────────────────┘
│   • Auth (JWT + cookies)   │
│   • Rate limiting          │              ┌───────────────────────────┐
│   • SSE (AI chat stream)   │              │  React SPA (Vite)         │
└──────┬──────────┬──────────┘              │  ─────────────────        │
       │          │                         │  • /app/* routes          │
       │          │ HTTP (service-to-service)│  • Fetches /api/*        │
       │          ▼                         │  • S3 + CloudFront (prod) │
       │   ┌─────────────────────┐          │  • localhost:5173 (dev)   │
       │   │ AI Service (:8010)  │          └───────────────────────────┘
       │   │ ─────────────────── │
       │   │ • POST /v1/brain/*  │
       │   │ • Mock / Live LLM  │
       │   │ • Shared secret auth│
       │   └─────────────────────┘
       │
       ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ Redis        │  │ Celery       │
│ 18-alpine    │  │ 7-alpine     │  │ (Background  │
│ Port 5433    │  │ Port 6379    │  │  tasks)      │
│ (host)       │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Backend Architecture (Layered)

The backend follows a strict **unidirectional** four-layer architecture:

```
Endpoint (API)  →  Service (Use Case)  →  Repository (DB Access)  →  Models/DB
```

### Layer Responsibilities

| Layer        | Location                     | Owns                                               | Must Not                       |
| ------------ | ---------------------------- | --------------------------------------------------- | ------------------------------ |
| **API**      | `backend/app/api/v1/endpoints/` | HTTP/WS semantics, Pydantic schemas, auth deps   | Import repository directly     |
| **Service**  | `backend/app/service/`          | Business rules, orchestration, transactions       | Import API schemas             |
| **Repository** | `backend/app/repository/`     | SQLAlchemy queries, joins, pagination             | Contain HTTP or business logic |
| **Models**   | `backend/app/models/`           | ORM definitions, table args, relationships        | —                              |

### Dependency Rules

```
✅ api → service → repository → models
❌ service → api schema
❌ repository → api or service
❌ api → repository (unless temporary documented exception)
```

*Evidence: [`docs/02-design/backend-architecture.md`](../docs/02-design/backend-architecture.md)*

## Frontend Architecture (Feature-Sliced)

```
src/
├── app/              # App shell, routing, guards
├── features/         # Domain modules (11 features)
│   ├── auth/         # Login, register, JWT store
│   ├── organizations/# Org CRUD, switcher, members
│   ├── projects/     # Project list, overview, settings, members
│   ├── tasks/        # Task table, hierarchy, inline editing
│   ├── gantt/        # Gantt chart (custom canvas)
│   ├── calendar/     # Calendar view
│   ├── resources/    # Resource sheet, utilization
│   ├── dashboard/    # Dashboard page
│   ├── reports/      # Reports page
│   ├── notifications/# Inbox, WebSocket badges
│   └── ai/           # AI chat panel, estimation
├── shared/           # Truly shared (ui, layout, hooks, api, lib)
├── config/           # React Query configuration
└── index.css         # Design tokens (light + dark)
```

Each feature owns: `pages/`, `components/`, `hooks/`, `api/`, `store/`, `types.ts`, `index.ts`.

*Evidence: [`docs/02-design/frontend-architecture.md`](../docs/02-design/frontend-architecture.md)*

## Infrastructure

| Component       | Technology         | Purpose                                     |
| --------------- | ------------------ | ------------------------------------------- |
| Containers      | Docker Compose     | All services orchestrated in one stack       |
| Reverse proxy   | Nginx 1.28-alpine  | SSL termination, routing, static files      |
| Database        | PostgreSQL 18      | Primary data store (port 5433 on host)      |
| Cache/Queue     | Redis 7            | Caching, session store, Celery broker       |
| Background jobs | Celery             | Async tasks (email, heavy computation)      |
| Dev email       | Mailpit            | SMTP testing UI (dev profile only)          |
| CI/CD           | GitHub Actions     | Lint, test, deploy landing page to S3       |
| Pre-commit      | Ruff + ESLint      | Lint/format on commit                       |

## Key Architecture Choices

| Choice              | Rationale                                                            |
| ------------------- | -------------------------------------------------------------------- |
| **Separate AI service** | Isolates LLM dependencies, allows independent scaling and mock mode |
| **Feature-sliced frontend** | Scales with complexity, prevents cross-module coupling          |
| **UUIDv7 PKs**      | Time-ordered for better index performance + globally unique          |
| **Async SQLAlchemy** | Non-blocking DB I/O matches FastAPI's async model                   |
| **Cookie-based JWT** | Prevents XSS token theft vs localStorage; path-scoped for security  |
| **Multi-tenant orgs** | Data isolation from day 1 avoids costly later refactoring           |

---

*Evidence: [`docker-compose.yml`](../docker-compose.yml), [`backend/app/main.py`](../backend/app/main.py), [`CLAUDE.md`](../CLAUDE.md), [`DEPLOYMENT_GUIDE.md`](../DEPLOYMENT_GUIDE.md)*
