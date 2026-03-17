# Conventions

This file defines the default consistency rules for code review in this repo.
It is intentionally short. If a pattern is not established here, follow the
existing local pattern in the surrounding code.

## Review Order

1. Correctness
2. Consistency
3. Preference

Correctness always wins. A consistent pattern should still be changed if it is
wrong or unsafe.

## Default Consistency

### Backend

- Endpoints follow the existing FastAPI domain-file pattern (`api/v1/endpoints/{domain}.py`).
- Business logic lives in plain async service functions, not classes (`service/{domain}_service.py`).
- Layer direction is `api → service → repository → models/db`.
- SQLAlchemy queries and persistence logic belong in `backend/app/repository/`.
- Services must not import API schema modules for request/response contracts.
- Agent code lives in `service/agent/` as a subsystem within the service layer. Same rules: plain async functions, direct DB access via `AsyncSession`, no imports from API layer.
- Domain exceptions come from `core/exceptions.py` — never raise raw `HTTPException` from service layer.

### Frontend

- Code is organized by feature, not by file type.
- Visual/styling ownership follows `docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`.
- Shared API calls use `shared/api/api.ts` unless the transport requires something else (e.g. SSE streaming).
- React Query for server state. Zustand for client/UI state. No mixing.
- Similar problems use similar naming, file placement, and error handling.

## Canonical Examples

When in doubt, match one of these before inventing a new one:

| Pattern | Example |
|---|---|
| Backend endpoint | `backend/app/api/v1/endpoints/tasks.py` |
| Backend service | `backend/app/service/task_service.py` |
| Backend repository | `backend/app/repository/task_repo.py` |
| Backend agent tool dispatch | `backend/app/service/agent/tool_registry.py` |
| Frontend query/mutation hook | `frontend/src/features/tasks/hooks/useTasks.ts` |
| Frontend API client | `frontend/src/shared/api/api.ts` |
| Frontend SSE stream | `frontend/src/features/ai/api/ai.service.ts` |

## Exceptions

Inconsistency is allowed only when there is a real reason. Document it via:

- A short inline comment near the unusual code
- A note in this file or a relevant doc
- A backlog item in `issues/` if it is temporary technical debt

Undocumented exceptions should be treated as suspicious in review.

## Review Labels

- **Bug**: behavior is wrong now
- **Pattern violation**: behavior works but breaks an established repo pattern
- **Intentional exception**: different on purpose and documented
- **Technical debt**: acceptable for now, should be unified later

## Backlog

The `issues/` folder is the backlog. Use it for technical debt, deferred
standardization, and follow-up cleanup. Each item should say what the problem
is, why it is not being fixed now, and what should trigger revisiting it.
