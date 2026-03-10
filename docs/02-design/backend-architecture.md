# Backend Architecture

## Layer Direction

The backend follows a strict unidirectional flow:

`endpoint (api) -> service (use case) -> repository (db access) -> models/db`

## Layer Responsibilities

### API Layer (`backend/app/api`)

- Owns request/response contracts (Pydantic schemas).
- Owns auth/deps and HTTP/WS status semantics.
- Converts request models to primitive payloads/patch dicts for services.
- Converts service outputs to response schemas.

### Service Layer (`backend/app/service`)

- Owns use-case orchestration and business rules.
- Owns transaction boundaries (`flush/commit/publish`) unless explicitly delegated.
- Calls repositories for reads/writes.
- Must not depend on API schema contracts for request/response shapes.

### Repository Layer (`backend/app/repository`)

- Owns SQLAlchemy queries, joins, pagination queries, and persistence helpers.
- Returns ORM/domain-shaped data to services.
- Contains no HTTP concerns and no endpoint contract logic.

## Dependency Rules

- Allowed:
  - `api -> service`
  - `service -> repository`
  - `repository -> models`
- Not allowed:
  - `service -> api schema` for request/response contracts
  - `repository -> api` or `repository -> service`
  - `api -> repository` (unless a temporary migration exception is documented)

## Migration Notes

- Legacy service modules that still import response/request schemas are tracked as technical debt in `issues/open_issues/`.
- New backend code should follow this architecture by default.
