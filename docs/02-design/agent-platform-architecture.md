# Sophikon Agent Platform — Architecture & Constitution

> Written: 2026-03-16
> Status: AUTHORITATIVE — this document governs all agent implementation decisions.
> Scope: PM Agent (Phase 1) + Agent Platform (foundation for all future agents)

---

## Vision

The AI in Sophikon is not a chatbot. It is a **Project Manager Agent** — the first agent in a
growing multi-agent platform. The human's role is the **stakeholder**: approve or reject plans,
give direction, make judgment calls. Everything else is the agent's job.

Future agents (Email Agent, Notes Agent, Code Agent, HR/Salary Agent, etc.) plug into the same
platform. The PM Agent is the first tenant, not the only one.

---

## Principles (The Constitution)

These rules are non-negotiable. Every implementation decision must be consistent with them.

### 1. The Agent Decides, The Human Approves

The agent does not ask "what should I do?" It decides, presents a plan, and executes after
approval. The human approves or redirects — not micromanages.

### 2. Provider Agnosticism Is Non-Negotiable

No part of the agent logic is coupled to Anthropic, OpenAI, or Google. Provider SDKs are used
as **clients only** — thin wrappers that translate a normalized contract to/from each provider's
API format. The loop, tools, approval flow, and all reasoning are provider-independent.
Users bring their own API keys. Gemini free tier must work end-to-end.

### 3. The Loop Lives In The Backend

The agentic loop (plan → execute → tool_call → tool_result → reason → repeat) lives in the
backend where it has direct DB access. No HTTP round-trips to execute tools. The ai-service
handles one job: single-turn LLM completion.

### 4. ai-service Is The Agent Platform, Not A Proxy

ai-service is a long-lived platform. Today it hosts the provider adapters and exposes MCP/A2A
protocols. Tomorrow it hosts Email Agent, Notes Agent, etc. It must be designed for extension,
not for the current PM use case only.

### 5. Open Standards Over Custom Protocols

- Agent ↔ External tools/Claude Code: **MCP** (Model Context Protocol)
- Agent ↔ Agent: **A2A** (Agent-to-Agent Protocol by Google)
- Agent ↔ Frontend: **SSE** (Server-Sent Events, existing)
- No custom inter-agent HTTP protocols.

### 6. Tools Are The Agent's Only Interface To The World

The LLM calls tools. Tools dispatch to service functions. Service functions call repositories.
Repositories query the DB. The full layer chain is preserved — agent code is not special.
Every action the LLM takes is traceable to a tool call, which is traceable to a service
function, which is traceable to a repository query.

### 7. Lazy Context — Agent Queries What It Needs

No pre-loading project data into the system prompt. The agent starts with a minimal context and
calls read tools to gather what it needs. This ensures accuracy (no stale data) and forces
explicit, auditable reasoning.

### 8. Plan Before Execute — Always

The agent never executes write/destructive actions without presenting a plan first. Read-only
tool calls are exempt. The plan approval is one gate — not per-tool approval (except destructive
actions which always require explicit per-action confirmation regardless).

### 9. Reasoning Is Visible

The agent's reasoning steps stream to the frontend in real time. The user sees what the agent
is thinking, what tools it is calling, and what results it received. No black box.

### 10. The Human Is Never Blocked Without Reason

Approval gates exist for plans and destructive actions. Everything else executes automatically.
The agent does not ask for permission on read operations, safe writes, or UI actions.

---

## System Boundaries

```
┌────────────────────────────────────────────────────────────────┐
│  Frontend (React SPA)                                          │
│  - Streams SSE events from backend                             │
│  - Renders: reasoning steps, tool calls, plan approval card,   │
│    text response, ui_actions                                   │
│  - Sends: chat messages, plan approval/redirect, destructive   │
│    action approval                                             │
└───────────────────────────┬────────────────────────────────────┘
                            │ SSE + REST
┌───────────────────────────▼────────────────────────────────────┐
│  Backend (FastAPI)                                             │
│  - Owns the PM Agent loop (plan + execute phases)              │
│  - Owns all tool execution (service → repository → DB, no HTTP)│
│  - Owns conversation history + context management              │
│  - Owns Celery proactive monitoring tasks                      │
│  - Calls ai-service for single-turn LLM completions only       │
└───────────────────────────┬────────────────────────────────────┘
                            │ HTTP (one call per LLM turn)
┌───────────────────────────▼───────────────────────────────────┐
│  ai-service (FastAPI — Agent Platform)                        │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Providers  │  │  MCP Server  │  │   A2A Protocol     │    │
│  │  Anthropic  │  │  (exposes PM │  │  (inter-agent      │    │
│  │  OpenAI     │  │   tools to   │  │   communication)   │    │
│  │  Gemini     │  │  Claude Code │  │                    │    │
│  │  Mock       │  │  etc.)       │  │                    │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
│                                                               │
│  Future agents register here:                                 │
│  Email Agent / Notes Agent / Code Agent / HR Agent / ...      │
└───────────────────────────────────────────────────────────────┘
```

---

## Backend: Agent Loop

### Directory Structure

```
backend/app/service/agent/
├── loop.py           — the while loop, owns plan + execute phases
├── planner.py        — Phase 1: LLM call → structured plan output
├── executor.py       — Phase 2: LLM turns with tool calls until stop
├── tool_registry.py  — all tool schemas + dispatch functions
├── context.py        — AgentContext dataclass (project_id, db, user, conversation)
├── history.py        — conversation history + rolling summary management
└── streaming.py      — SSE event builders for every event type
```

### Phase 1: Plan

```
1. Agent receives user message
2. Calls LLM with: system prompt + project summary (from get_project_summary) + user message
   — model is instructed to return a structured plan, not to execute anything
3. Plan = ordered list of intended actions with reasoning
4. Backend emits `plan` SSE event → frontend renders plan approval card
5. User: APPROVE / REDIRECT (with feedback text)
   — if REDIRECT: amend plan with user feedback, repeat Phase 1
   — if APPROVE: enter Phase 2
```

### Phase 2: Execute

```
while True:
    response = ai_service.complete_turn(messages, tools, provider, model, api_key)

    stream reasoning tokens live as `reasoning` events

    if response.stop_reason == "end_turn":
        stream final text as `chunk` events
        emit `done`
        break

    for tool_call in response.tool_calls:
        emit `tool_call` event (tool name + args shown live)

        if tool_call.name in DESTRUCTIVE_TOOLS:
            emit `approval_required`
            approved = await wait_for_human_decision()
            if not approved:
                result = ToolResult(success=False, message="User denied this action.")
            else:
                result = await execute_tool(tool_call, ctx)
        else:
            result = await execute_tool(tool_call, ctx)  # auto-execute, plan was approved

        emit `tool_result` event (result shown live, collapsible)
        messages.append(assistant_turn(response))
        messages.append(tool_result_message(tool_call.id, result))

    # loop — LLM sees every result and reasons over them
```

---

## Tool Registry

### Approval Policy

| Category          | Approval Required                                |
| ----------------- | ------------------------------------------------ |
| Read tools        | None — execute immediately                       |
| Write tools       | Plan approval (Phase 1 gate)                     |
| UI tools          | None — instant, no DB                            |
| Destructive tools | Plan approval + explicit per-action confirmation |

### Complete Tool Set (28 tools)

#### Read (14 tools)

| Tool                                   | Returns                                                                                   |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| `get_project_summary`                  | health %, overdue count, at-risk tasks, schedule status                                   |
| `get_tasks(filter?)`                   | full list — id, name, wbs_code, color, dates, %, priority, parent, assignees, is_critical |
| `get_task(task_id)`                    | single task, all fields including parent name/color, wbs path                             |
| `search_tasks(query)`                  | fuzzy match on name/notes — resolves partial names to task UUIDs                          |
| `get_dependencies`                     | all predecessor/successor pairs with type and lag                                         |
| `get_critical_path`                    | ordered critical path chain with float values                                             |
| `get_members`                          | members with roles, email, join date                                                      |
| `get_resources`                        | resources with type, max_units, cost rates                                                |
| `get_utilization`                      | per-resource load %, over-allocation flag, affected date ranges                           |
| `get_assignments(task_id?)`            | resource→task assignments, units, dates                                                   |
| `get_activity_log(limit?)`             | recent changes — what, who, when                                                          |
| `get_comments(entity_type, entity_id)` | comments on any task or project                                                           |
| `get_calendar`                         | working days, exceptions, inherited calendar                                              |
| `get_insights`                         | project insight signals from insights service                                             |

#### Write (12 tools)

| Tool                 | Action                                             |
| -------------------- | -------------------------------------------------- |
| `create_task`        | single task                                        |
| `bulk_create_tasks`  | up to 50 tasks in one call                         |
| `update_task`        | any field — name, dates, %, priority, color, notes |
| `add_dependency`     | predecessor → successor with type                  |
| `indent_task`        | WBS: make child of previous sibling                |
| `outdent_task`       | WBS: promote one level up                          |
| `reorder_task`       | change position, optionally change parent          |
| `calculate_schedule` | recalculate all dates, critical path, float        |
| `assign_resource`    | assign resource to task with units                 |
| `unassign_resource`  | remove resource assignment                         |
| `post_comment`       | agent posts comment on task or project             |
| `send_notification`  | send notification to a project member              |

#### Destructive (2 tools — always require per-action confirmation)

| Tool                | Requires                             |
| ------------------- | ------------------------------------ |
| `delete_task`       | task_id + reason shown to user       |
| `delete_dependency` | dependency_id + reason shown to user |

#### UI (4 tools — instant, no approval, no DB)

| Tool                        | Effect                                                        |
| --------------------------- | ------------------------------------------------------------- |
| `navigate(view)`            | switch view: overview/tasks/gantt/resources/calendar/reports  |
| `highlight_tasks(task_ids)` | visually highlight tasks in current view                      |
| `open_task(task_id)`        | open task detail panel                                        |
| `filter_view(filter)`       | apply filter: all/overdue/in_progress/completed/critical_path |

---

## SSE Event Contract

All events flow through `backend → frontend` over the existing SSE channel.
`approval_required` and `plan` events pause the stream and wait for frontend response.

| Event               | When                                  | Payload                                            |
| ------------------- | ------------------------------------- | -------------------------------------------------- |
| `start`             | conversation turn begins              | conversation_id, model                             |
| `plan`              | Phase 1 complete                      | steps: [{action, reason}], requires_approval: true |
| `plan_approved`     | user approved plan                    | —                                                  |
| `reasoning`         | agent thinking token                  | content (streaming)                                |
| `tool_call`         | agent invoking a tool                 | tool_name, tool_input                              |
| `tool_result`       | tool execution result                 | tool_name, success, data (collapsible)             |
| `approval_required` | destructive action needs confirmation | approval_id, tool_name, reason                     |
| `chunk`             | text response token                   | content                                            |
| `ui_action`         | frontend UI command                   | action, payload                                    |
| `done`              | turn complete                         | usage, model                                       |
| `error`             | failure                               | message                                            |

---

## ai-service: Agent Platform

### Immediate Responsibility (Phase 1)

Single-turn LLM completion adapter. One endpoint, called by backend once per agent turn.

```
POST /v1/complete
  Request:  { messages, tools, system_prompt, provider, model, api_key }
  Response: { text, tool_calls, stop_reason, usage }
```

Provider adapters translate the normalized contract to/from each provider's format.
No tool execution. No loop logic. No business logic.

### Directory Structure (current + platform additions)

```
ai-service/app/
├── core/
│   └── config.py
├── providers/               ← moved from service/providers/
│   ├── anthropic.py
│   ├── openai.py
│   ├── gemini.py
│   └── mock.py
├── mcp/                     ← MCP server (Phase 2)
│   ├── server.py            — exposes PM tools to Claude Code and other MCP clients
│   └── handlers.py          — calls backend tool execution via internal API
├── a2a/                     ← A2A protocol (Phase 2)
│   ├── server.py            — receives tasks from other agents
│   └── client.py            — sends tasks to other agents
├── agents/                  ← future agent registry (Phase 3+)
│   └── registry.py          — registered agents, their capabilities, routing
└── main.py
```

### Inter-Agent Communication Protocols

#### MCP (Model Context Protocol)

- ai-service exposes an MCP server
- Claude Code, Cursor, or any MCP-compatible client can connect
- PM tools exposed as MCP resources/tools: read project state, create tasks, update progress
- Use case: developer finishes a task in Claude Code → marks it done via MCP → PM agent
  recalculates schedule automatically

#### A2A (Agent-to-Agent Protocol — Google open standard)

- PM Agent delegates to sub-agents via A2A
- Example: "summarize emails about project delays" → Email Agent (A2A) → result
- Example: "check notes from last standup" → Notes Agent (A2A) → result
- Each future agent registers with ai-service and declares its A2A capabilities

---

## Proactive Agent (Celery)

```
backend/app/tasks/
└── agent_monitor.py     ← Celery beat tasks
```

### Daily Health Check

```
Trigger: Celery beat, daily per active project
Flow:
  1. Agent starts in proactive mode (no user message)
  2. Calls: get_project_summary + get_tasks(filter=overdue) + get_critical_path
  3. Analyzes: overdue tasks, resource conflicts, schedule slippage, dependency violations
  4. If issues found:
     a. Builds action plan
     b. Posts comment on project: agent explains findings + proposed plan
     c. Sends notification to project manager with plan + approve button
     d. If manager approves (via notification action): agent executes the plan
     e. If no response in 24h: re-notify once, then archive the proposal
  5. If project is healthy: silent (no noise)
```

---

## Context & History Management

### Per-Turn Context Strategy

- Agent starts with no pre-loaded project data
- First tool call is always `get_project_summary` unless message makes the intent obvious
- Agent queries details lazily — only what it needs to answer the question or execute the plan

### Conversation History

- Last 20 messages kept verbatim in context window
- Messages older than 20: replaced by a rolling summary
- Rolling summary generated by LLM: "summarize these N messages in 3-5 sentences preserving key decisions and context"
- Summary stored in `AIConversation.summary` (new column, migration required)
- Per-turn token cost tracked in existing `AIUsage` model

### System Prompt Per Provider

- Same logical system prompt, adapted per provider's formatting requirements
- Instructs agent: role (PM Agent), behavior (plan first), approval policy, tool usage patterns
- Injected with current date, project name, user name at runtime

---

## What Changes

| Component                                          | Change                                                         |
| -------------------------------------------------- | -------------------------------------------------------------- |
| `backend/app/service/agent/`                       | **New** — entire agent system                                  |
| `backend/app/service/ai_service.py`                | **Gutted** — becomes thin adapter calling loop.py              |
| `backend/app/api/v1/endpoints/ai.py`               | **Extended** — plan approval endpoint added                    |
| `backend/app/tasks/agent_monitor.py`               | **New** — proactive Celery tasks                               |
| `ai-service/app/service/brain_service.py`          | **Gutted** — single-turn completion only                       |
| `ai-service/app/service/providers/tool_catalog.py` | **Deleted** — moves to backend tool_registry.py                |
| `ai-service/app/schema/contracts.py`               | **Simplified** — completion contract only                      |
| `ai-service/app/mcp/`                              | **New** — MCP server (Phase 2)                                 |
| `ai-service/app/a2a/`                              | **New** — A2A protocol (Phase 2)                               |
| `backend/app/service/contracts/ai.py`              | **Expanded** — plan, reasoning, new event types                |
| `frontend/src/features/ai/`                        | **Extended** — plan card, reasoning steps, richer tool display |
| All existing services (task, resource, etc.)       | **Untouched**                                                  |
| All existing models                                | **Untouched** except `AIConversation.summary` column added     |

---

## Implementation Phases

### Phase 1 — Real Agent (backend loop + complete tool set)

Backend agent loop. Plan + execute. Full tool registry (28 tools). Provider-agnostic
single-turn ai-service. SSE event contract. Frontend plan card + reasoning display.
Proactive Celery monitoring.

### Phase 2 — Agent Platform (MCP + A2A)

MCP server in ai-service. A2A protocol foundation.
Claude Code integration via MCP. Agent registry.

### Phase 3 — Sub-Agents

Email Agent, Notes Agent, HR Agent — each registering into ai-service.
PM Agent delegates via A2A.

---

_This document is the source of truth for all agent implementation decisions._
_Update it when decisions change — do not let code diverge silently from this spec._
