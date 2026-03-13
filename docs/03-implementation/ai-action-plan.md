# Plan: Sophikon AI Agent — Real Claude Integration with Tool Use

## Context

The AI infrastructure is already built (ai-service, backend endpoints, frontend panel, DB models)
but runs in mock mode — keyword matching, no real LLM. The goal is to connect real Claude API
and implement a full agentic loop where Claude can read and act on project data using tools,
with user-controlled approval for destructive actions.

This is a portfolio/LIA piece — it needs to be impressive: real streaming, real tool calls,
real approval flows, real UI actions.

---

## Architecture

```
Frontend (React)
  AiDockedPanel
  ├── ChatMessages + ToolCallIndicator (real-time: "Hämtar tasks...")
  ├── ApprovalDialog (AlertDialog, variant=destructive)
  └── ProfilePage → AI Settings tab (auto-approve toggles per tool)
          │
          │ SSE stream / POST /approvals/{id}
          ▼
Backend (FastAPI)  — orchestrates everything
  POST /projects/{id}/ai/chat  → agentic_loop()
  POST /projects/{id}/ai/approvals/{approval_id}  → resolve pending
  ai_service.py:
  ├── agentic_loop()     — multi-turn: send → tool_call → execute → continue
  ├── tool_executor()    — dispatches to existing services
  └── approval store     — asyncio.Future per pending approval (in-memory dict)
          │
          │ HTTP POST with project context + tool definitions
          ▼
AI Service (ai-service/)
  brain_service.py:
  ├── ClaudeProvider     — anthropic SDK, real streaming
  ├── tool_definitions   — 21 tools defined as Claude tool specs
  └── stream_with_tools  — yields tool_call / text / done events
```

---

## Tools (21 total)

### Read — always autonomous

| Tool                  | Calls                                          |
| --------------------- | ---------------------------------------------- |
| `get_tasks`           | `task_service.list_tasks()`                    |
| `get_task`            | `task_service.get_task_by_id()`                |
| `get_dependencies`    | `dependency_service.list_dependencies()`       |
| `get_critical_path`   | `scheduling_service.get_critical_path_tasks()` |
| `get_project_summary` | `ai_service.build_project_context()`           |
| `search_tasks`        | `task_repo.search()` (name/status/date filter) |
| `get_members`         | existing member query                          |

### Write — configurable (default: autonomous)

| Tool                 | Calls                                     |
| -------------------- | ----------------------------------------- |
| `create_task`        | `task_service.create_task()`              |
| `update_task`        | `task_service.update_task()`              |
| `indent_task`        | `task_hierarchy_service.indent_task()`    |
| `outdent_task`       | `task_hierarchy_service.outdent_task()`   |
| `reorder_task`       | `task_hierarchy_service.reorder_task()`   |
| `add_dependency`     | `dependency_service.create_dependency()`  |
| `calculate_schedule` | `scheduling_service.calculate_schedule()` |
| `bulk_create_tasks`  | `task_bulk_service.bulk_create_tasks()`   |

### Destructive — ALWAYS approval

| Tool                | Calls                                    |
| ------------------- | ---------------------------------------- |
| `delete_task`       | `task_service.soft_delete_task()`        |
| `delete_dependency` | `dependency_service.delete_dependency()` |

### UI actions — configurable (default: autonomous)

| Tool              | Frontend action              |
| ----------------- | ---------------------------- |
| `navigate`        | `router.push(path)`          |
| `highlight_tasks` | gantt/task list highlight    |
| `open_task`       | open task detail panel       |
| `filter_view`     | apply filter to current view |

---

## Agentic Loop

```
User sends message
  → Backend: save user message, load preferences, build project context
  → Backend calls ai-service: context + conversation history + tool definitions
  → ai-service: Claude API (streaming)
      → text chunks → SSE "chunk" events to frontend
      → tool_use block → SSE "tool_call" event to backend
  → Backend receives "tool_call":
      check user preferences:
      ├── always_approval (delete_*): stream "approval_required" + approval_id
      │     Frontend: ApprovalDialog appears
      │     User: approve/deny → POST /ai/approvals/{id}
      │     Backend: asyncio.Future resolved → continue or cancel
      └── autonomous: execute immediately
            stream "tool_result" to frontend ("✓ Created task 'Login UI'")
  → Backend sends tool result back to ai-service (next turn)
  → Claude continues → more text or more tools
  → Claude done → backend saves assistant message, stream "done"
```

---

## User AI Preferences

Stored in `user.preferences` JSONB (field already exists, no migration needed):

```json
{
  "ai": {
    "auto_approve": {
      "create_task": true,
      "update_task": true,
      "add_dependency": true,
      "indent_task": true,
      "outdent_task": true,
      "reorder_task": true,
      "calculate_schedule": true,
      "bulk_create_tasks": true,
      "navigate": true,
      "highlight_tasks": true,
      "open_task": true,
      "filter_view": true
    }
  }
}
```

---

## Implementation Phases

### Phase 1 — AI Service: Real Claude (ai-service/)

**Files:**

- `ai-service/pyproject.toml` — add `anthropic>=0.50.0`
- `ai-service/app/core/config.py` — no change needed (ANTHROPIC_API_KEY already there)
- `ai-service/app/schema/contracts.py` — add tool event types:
  - `ToolCallEvent(type="tool_call", tool_name, tool_input, tool_use_id)`
  - `ToolResultEvent(type="tool_result", tool_use_id, result)`
  - `ApprovalRequiredEvent(type="approval_required", approval_id, tool_name, tool_input, description)`
  - `UiActionEvent(type="ui_action", action, payload)`
- `ai-service/app/service/brain_service.py` — replace mock with:
  - `ClaudeProvider` class using `anthropic.AsyncAnthropic`
  - `TOOL_DEFINITIONS` list (21 tools as Anthropic tool specs with JSON schemas)
  - `stream_with_tools(request)` — real streaming with `client.messages.stream()`
  - Fallback to mock if `AI_MODE != "live"` or no API key

**System prompt structure:**

```
You are Sophikon AI — a project management assistant for {project_name}.
Today: {date}. Project status: {summary}.

You have access to tools to read and act on project data.
- Read tools: use freely without asking
- Write tools: execute unless user has restricted them
- Delete tools: ALWAYS present what you'll delete and wait

Be concise. Show your work. When taking actions, confirm what you did.
```

### Phase 2 — Backend: Tool Executor + Approval Flow

**Files:**

- `backend/app/service/ai_service.py` — add:
  - `_APPROVAL_STORE: dict[str, asyncio.Future]` — in-memory pending approvals
  - `tool_executor(tool_name, tool_input, db, project, user)` — dispatcher
  - `agentic_loop(db, project, user, body, preferences)` — multi-turn orchestration
    - Calls ai-service, receives SSE events
    - On `tool_call`: check approval, execute or pend
    - Streams all events to frontend
    - Loops until `done` event
  - `resolve_approval(approval_id, approved)` — resolves Future

- `backend/app/api/v1/endpoints/ai.py` — add:
  - `POST /projects/{project_id}/ai/approvals/{approval_id}` — calls resolve_approval
  - Update chat endpoint to call `agentic_loop` instead of `stream_chat`

- `backend/app/schema/ai.py` — add:
  - `AIApprovalRequest(approved: bool)`
  - `AIToolCallEvent`, `AIToolResultEvent`, `AIApprovalRequiredEvent`, `AIUiActionEvent`

### Phase 3 — Backend: User AI Preferences API

**Files:**

- `backend/app/api/v1/endpoints/users.py` — add:
  - `PATCH /users/me/ai-preferences` — updates `user.preferences["ai"]`
  - `GET /users/me/ai-preferences` — returns current AI preferences with defaults

- `backend/app/schema/auth.py` — add:
  - `AIPreferencesRequest(auto_approve: dict[str, bool])`
  - `AIPreferencesResponse(auto_approve: dict[str, bool])`

### Phase 4 — Frontend: Tool Feedback + Approval + Settings

**New files:**

- `features/ai/components/ApprovalDialog.tsx` — reuses `AlertDialog` (variant=destructive)
  - Shows: tool name, what it will do, Approve/Deny buttons
  - On approve: POST /ai/approvals/{id} with `{approved: true}`

- `features/ai/components/ToolCallIndicator.tsx` — shows tool execution in chat
  - "🔍 Hämtar tasks..." / "✓ Task skapad" / "✗ Avvisad"

**Modified files:**

- `features/ai/types.ts` — add all new event types (ToolCallEvent, ApprovalRequiredEvent, UiActionEvent, etc.)
- `features/ai/api/ai.service.ts` — handle new SSE event types, add approvals endpoint
- `features/ai/store/ai-panel-store.ts` — add `pendingApproval` state
- `features/ai/components/AiDockedPanel.tsx` — render ToolCallIndicators, mount ApprovalDialog, handle ui_action events (router.push, highlight etc.)
- `features/auth/pages/ProfilePage.tsx` — add "AI" tab with toggle switches per tool
- `features/auth/api/auth.service.ts` — add `getAiPreferences()`, `updateAiPreferences()`
- `features/auth/hooks/useAuth.ts` — add `useAiPreferences` hook

**UI action handling in AiDockedPanel:**

```typescript
case "ui_action":
  if (event.action === "navigate") router.push(event.payload.path)
  if (event.action === "highlight_tasks") emitHighlight(event.payload.task_ids)
  if (event.action === "open_task") setSelectedTask(event.payload.task_id)
  if (event.action === "filter_view") applyFilter(event.payload.filter)
```

---

## Critical Files (existing — must read before editing)

| File                                                    | Why                                         |
| ------------------------------------------------------- | ------------------------------------------- |
| `ai-service/app/service/brain_service.py`               | Full rewrite — understand current structure |
| `ai-service/app/schema/contracts.py`                    | Add tool events — must not break existing   |
| `backend/app/service/ai_service.py`                     | Major extension — orchestration lives here  |
| `backend/app/api/v1/endpoints/ai.py`                    | Add approval endpoint, update chat          |
| `frontend/src/features/ai/api/ai.service.ts`            | SSE parser — add new event types            |
| `frontend/src/features/ai/components/AiDockedPanel.tsx` | Main UI — add tool feedback                 |
| `frontend/src/features/auth/pages/ProfilePage.tsx`      | Add AI tab                                  |

## Reusable (call directly, don't rewrite)

| Service                      | Functions                                                                        |
| ---------------------------- | -------------------------------------------------------------------------------- |
| `task_service.py`            | `create_task`, `update_task`, `list_tasks`, `get_task_by_id`, `soft_delete_task` |
| `dependency_service.py`      | `create_dependency`, `delete_dependency`, `list_dependencies`                    |
| `scheduling_service.py`      | `calculate_schedule`, `get_critical_path_tasks`                                  |
| `task_hierarchy_service.py`  | `indent_task`, `outdent_task`, `reorder_task`                                    |
| `task_bulk_service.py`       | `bulk_create_tasks`, `bulk_update_tasks`                                         |
| `shared/ui/alert-dialog.tsx` | ApprovalDialog base                                                              |

---

## Verification

1. Set `AI_MODE=live` and `ANTHROPIC_API_KEY=sk-ant-...` in `ai-service/.env`
2. Start everything: `docker compose up -d`
3. Open a project → AI panel
4. Test read: "vilka tasks är försenade?" → Claude calls `get_tasks`, answers correctly
5. Test write (autonomous): "skapa en task 'Deploy to prod'" → task appears in list without dialog
6. Test destructive: "radera task X" → ApprovalDialog appears, user approves → task deleted
7. Test UI action: "visa kritisk väg på gantt" → navigates to Gantt + highlights critical path
8. Toggle off auto-approve for `create_task` in Profile → AI settings
9. Repeat step 5 → dialog appears this time
10. Test multi-tool: "analysera projektet och fixa schemaläggningen" → Claude calls get_tasks + get_critical_path + calculate_schedule in sequence
