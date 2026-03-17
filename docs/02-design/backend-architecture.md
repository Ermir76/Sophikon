# Backend Architecture

## Layer Direction

`endpoint (api) → service (use case) → repository (db access) → models/db`

## Layer Responsibilities

### API Layer (`backend/app/api`)

- Owns request/response contracts (Pydantic schemas).
- Owns auth/deps and HTTP/WS status semantics.
- Converts request models to primitive payloads for services.
- Converts service outputs to response schemas.

### Service Layer (`backend/app/service`)

- Owns use-case orchestration and business rules.
- Owns transaction boundaries (`flush/commit`).
- Calls repository functions for reads/writes.
- Must not depend on API schema contracts.

### Repository Layer (`backend/app/repository`)

- Owns SQLAlchemy queries, joins, and persistence helpers.
- Returns ORM/domain-shaped data to services.
- No HTTP concerns, no endpoint contract logic.

### Agent Subsystem (`backend/app/service/agent/`)

A self-contained subsystem within the service layer. Owns the full PM Agent lifecycle:

- `loop.py` — orchestrates plan + execute phases
- `planner.py` — Phase 1: LLM call → structured plan
- `executor.py` — Phase 2: tool loop until stop
- `tool_registry.py` — 28 tool schemas + dispatch to service functions
- `context.py` — AgentContext per run (project, user, db, provider, model, api_key)
- `history.py` — conversation history, rolling summary, cross-session memory
- `streaming.py` — SSE event builders

The agent calls service functions directly (same process, no HTTP). It never touches the DB
outside of tool dispatch. The only cross-service HTTP call is to ai-service for single-turn
LLM completions.

### Cross-Service Boundary (ai-service)

Backend calls `ai-service` once per LLM turn:

```
POST http://ai-service/v1/complete
  in:  { messages, tools, system_prompt, provider, model, api_key }
  out: { text, tool_calls, stop_reason, usage }  (streaming)
```

ai-service handles provider-specific formatting only. All tool execution and loop logic
stays in backend.

## Dependency Rules

- Allowed: `api → service`, `service → repository`, `repository → models`, `agent → service functions`
- Not allowed: `service → api schema`, `api → repository` directly, `repository → service`
- Agent cross-service: `agent → ai-service` (HTTP, one call per LLM turn only)
