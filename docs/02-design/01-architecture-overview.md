# Architecture Overview

Version: 1.0
Date: 2026-03-20

## System Context

Sophikon is a web-based AI-powered project management platform with four runtime components:

- Frontend: React SPA (Vite in development, static build in production)
- Backend API: FastAPI handling business logic, REST, WebSocket, and SSE
- AI Service: Separate FastAPI service for LLM provider communication
- Infrastructure: PostgreSQL (primary data store), Redis (rate limit storage, pub/sub, Celery broker/backend), Celery (background and scheduled tasks)

## Component Communication

| From          | To         | Protocol / Mechanism                        |
| ------------- | ---------- | ------------------------------------------- |
| Frontend      | Backend    | REST, WebSocket, SSE                        |
| Backend       | AI Service | HTTP streaming                              |
| Backend       | PostgreSQL | Async SQLAlchemy                            |
| Backend       | Redis      | Pub/sub, key-value                          |
| Celery Worker | PostgreSQL | Async SQLAlchemy (task coroutine execution) |
| Celery Worker | Redis      | Broker/backend                              |

## Backend Layer Model

API (transport + auth/deps)
-> Service (business logic + orchestration)
-> Repository (queries/persistence)
-> Models (ORM)

Layer rule: no layer skips; API does not access repository/models directly.

## Frontend Layer Model

Pages and components
-> Feature hooks (TanStack Query)
-> API client (axios/fetch)

Feature state
-> Feature-local Zustand stores

Structure rule: each feature is self-contained under `features/{name}/`; shared code is used only for cross-feature concerns.

## Key Design Decisions

- AI execution loop stays in backend; AI service is an LLM adapter and does not execute domain tools or touch product DB state.
- WebSocket fan-out uses Redis pub/sub and Redis-backed presence to support horizontal backend scaling.
- Celery is the platform mechanism for scheduled and background execution (no ad-hoc thread workers in API process).
- Backend architecture follows strict API -> Service -> Repository separation for maintainability and traceability.
