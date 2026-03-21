# AI Agent Standards

Version: 1.0
Date: 2026-03-20

## Purpose

Define mandatory standards for PM agent behavior, tool safety, approval flow, and platform extensibility.

## Architectural Boundary Standards

1. Backend owns agent loop orchestration, tool execution, and conversation persistence.
2. ai-service owns provider communication only (single-turn completion boundary).
3. ai-service must not execute domain tools or directly mutate product domain data.

## Agent Loop Standards

- Every user turn follows plan then execute flow.
- Plan must be presented before executing write/destructive intent.
- Destructive actions require explicit per-action confirmation, even after plan approval.
- Streamed agent events must remain ordered and parseable by frontend consumers.

## Tooling Standards

- Tools are the only execution interface for agent actions.
- Tool categories and approval policy:
- Read: no approval
- Write: plan approval required
- UI: no approval
- Destructive: plan approval plus per-action confirmation
- Every tool execution must be traceable (input, outcome, success/failure).

## Safety and Permission Standards

- Tool handlers must enforce role/object permissions before mutation.
- Reject or pause execution when approval state is missing or invalid.
- Never execute implicit destructive actions from unapproved free text.

## Context and Prompt Standards

- Start with minimal context and fetch needed data through read tools.
- Avoid dumping entire project state into prompts.
- Summarize long histories to control context size and cost.
- Prompt templates and reasoning behavior must remain deterministic where possible.

## Streaming Contract Standards

- Frontend-facing stream events should include:
- lifecycle (`start`, `done`, `error`)
- content deltas (`chunk`, `reasoning`)
- plan/approval events
- tool call/result events
- UI action events
- Event payloads must stay backward-compatible or be versioned.

## Proactive Agent Standards

- Scheduled proactive analysis must run through Celery scheduling.
- Proactive outputs must follow same approval and safety model as user-initiated flows.
- No autonomous destructive action without explicit user approval.

## Extensibility Standards

- MCP and A2A support must be introduced behind stable internal interfaces.
- New agent types must register through explicit registry/routing configuration.
- Cross-agent communication must preserve auth and audit constraints.

## Definition of Done (Agent Change)

- Boundary rules preserved (backend vs ai-service responsibilities).
- Approval and safety rules validated by tests.
- Stream event contract compatibility validated.
- Tool execution path is auditable.
- Related architecture and traceability docs updated.
