# Deployment Topology

**Version:** 1.0
**Date:** 2026-02-06

---

## Local Development

All services run via Docker Compose:

| Service      | Image               | Port        |
| ------------ | ------------------- | ----------- |
| `postgres`   | PostgreSQL 18       | 5433 → 5432 |
| `redis`      | Redis 7             | 6379        |
| `backend`    | FastAPI             | 8000        |
| `ai-service` | FastAPI             | 8010        |
| `nginx`      | Reverse proxy       | 80, 443     |
| `mailpit`    | Dev SMTP (optional) | 1025, 8025  |

Startup order: `postgres` + `redis` + `ai-service` → `backend` → `nginx`.

---

## Container Runtime

**Backend** — on start, runs `alembic upgrade head` then `uvicorn app.main:app --workers 4 --proxy-headers`. Migrations always run at boot. No Celery worker in this container.

**AI Service** — single process: `uvicorn app.main:app --host 0.0.0.0 --port 8010`. No migrations, no workers. Requires:

- `AI_MODE` — LLM provider (`anthropic` | `openai` | `gemini` | `mock`)
- `AI_SERVICE_SHARED_SECRET` — all requests require `X-AI-Service-Secret` header matching backend config

**Celery** — worker and beat run as separate processes (not in docker-compose). Must be started manually in development.

---

## Reverse Proxy (Nginx)

- Upstream: `backend:8000`
- WebSocket upgrade headers enabled
- Max request size: 10MB
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- SSL: HTTP → HTTPS redirect, TLS for `api.sophikon.org`, HSTS enabled

---

## Production

| Layer        | Infrastructure                                                     |
| ------------ | ------------------------------------------------------------------ |
| Backend      | EC2 + Docker Compose (backend, ai-service, postgres, redis, nginx, celery) |
| Frontend     | S3 + CloudFront                                                            |
| Landing page | S3                                                                         |

`backend` and `ai-service` run as separate containers on the same EC2. Each has its own isolated filesystem and Python environment — no shared state, no dependency conflicts. This gives architectural separation without the operational overhead of a second EC2.

Upgrade path: extract `ai-service` to its own EC2 when AI traffic justifies independent scaling.

---

## CI/CD

On PR → run backend tests (Ruff + migrations + pytest) against ephemeral Postgres.

On merge to `main` → tests pass → deploy:

- Backend: SSH to EC2, `docker compose up -d --build`
- Frontend: build SPA, sync to S3, invalidate CloudFront
- Landing: sync to S3
- Discord notification on outcome
