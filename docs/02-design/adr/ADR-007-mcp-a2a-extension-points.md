# ADR-007: Keep MCP/A2A Extension Points in AI Service

- Status: [INFERRED]
- Date: 2026-03-20

## Context

Design docs define ai-service as the long-lived agent platform, not only a PM-agent adapter, with future protocol needs (MCP and A2A).

## Decision

Retain explicit extension points in ai-service for:
- MCP integration
- A2A integration
- future agent registry/routing

Current implementation keeps these as placeholders, while production traffic uses only `/v1/complete`.

## Evidence

- Design intent: `docs/02-design/agent-platform-architecture.md`
- Code placeholders:
  - `ai-service/app/mcp/__init__.py`
  - `ai-service/app/a2a/__init__.py`
- Git history signals around phased agent-platform docs (`4da0935`, `ab0cd65`, `c6b34ba`)

## Consequences

- Architectural direction stays explicit without forcing premature implementation.
- Additional protocol/runtime work is still required before MCP/A2A can be considered delivered.
