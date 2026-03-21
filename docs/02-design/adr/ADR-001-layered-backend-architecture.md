# ADR-001: Layered Backend Architecture (API -> Service -> Repository)

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

The backend has grown across auth, org/project/task domains, scheduling, notifications, and AI. We need stable boundaries so transport logic, business rules, and SQL do not mix.

## Decision

Adopt and enforce a layered direction:
- API endpoints own HTTP/WS contracts and auth/deps
- Services own use-case orchestration and transaction behavior
- Repositories own SQLAlchemy query/persistence concerns

Direct `api -> repository` and `repository -> service` coupling is avoided.

## Evidence

- Code layout: `backend/app/api`, `backend/app/service`, `backend/app/repository`
- Existing docs: `docs/02-design/backend-architecture.md`
- Git history signal: `48216fc refactor(backend): introduce repository layer for core domains`

## Consequences

- Domain changes are mostly localized to service/repository modules.
- API contract changes do not require SQL-level rewrites in endpoint files.
