# Sophikon AI Service

Standalone AI brain service for Sophikon.

## Purpose

This service handles AI reasoning/orchestration for:
- chat
- task estimation
- contextual suggestions

Frontend does not call this service directly. Backend is the control plane and calls this service with service-to-service auth.

## Local Run

From `ai-service/`:

```bash
uv venv .venv
.venv\Scripts\activate
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

## Dependency Management

Use `uv` for all dependency changes:

```bash
uv add <package>
```

## Environment Variables

- `AI_SERVICE_SHARED_SECRET` (required for backend calls)
- `AI_MODE` (`mock` by default)
- `AI_MODEL_NAME` (default `sophikon-mock-v1`)
- `ENV` (`development` by default)
- `ANTHROPIC_API_KEY` (optional, live mode)
- `OPENAI_API_KEY` (optional, live mode)
- `GEMINI_API_KEY` (optional, live mode)

## API Endpoints

- `GET /health`
- `POST /v1/brain/chat` (SSE stream)
- `POST /v1/brain/estimate`
- `POST /v1/brain/suggestions`

## Backend Integration

Backend calls this service using:
- `X-AI-Service-Secret` header
- `AI_SERVICE_URL` configured in backend settings

Secrets must match between backend and ai-service.
