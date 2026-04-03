# Backend Standards

Version: 1.0
Date: 2026-03-20

## Purpose

Define mandatory backend engineering standards for API, service, persistence, security, and runtime behavior.

## Non-Negotiable Rules

1. Layer direction must stay `api -> service -> repository -> models/db`.
2. Domain/business logic must live in service functions, not endpoint handlers.
3. Repository code owns SQLAlchemy query logic.
4. Service layer must not import API schema modules for transport contracts.
5. Service layer must not raise raw `HTTPException`; use domain exceptions from `core/exceptions.py`.

## API Standards

- FastAPI endpoints must be grouped by domain under `backend/app/api/v1/endpoints/`.
- Endpoints own transport concerns only:
- request validation
- dependency wiring
- status codes and response shaping
- Use shared dependency layer for auth and access context checks (`api/deps.py`).
- New endpoints must follow existing error payload contract.

## Service Standards

- Service functions are async and use explicit `AsyncSession` flow.
- Services own business rules, orchestration, and transaction boundaries.
- External side effects (notifications, realtime events) must happen only after successful commit.
- Cross-domain orchestration belongs in service layer, not repository layer.
- Time/date business logic must follow `docs/02-design/adr/ADR-012-time-semantics-contract.md`; do not introduce ad hoc `today` or timezone semantics in feature code.

## Repository and Persistence Standards

- Repository modules own filtering, joins, pagination, and persistence helpers.
- Repositories must stay policy-free (no transport or role decisions).
- Model constraints and enum semantics belong in ORM model definitions.
- Migrations must accompany schema changes.

## Realtime and Task Standards

- WebSocket publication must use existing manager patterns and Redis fan-out flow.
- Presence/connection state behavior must be compatible with current Redis and manager design.
- Background and scheduled jobs must run through Celery tasks, not ad-hoc threads.

## Security Standards

- Use centralized JWT and auth helpers in `core/security.py`.
- Keep rate limiting rules in centralized middleware/dependency path (`core/rate_limit.py`).
- Validate object-level access in dependencies and/or service checks before mutation.
- Keep file/path operations behind existing safe helper patterns.

## Performance and Reliability Standards

- Avoid N+1 queries in list/detail endpoints.
- Use pagination for large collections unless explicit bounded list is required.
- Keep transaction scope as small as possible.
- Log and handle failure paths explicitly for background/realtime paths.

## Definition of Done (Backend Change)

- Architecture/layer rules followed.
- Unit/integration tests added or updated.
- Required migration included (if schema changed).
- Error and auth behavior verified.
- Traceability and relevant docs updated.

## Related Decisions

- Time semantics contract -> `docs/02-design/adr/ADR-012-time-semantics-contract.md`
