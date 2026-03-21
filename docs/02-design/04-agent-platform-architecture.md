# Agent Platform Architecture

**Version:** 1.0
**Date:** 2026-03-16

---

## Vision

The AI in Sophikon is not a chatbot. It is a **Project Manager Agent** — the first agent in a growing multi-agent platform. The human's role is the stakeholder: approve plans, give direction, make judgment calls. Everything else is the agent's job.

Future agents (Email, Notes, Code, HR, etc.) plug into the same platform. The PM Agent is the first tenant, not the only one.

---

## System Boundaries

```
┌──────────────────────────────────────────┐
│  Frontend                                │
│  Renders: reasoning, tool calls, plan,   │
│  text responses, UI actions              │
│  Sends: messages, approvals              │
└──────────────────┬───────────────────────┘
                   │ SSE + REST
┌──────────────────▼───────────────────────┐
│  Backend                                 │
│  Owns: agent loop, tool execution,       │
│  conversation history, proactive tasks   │
│  Calls ai-service once per LLM turn      │
└──────────────────┬───────────────────────┘
                   │ HTTP streaming
┌──────────────────▼───────────────────────┐
│  ai-service (Agent Platform)             │
│  - LLM provider adapters                 │
│  - MCP server (Phase 2)                  │
│  - A2A protocol (Phase 2)                │
│  - Future agent registry (Phase 3+)      │
└──────────────────────────────────────────┘
```

---

## Agent Loop

Two phases per user message:

**Phase 1 — Plan:** Agent receives the message, reasons over project context, and produces a structured plan of intended actions. Plan is presented to the user for approval or redirection before anything executes.

**Phase 2 — Execute:** Agent executes the approved plan via tool calls. Each tool call and its result streams to the frontend in real time. Destructive actions pause for explicit per-action confirmation regardless of plan approval.

---

## Tool Categories

| Category    | Approval required                       |
| ----------- | --------------------------------------- |
| Read        | None                                    |
| Write       | Plan approval                           |
| UI          | None                                    |
| Destructive | Plan approval + per-action confirmation |

Tools are the agent's only interface to the world. Every action traces to a tool call → service function → repository → DB.

---

## Communication Protocols

**Agent → Frontend:** SSE stream. Events cover reasoning tokens, tool calls, tool results, plan presentation, approval requests, and final response.

**Backend → ai-service:** Single HTTP call per LLM turn. Normalized request/response contract — provider-agnostic. ai-service translates to/from each provider's format.

**Agent → External tools:** MCP (Phase 2)

**Agent → Other agents:** A2A (Phase 2)

---

## ai-service Role

Single responsibility: single-turn LLM completion. No tool execution, no loop logic, no business logic.

Designed as a long-lived platform — provider adapters today, MCP server and A2A protocol in Phase 2, additional agent registrations in Phase 3+.

---

## Proactive Agent

A Celery-scheduled task shall run daily per active project. It analyzes project health autonomously, and if issues are found, posts findings and a proposed plan for the project manager to approve. Silent when the project is healthy.

---

## Context Strategy

Agent starts each turn with minimal context and queries what it needs via read tools. No pre-loading of project data into the system prompt. Conversation history is summarized beyond a rolling window to stay within context limits.

---

## Related Docs

- Implementation plan → `docs/03-implementation/agent-platform-plan.md`
- Backend module design → `02-backend-architecture.md`
- Data flow → `data-flow.md`
