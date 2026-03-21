# ADR-006: Hybrid Deployment Model (EC2 Docker + S3/CloudFront)

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

Backend and frontend have different runtime characteristics: backend is stateful/service-based; frontend and landing are static artifacts.

## Decision

Deploy using a hybrid model:
- Backend stack deployed on EC2 host via Docker Compose (including backend infra services)
- Frontend SPA deployed as static build to S3 and served via CloudFront
- Landing page deployed to S3 separately

## Evidence

- CI workflow deploy jobs: `.github/workflows/ci.yml`
- Compose runtime config: `docker-compose.yml`
- Nginx reverse proxy config: `nginx/nginx.conf`, `nginx/nginx.ssl.conf`
- Git history signals:
  - `2ddb2a6 feat(ci): add frontend auto-deploy to S3 + CloudFront`
  - `acac601 feat(infra): add backend deploy...`
  - `f012b1c chore(infra): add ai-service to docker-compose...`

## Consequences

- Static assets can scale/distribute independently from backend service lifecycle.
- Backend deploy remains simple (single host + compose) but depends on host-level operations.
