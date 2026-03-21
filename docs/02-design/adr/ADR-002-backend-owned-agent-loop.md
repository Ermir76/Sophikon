# ADR-002: Backend Owns Agent Loop; AI Service Is Single-Turn Adapter

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

The PM agent needs direct access to business tools and DB-backed project state while remaining provider-agnostic for model calls.

## Decision

Place the agent loop in backend (`plan -> execute -> tools -> repeat`) and keep `ai-service` focused on provider-specific single-turn completion streaming.

## Evidence

- Backend loop modules: `backend/app/service/agent/{loop,planner,executor,tool_registry}.py`
- Backend to ai-service call path: `backend/app/service/ai_service.py` (`_complete_from_service`)
- ai-service surface: `ai-service/app/main.py` with `/v1/complete`
- Git history signals:
  - `fda11cc feat(agent): implement backend PM agent loop subsystem (Phase 2)`
  - `8422b5e feat(ai-service): simplify to single-turn completion adapter (Phase 3)`

## Consequences

- Tool execution remains close to domain services and DB transactions.
- Provider changes are isolated in ai-service adapters.
- Cross-service latency is limited to LLM turns, not every tool call.
