# Module Design

**Version:** 1.0
**Date:** 2026-02-06

---

## Backend

### Layer Responsibilities

| Module        | Responsibility                                                                                            |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| `api/`        | HTTP, WebSocket, SSE transport. Request validation, auth deps, response serialization. No business logic. |
| `schema/`     | Pydantic request/response contracts. Shared between API and service boundaries.                           |
| `service/`    | All business logic. Plain async functions, no classes.                                                    |
| `repository/` | Database queries. SQLAlchemy `select()` style only.                                                       |
| `models/`     | ORM models. Defines tables, indexes, constraints.                                                         |
| `core/`       | Infrastructure primitives — config, DB engine, security, rate limiting, storage, WebSocket managers.      |
| `tasks/`      | Celery background and scheduled tasks.                                                                    |

### API Dependencies (`api/deps/`)

- `auth.py` — token validation, active user requirement
- `project.py` — project access checks, role gates
- `organization.py` — org membership and role checks
- `ws.py` — WebSocket token extraction and auth resolution

### Service Layer

Domain services (one per domain):
`auth`, `organization`, `project`, `project_member`, `organization_member`, `task`, `task_hierarchy`, `task_bulk`, `task_rollup`, `dependency`, `assignment`, `resource`, `utilization`, `calendar`, `comment`, `attachment`, `notification`, `activity_log`, `insights`

Cross-cutting services:

- `realtime_service` — queues events in transaction context, publishes to Redis after commit
- `ws_protocol` / `ws_session_service` — WebSocket protocol parsing and session lifecycle
- `ai_service` — AI conversation orchestration and ai-service HTTP client

### Agent Subsystem (`service/agent/`)

| Module             | Responsibility                                    |
| ------------------ | ------------------------------------------------- |
| `loop.py`          | Plan/execute orchestration, plan approval waiting |
| `planner.py`       | Structured plan definition and LLM request        |
| `executor.py`      | Iterative tool loop, destructive action approval  |
| `tool_registry.py` | Tool schemas and dispatch to domain services      |
| `history.py`       | Conversation history and memory                   |
| `streaming.py`     | SSE event constructors                            |
| `context.py`       | Per-run execution context                         |

---

## Frontend

### Feature Modules (`features/`)

Each feature owns its pages, components, hooks, API calls, store, and types. No cross-feature imports — use `shared/` only for code used by 2+ features.

| Feature         | Responsibility                                                                          |
| --------------- | --------------------------------------------------------------------------------------- |
| `auth`          | Login, register, profile, password reset, email verification                            |
| `organizations` | Org settings, member management, org switcher                                           |
| `projects`      | Project list, detail, settings, members, activity, realtime state                       |
| `tasks`         | Task table, detail panel, inline edit, dependencies, comments, attachments, assignments |
| `gantt`         | Gantt view, bar drag/resize, dependency drawing, schedule API                           |
| `kanban`        | Board columns, card drag-and-drop, column collapse, quick-add                           |
| `resources`     | Resource CRUD, utilization view                                                         |
| `calendar`      | Calendar view and exceptions                                                            |
| `dashboard`     | Project dashboard, insights                                                             |
| `reports`       | Reports page                                                                            |
| `notifications` | Notification inbox, real-time bell, WebSocket state                                     |
| `ai`            | Docked AI panel, conversation, plan approval, streaming                                 |

### Supporting Modules

| Module                  | Responsibility                                    |
| ----------------------- | ------------------------------------------------- |
| `app/`                  | App shell, route composition, route guards        |
| `shared/ui/`            | shadcn/ui primitives and design system components |
| `shared/api/`           | Axios client, base URL, interceptors              |
| `shared/layout/`        | App layout, sidebar, header                       |
| `shared/hooks/`         | Hooks used across 2+ features                     |
| `config/react-query.ts` | TanStack Query client defaults                    |
