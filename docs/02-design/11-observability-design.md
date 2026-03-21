# Observability Design

**Version:** 1.0
**Date:** 2026-02-06

---

## Logging

All backend modules use `logging.getLogger(__name__)`. Log levels:

- `info` — normal operational events
- `warning` — recoverable failures, unexpected but non-fatal state
- `exception` — unhandled errors with full stack trace

The global FastAPI exception handler catches unhandled exceptions, logs the stack trace, and returns a sanitized 500 response — no internal details leak to the client.

Critical paths that must log failures: realtime publish, WebSocket pub/sub, auth/OAuth, email delivery, agent planner/executor/tools, AI provider calls.

---

## AI Usage Tracking

Every AI feature call persists token usage and estimated cost in the `AIUsage` table, scoped to conversation and message. Streaming completions propagate usage via `done` events before the stream closes.

---

## Redis Operational Channels

| Channel                       | Purpose                        |
| ----------------------------- | ------------------------------ |
| `sophikon:realtime`           | Project-scoped mutation events |
| `sophikon:user_notifications` | Per-user notification fan-out  |

Presence state is stored in Redis hash keys `sophikon:presence:{project_id}` with TTL refresh on each heartbeat.

Events are queued in DB session context and only published to Redis after a successful DB commit — no stale pushes on rollback.

---

## Celery

Schedules:

- Daily deadline notification task
- Daily proactive project health check

Task failures are visible via process logs. Each task logs per-item failures internally. No distributed tracing or queue depth monitoring in V1.0 — plain logs are sufficient at this scale.

---

## Health Endpoints

| Service    | Endpoint      | Returns               |
| ---------- | ------------- | --------------------- |
| Backend    | `GET /`       | Basic status          |
| AI Service | `GET /health` | `{ status, ai_mode }` |

Readiness checks for DB and Redis dependencies are deferred to V1.1.
