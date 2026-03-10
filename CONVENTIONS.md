# Conventions

This file defines the default consistency rules for code review in this repo.
It is intentionally short. If a pattern is not established here, follow the
existing local pattern in the surrounding code.

## Review Order

Review code in this order:

1. Correctness
2. Consistency
3. Preference

Correctness always wins. A consistent pattern should still be changed if it is
wrong or unsafe.

## Default Consistency

Default consistency means new code should follow the existing pattern for
similar work unless there is a concrete reason not to.

Use these defaults:

- Backend endpoints follow the existing FastAPI domain-file pattern.
- Backend business logic lives in plain service functions, not service classes.
- Backend layer direction is `api -> service -> repository -> models/db`.
- Backend services should not import API schema modules for request/response contracts.
- Backend SQLAlchemy query/persistence logic belongs in `backend/app/repository/`.
- Frontend code is organized by feature, not by file type.
- Frontend visual/styling ownership follows:
  - `docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`
  - `docs/02-design/frontend-architecture.md`
  - `docs/03-implementation/ui-ux-recovery-tracker.md`
- Shared frontend API calls use `shared/api/api.ts` unless the transport
  requires something else, such as streaming.
- React Query is used for shared server state. Local component state is used
  for transient UI state.
- Similar problems should use similar naming, file placement, and error
  handling.

## Canonical Examples

When in doubt, match one of these existing patterns before inventing a new one:

- Backend endpoint pattern: `backend/app/api/v1/endpoints/tasks.py`
- Backend service pattern: `backend/app/service/task_service.py`
- Frontend query and mutation pattern: `frontend/src/features/tasks/hooks/useTasks.ts`
- Frontend API client pattern: `frontend/src/shared/api/api.ts`

## Exceptions

Inconsistency is allowed only when there is a real reason.

When code intentionally deviates from the default pattern, document it in one of
these ways:

- A short inline comment near the unusual code
- A short note in this file or another relevant doc
- A backlog item in `issues/` if the exception is temporary technical debt

Undocumented exceptions should be treated as suspicious in review.

## Review Labels

Classify review findings using these buckets:

- Bug: behavior is wrong now
- Pattern violation: behavior works but breaks an established repo pattern
- Intentional exception: different on purpose and documented
- Technical debt: acceptable for now, but should be unified or improved later

## Backlog

The `issues/` folder is the backlog for this repo.

Use it for:

- Technical debt
- Deferred standardization work
- Follow-up cleanup that should not block shipping

Backlog items should say:

- what is duplicated, inconsistent, or risky
- why it is not being fixed now
- what future trigger should cause it to be revisited
