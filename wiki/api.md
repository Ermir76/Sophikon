# API

## Overview

RESTful API built with **FastAPI**, versioned under `/api/v1`. All endpoints return JSON. 75+ endpoints across 19 router groups.

**Base URL:** `https://api.sophikon.org/api/v1` (production)
**Local docs:** `http://localhost:8000/docs` (Swagger UI, development only)

## Authentication

- **Method:** JWT access tokens (30 min) + refresh tokens (7 days)
- **Delivery:** HTTP-only, secure cookies with path scoping
  - Access token: `path="/api"` — sent to all API routes
  - Refresh token: `path="/api/v1/auth"` — sent only to auth endpoints
- **Requirement:** All endpoints except `/auth/*` require authentication via `Depends(get_current_user)`
- **RBAC:** Project endpoints enforce role-based access via `get_project_or_404` dependency

## Response Format

**Success:**
```json
{
  "data": { ... },
  "meta": { "timestamp": "2026-02-06T10:30:00Z" }
}
```

**Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [{ "field": "email", "message": "Invalid email format" }]
  }
}
```

**Error codes:** `AppException` hierarchy — `NotFoundError`, `AuthenticationError`, `PermissionDeniedError`, `InvalidOperationError`, `ValidationError`, `ResourceConflictError`

## Endpoint Groups

| Group               | Prefix                             | Endpoints | Description                                    |
| ------------------- | ---------------------------------- | --------- | ---------------------------------------------- |
| **Auth**            | `/auth`                            | 8         | Register, login, logout, refresh, password reset, email verify |
| **Organizations**   | `/organizations`                   | 5         | Org CRUD                                        |
| **Org Members**     | `/organizations/:id/members`       | 4         | Invite, remove, change role, list               |
| **Projects**        | `/projects`                        | 6+        | CRUD, dashboard, list (org-scoped)              |
| **Project Members** | `/projects/:id/members`            | 7+        | Invite, accept, remove, change role, list invitations |
| **Tasks**           | `/projects/:id/tasks`              | 7+        | CRUD, hierarchy, bulk ops, reorder              |
| **Dependencies**    | `/projects/:id/dependencies`       | 4         | CRUD with circular detection                    |
| **Schedule**        | `/projects/:id/schedule`           | 2         | Trigger recalculation, get schedule data        |
| **Resources**       | `/projects/:id/resources`          | 6         | CRUD, workload                                  |
| **Assignments**     | `/tasks/:taskId/assignments`       | 4         | Assign/unassign resources, update units         |
| **Utilization**     | `/projects/:id/utilization`        | 2+        | Resource utilization data                       |
| **Calendars**       | `/projects/:id/calendars`          | 5+        | Calendar CRUD, exceptions                       |
| **Comments**        | `/comments`                        | 4         | Polymorphic CRUD (project, task, resource, etc.)|
| **Notifications**   | `/notifications`                   | 4         | List, mark read, mark all read, settings        |
| **Activity**        | `/projects/:id/activity`           | 1         | Project activity feed                           |
| **Insights**        | `/projects/:id/insights`           | 1+        | Project analytics and insights                  |
| **AI**              | `/projects/:id/ai`                 | 3         | Chat (SSE), estimate, suggestions               |
| **WebSocket**       | `/ws/projects/:id`                 | 1         | Real-time project updates                       |

## Key Contract Patterns

### Pagination
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

### Partial Updates (PATCH)
All updates use partial PATCH semantics — only send fields you want to change.

### Bulk Operations
Tasks support bulk create/update/delete via `POST /projects/:id/tasks/bulk`:
```json
{
  "create": [{ "name": "Task A", ... }],
  "update": [{ "id": "uuid", "name": "Renamed" }],
  "delete": ["uuid1", "uuid2"]
}
```

### AI Chat (SSE Streaming)
`POST /projects/:id/ai/chat` returns a Server-Sent Events stream:
```
data: {"type": "token", "content": "The project"}
data: {"type": "token", "content": " has 45 tasks"}
data: {"type": "done", "usage": {"tokens": 150}}
```

### WebSocket Protocol
`WS /api/v1/ws/projects/:id` — bidirectional real-time updates for project changes (task created, updated, deleted, etc.)

## Rate Limiting

Built-in via **SlowAPI** middleware. Applied globally with configurable per-endpoint limits.

## Full API Specification

See [`docs/02-design/api-specification.md`](../docs/02-design/api-specification.md) for complete endpoint documentation with request/response schemas for all 75+ endpoints.

---

*Evidence: [`backend/app/main.py`](../backend/app/main.py), [`backend/app/api/v1/endpoints/`](../backend/app/api/v1/endpoints/), [`docs/02-design/api-specification.md`](../docs/02-design/api-specification.md)*
