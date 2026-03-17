# Agent Platform — Implementation Plan

> Written: 2026-03-17
> Architecture reference: `docs/05-agent-platform/AGENT_ARCHITECTURE.md`
> 3 weeks, solo. Goal: real agent, not a prototype.

---

## What Already Exists (Do Not Rebuild)

- All 28 DB models including `AIConversation`, `AIMessage`, `AIUsage`
- All service functions: task, dependency, assignment, resource, scheduling, comments, notifications, activity
- All 98 HTTP endpoints
- Frontend AI feature: `AiDockedPanel`, `ApprovalDialog`, `ToolCallIndicator`, `useAi`, `ai-panel-store`, `ai.service.ts`
- ai-service providers: `anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py`, `mock_provider.py`, `message_builders.py`
- SSE streaming infrastructure end-to-end

Everything above is kept. The agent is built on top of it, not instead of it.

---

## What Gets Rebuilt / Replaced

| File                                                    | Action                    | Reason                                   |
| ------------------------------------------------------- | ------------------------- | ---------------------------------------- |
| `backend/app/service/ai_service.py`                     | Gutted → thin adapter     | No real loop, no tool feedback           |
| `ai-service/app/service/brain_service.py`               | Gutted → single-turn only | Was doing orchestration it shouldn't own |
| `ai-service/app/service/providers/tool_catalog.py`      | Deleted                   | Moves to backend `tool_registry.py`      |
| `backend/app/service/contracts/ai.py`                   | Expanded                  | New event types needed                   |
| `frontend/src/features/ai/types.ts`                     | Expanded                  | New event types                          |
| `frontend/src/features/ai/components/AiDockedPanel.tsx` | Extended                  | Plan card, reasoning steps               |
| `frontend/src/features/ai/hooks/useAi.ts`               | Extended                  | Plan approval flow, resume               |
| `frontend/src/features/ai/store/ai-panel-store.ts`      | Extended                  | Conversation status, plan state          |
| `frontend/src/features/ai/api/ai.service.ts`            | Extended                  | Plan approval call, resume call          |

---

## Phase 1 — Database Foundation

**Goal:** Add the 3 missing pieces to the DB. Everything else depends on this.

### 1.1 — Migrate `AIConversation`

Add 3 columns:

```python
# summary: rolling intra-session compressed history
summary: Mapped[str | None] = mapped_column(Text, nullable=True)

# status: where is this conversation right now
status: Mapped[str] = mapped_column(
    String(30),
    nullable=False,
    server_default="idle",
    comment="idle | awaiting_plan_approval | executing | awaiting_approval | interrupted"
)

# mode: who triggered this conversation
mode: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    server_default="chat",
    comment="chat | proactive"
)
```

### 1.2 — New table `AgentProjectMemory`

One row per project. Agent writes to this. Persists across all sessions.

```python
class AgentProjectMemory(Base):
    __tablename__ = "agent_project_memory"

    id: UUID (pk)
    project_id: UUID (FK project.id CASCADE, unique)
    content: Text   # max ~600 tokens, agent-curated key decisions/patterns
    updated_at: TIMESTAMP
    updated_by_conversation_id: UUID (FK ai_conversation.id, nullable)
```

### 1.3 — Alembic migration

One migration file. Columns first, then new table.
No changes to any other model.

---

## Phase 2 — Backend Agent Loop

**Goal:** The real agent lives here. This is the core of everything.

### 2.1 — New directory structure

```
backend/app/service/agent/
├── __init__.py
├── context.py        ← AgentContext dataclass
├── history.py        ← conversation history + rolling summary logic
├── tool_registry.py  ← all 28 tool schemas + dispatch functions
├── streaming.py      ← SSE event builders
├── planner.py        ← Phase 1: LLM call → structured plan
├── executor.py       ← Phase 2: tool loop until stop
└── loop.py           ← orchestrates plan + execute, exposes run_agent()
```

### 2.2 — `context.py`

```python
@dataclass
class AgentContext:
    project_id: UUID
    user_id: UUID
    conversation_id: UUID
    db: AsyncSession
    provider: str       # anthropic | openai | gemini | mock
    model: str
    api_key: str        # user's own key
```

No global state. Every agent run gets its own context.

### 2.3 — `history.py`

Responsibilities:

- Load conversation messages from DB (`AIMessage` rows)
- Build the messages list for the LLM call (summary + last 20 verbatim)
- Append new messages to DB after each turn
- Trigger rolling summary when messages exceed 20 (LLM call to compress oldest 10)
- Load/save `AgentProjectMemory` for cross-session context

```
Context window sent to LLM each turn:
  [system prompt with project memory injected]
  [summary message if exists]
  [last 20 AIMessage rows, verbatim]
  [current user message]
```

### 2.4 — `tool_registry.py`

Two things per tool:

1. **Schema** (what the LLM sees) — moved and expanded from `ai-service/tool_catalog.py`
2. **Dispatch** (what runs when LLM picks it) — calls existing service functions directly

```python
TOOL_SCHEMAS: list[dict] = [...]   # 28 tool definitions for LLM

async def execute_tool(
    tool_name: str,
    tool_input: dict,
    ctx: AgentContext,
) -> ToolResult:
    match tool_name:
        case "get_tasks":
            tasks = await task_service.list_tasks(ctx.db, ctx.project_id, ...)
            return ToolResult(success=True, data=serialize_tasks(tasks))
        case "create_task":
            task = await task_service.create_task(ctx.db, ctx.project_id, ...)
            return ToolResult(success=True, data=serialize_task(task))
        case "get_resources":
            resources = await resource_service.list_resources(ctx.db, ctx.project_id)
            return ToolResult(success=True, data=serialize_resources(resources))
        case "assign_resource":
            ...
        case "post_comment":
            await comment_service.create_comment(ctx.db, ...)
            return ToolResult(success=True, data={"posted": True})
        case "send_notification":
            await notification_service.create_notification(ctx.db, ...)
            return ToolResult(success=True, data={"sent": True})
        case "navigate" | "highlight_tasks" | "open_task" | "filter_view":
            # UI tools — no DB, just return the action for streaming
            return ToolResult(success=True, data=tool_input, is_ui_action=True)
        ...
```

Tool results include full rich data — all fields the frontend might need (color, wbs_code, parent, etc.).

**Destructive tools check:**

```python
DESTRUCTIVE_TOOLS = {"delete_task", "delete_dependency"}
```

### 2.5 — `streaming.py`

One function per event type. Returns `dict` ready to be SSE-encoded.

```python
def event_start(conversation_id, model) -> dict
def event_plan(steps: list[PlanStep]) -> dict
def event_plan_approved() -> dict
def event_reasoning(content: str) -> dict
def event_tool_call(tool_name: str, tool_input: dict) -> dict
def event_tool_result(tool_name: str, result: ToolResult) -> dict
def event_approval_required(approval_id: str, tool_name: str, reason: str) -> dict
def event_chunk(content: str) -> dict
def event_ui_action(action: str, payload: dict) -> dict
def event_done(usage: dict) -> dict
def event_error(message: str) -> dict
```

### 2.6 — `planner.py`

Single LLM call. Instruction: produce a structured plan, do not execute.

```
System: "You are a PM agent. Given the user's request and project state,
         produce a numbered plan of what you intend to do. Be specific.
         Do NOT execute anything. Return only the plan."

Input: user message + get_project_summary() result (pre-fetched)

Output: PlanResponse
  steps: [{ action: str, reason: str }]
  needs_execution: bool  # false if it's a pure read/answer question
```

If `needs_execution` is false (user just asked a question) → skip Phase 2 plan approval,
go straight to execute phase (which will just answer with text + read tools).

### 2.7 — `executor.py`

The actual agentic while loop.

```python
async def execute(
    ctx: AgentContext,
    messages: list,
    approved_plan: PlanResponse | None,
) -> AsyncGenerator[dict, None]:

    while True:
        # call ai-service for one turn
        response = await ai_service_client.complete(
            messages=messages,
            tools=TOOL_SCHEMAS,
            system_prompt=build_system_prompt(ctx),
            provider=ctx.provider,
            model=ctx.model,
            api_key=ctx.api_key,
        )

        # stream reasoning tokens
        async for token in response.reasoning_tokens:
            yield event_reasoning(token)

        # if LLM is done
        if response.stop_reason == "end_turn":
            for token in response.text_tokens:
                yield event_chunk(token)
            yield event_done(response.usage)
            break

        # process tool calls
        assistant_turn_appended = False
        for tool_call in response.tool_calls:
            yield event_tool_call(tool_call.name, tool_call.input)

            if tool_call.name in DESTRUCTIVE_TOOLS:
                approval_id = str(uuid4())
                yield event_approval_required(approval_id, tool_call.name, tool_call.input.get("reason", ""))
                approved = await wait_for_approval(approval_id)
                if not approved:
                    result = ToolResult(success=False, message="User denied this action.")
                else:
                    result = await execute_tool(tool_call.name, tool_call.input, ctx)
            else:
                result = await execute_tool(tool_call.name, tool_call.input, ctx)

            if result.is_ui_action:
                yield event_ui_action(tool_call.name, result.data)

            yield event_tool_result(tool_call.name, result)

            if not assistant_turn_appended:
                messages.append(build_assistant_turn(response))
                assistant_turn_appended = True

            messages.append(build_tool_result_turn(tool_call.id, result))

        # persist messages to DB
        await history.save_turn(ctx, messages[-len(response.tool_calls)*2-1:])

        # loop — LLM sees results and reasons over them
```

### 2.8 — `loop.py`

Orchestrates everything. This is what `ai_service.py` calls.

```python
async def run_agent(
    ctx: AgentContext,
    user_message: str,
) -> AsyncGenerator[dict, None]:

    yield event_start(ctx.conversation_id, ctx.model)

    # update conversation status
    await set_conversation_status(ctx, "executing")

    # load history
    messages = await history.load(ctx)
    messages.append({"role": "user", "content": user_message})

    # Phase 1: plan
    plan = await planner.plan(ctx, messages)

    if plan.needs_execution:
        yield event_plan(plan.steps)
        # pause — wait for frontend approval
        await set_conversation_status(ctx, "awaiting_plan_approval")
        approved = await wait_for_plan_approval(ctx.conversation_id)
        if not approved.approved:
            # user redirected — amend and re-plan
            messages.append({"role": "user", "content": approved.feedback})
            plan = await planner.plan(ctx, messages)
            yield event_plan(plan.steps)
            await wait_for_plan_approval(ctx.conversation_id)
        yield event_plan_approved()
        await set_conversation_status(ctx, "executing")

    # Phase 2: execute
    async for event in executor.execute(ctx, messages, plan):
        yield event

    # end — update memory, status
    await memory.update_project_memory(ctx, messages)
    await set_conversation_status(ctx, "idle")
    await history.maybe_summarize(ctx)
```

### 2.9 — Update `ai_service.py`

Gut everything. Keep only:

- `prepare_chat_stream()` → calls `loop.run_agent()`
- `resolve_approval()` → unchanged (already works)
- Add `resolve_plan_approval()` → new, same pattern as approval store

### 2.10 — Update `endpoints/ai.py`

Add:

- `POST /projects/{project_id}/ai/plan-approval/{conversation_id}` — approve or redirect plan
- `GET /projects/{project_id}/ai/conversations` — list conversations for resume
- `GET /projects/{project_id}/ai/conversations/{conversation_id}` — load conversation history

---

## Phase 3 — ai-service Simplification

**Goal:** Strip ai-service to single-turn completion. Keep providers intact.

### 3.1 — New endpoint

```
POST /v1/complete
  Request:
    messages: list
    tools: list
    system_prompt: str
    provider: str
    model: str
    api_key: str

  Response (streaming):
    reasoning tokens → type: "reasoning"
    text tokens      → type: "chunk"
    tool calls       → type: "tool_call"
    done             → type: "done", usage: {...}
```

### 3.2 — Delete

- `brain_service.py` orchestration logic (keep only as thin router to providers)
- `tool_catalog.py` (fully deleted — lives in backend now)
- Estimate and suggestions heuristics (replaced by real LLM calls in backend)
- Old `/v1/brain/chat` endpoint (replaced by `/v1/complete`)

### 3.3 — Keep

- All provider files: `anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py`, `mock_provider.py`
- `message_builders.py` — normalizes message format per provider
- `tool_adapters.py` — normalizes tool schemas per provider
- `model_catalog.py` — available models per provider
- `config.py`

### 3.4 — Add stubs (empty, for future)

```
ai-service/app/mcp/__init__.py     # MCP server — Phase 2 of platform
ai-service/app/a2a/__init__.py     # A2A protocol — Phase 2 of platform
```

---

## Phase 4 — Frontend

**Goal:** The UI reflects what the agent is actually doing. User sees thinking, tools, plans.

### 4.1 — `types.ts` — new event types

```typescript
export type AiChatEvent =
  | { type: "start"; conversation_id: string; model: string }
  | { type: "plan"; steps: PlanStep[] }
  | { type: "plan_approved" }
  | { type: "reasoning"; content: string }
  | {
      type: "tool_call";
      tool_name: string;
      tool_input: Record<string, unknown>;
    }
  | { type: "tool_result"; tool_name: string; success: boolean; data: unknown }
  | {
      type: "approval_required";
      approval_id: string;
      tool_name: string;
      reason: string;
    }
  | { type: "chunk"; content: string }
  | { type: "ui_action"; action: string; payload: Record<string, unknown> }
  | { type: "done"; usage: AiUsageMeta }
  | { type: "error"; message: string };

export type PlanStep = { action: string; reason: string };
```

### 4.2 — New components

**`PlanApprovalCard.tsx`**

- Shows numbered list of plan steps with reasons
- Two buttons: "Approve & Execute" / "Redirect" (with text input for feedback)
- Renders inside `AiDockedPanel` when a `plan` event arrives
- Blocks the chat input until resolved

**`ReasoningStep.tsx`**

- Collapsible bubble: "Thinking..." while streaming, expands to show reasoning text
- Visual distinction from regular text (muted, italic, indented)

**`ToolCallRow.tsx`** (replace/extend `ToolCallIndicator`)

- Shows tool name + collapsed args
- When `tool_result` arrives: shows success/error + collapsed result data
- Click to expand full result

### 4.3 — `ai-panel-store.ts` — new state

```typescript
interface AiPanelState {
  // existing...
  conversationId: string | null;
  conversationStatus:
    | "idle"
    | "awaiting_plan_approval"
    | "executing"
    | "awaiting_approval"
    | "interrupted";
  pendingPlan: PlanStep[] | null;
  isThinking: boolean; // reasoning in progress
  reasoningText: string; // accumulated reasoning tokens
}
```

### 4.4 — `AiDockedPanel.tsx` — new event handling

```typescript
case "plan":
  store.setPendingPlan(event.steps)
  store.setConversationStatus("awaiting_plan_approval")
  // render PlanApprovalCard above chat input

case "reasoning":
  store.appendReasoningToken(event.content)
  // render ReasoningStep (streaming)

case "tool_call":
  // add ToolCallRow in message list, pending result

case "tool_result":
  // update matching ToolCallRow with result

case "plan_approved":
  store.setPendingPlan(null)
  store.setConversationStatus("executing")
```

### 4.5 — `useAi.ts` — plan approval flow

```typescript
const approvePlan = async (approved: boolean, feedback?: string) => {
  await aiService.resolvePlanApproval(projectId, conversationId, {
    approved,
    feedback,
  });
  store.setConversationStatus(
    approved ? "executing" : "awaiting_plan_approval",
  );
};
```

### 4.6 — Conversation resume

**`useConversations.ts`** (new hook)

```typescript
// loads list of conversations for the project
// lets user select a previous conversation to resume
const { conversations, loadConversation } = useConversations(projectId);
```

**`AiDockedPanel.tsx`** — conversation selector

- Small dropdown/list at top of panel showing past conversations
- Click → loads history, sets `conversationId`, resumes
- Status `awaiting_plan_approval` → shows plan card immediately on load
- Status `interrupted` → shows "Session was interrupted. Continue?" banner

---

## Phase 5 — Proactive Agent (Celery)

**Goal:** Agent runs autonomously, proactively monitors projects.

### 5.1 — New file: `backend/app/tasks/agent_monitor.py`

```python
@celery_app.task
async def daily_project_health_check():
    """Runs every morning for every active project."""
    projects = await get_active_projects()
    for project in projects:
        await run_proactive_check(project.id)

async def run_proactive_check(project_id: UUID):
    # create a system-owned conversation (mode="proactive")
    conversation = await create_proactive_conversation(project_id)

    ctx = AgentContext(
        project_id=project_id,
        user_id=SYSTEM_USER_ID,
        conversation_id=conversation.id,
        mode="proactive",
        ...
    )

    # agent analyses project state
    findings = await agent_loop.run_proactive_analysis(ctx)

    if findings.has_issues:
        # post a comment on the project
        await comment_service.create_comment(
            entity_type="project",
            entity_id=project_id,
            content=findings.summary,
            author="AI Agent",
        )
        # notify project manager
        await notification_service.create_notification(
            user_id=project.owner_id,
            title="AI Agent found issues",
            body=findings.summary,
            action_url=f"/projects/{project_id}?agent_proposal={conversation.id}",
        )
        # manager can approve from notification → triggers execution
```

### 5.2 — Celery beat schedule

```python
# backend/app/core/celery.py
beat_schedule = {
    "daily-project-health-check": {
        "task": "app.tasks.agent_monitor.daily_project_health_check",
        "schedule": crontab(hour=8, minute=0),  # 8am daily
    },
}
```

---

## Phase 6 — Contracts & Serialization

**Goal:** Tool results are rich. Agent can answer any question about any entity.

### 6.1 — Tool result serializers

Each read tool returns complete data. No missing fields.

`get_task` returns:

```json
{
  "id": "...",
  "name": "Design Phase",
  "wbs_code": "1.2",
  "color": "#3B82F6",
  "percent_complete": 45,
  "start_date": "2026-03-10",
  "finish_date": "2026-03-24",
  "duration": 960,
  "priority": 600,
  "is_critical": true,
  "is_milestone": false,
  "notes": "...",
  "parent_id": "...",
  "parent_name": "Frontend",
  "assignees": [{ "name": "Alice", "role": "developer", "units": 100 }]
}
```

`get_resources` returns:

```json
[
  {
    "id": "...",
    "name": "Alice",
    "type": "work",
    "max_units": 100,
    "cost_per_hour": 75.0,
    "current_utilization": 85,
    "is_over_allocated": false
  }
]
```

### 6.2 — Update `backend/app/service/contracts/ai.py`

Add all new event dataclasses (`PlanEvent`, `ReasoningEvent`, `ToolCallEvent`, `ToolResultEvent`, etc.)
and the new `AgentContext`, `ToolResult`, `PlanStep`, `PlanResponse` dataclasses.

---

## Execution Order (3 weeks)

### Week 1

| Day | Task                                                                                                                                    |
| --- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Phase 1: DB migration (3 columns + 1 table)                                                                                             |
| 1   | Phase 6: Tool result serializers (get_task, get_tasks, get_resources, get_utilization, get_assignments, get_activity_log, get_comments) |
| 2-3 | Phase 2.1-2.5: `context.py`, `history.py`, `tool_registry.py`, `streaming.py`                                                           |
| 4-5 | Phase 2.6-2.8: `planner.py`, `executor.py`, `loop.py`                                                                                   |

### Week 2

| Day | Task                                                                 |
| --- | -------------------------------------------------------------------- |
| 1   | Phase 2.9-2.10: Update `ai_service.py` + `endpoints/ai.py`           |
| 2   | Phase 3: Gut ai-service, new `/v1/complete` endpoint                 |
| 3-4 | Phase 4.1-4.5: Frontend types, new components, store, event handling |
| 5   | Phase 4.6: Conversation resume UI                                    |

### Week 3

| Day | Task                                                            |
| --- | --------------------------------------------------------------- |
| 1-2 | Phase 5: Celery proactive agent                                 |
| 3   | Integration testing end-to-end (Gemini free tier)               |
| 4   | Polish: error states, interrupted session handling, edge cases  |
| 5   | Demo prep: "fix my slipping project" flow works start to finish |

---

## Definition of Done

- [ ] Agent runs a real while loop — LLM sees every tool result
- [ ] Plan phase works — agent proposes, user approves, agent executes
- [ ] Reasoning streams live to frontend
- [ ] Tool calls and results visible in real time
- [ ] Conversation persists — user can leave and resume
- [ ] Conversation status tracked correctly (idle/executing/awaiting/interrupted)
- [ ] Cross-session memory works — agent remembers past decisions
- [ ] All 28 tools implemented and dispatching to real service functions
- [ ] Gemini free tier works end-to-end
- [ ] Proactive agent runs via Celery, posts findings, notifies manager
- [ ] ai-service is a thin adapter only — no business logic
- [ ] MCP/A2A stubs in place for future phases

---

_Reference: `docs/02-design/agent-platform-architecture.md`_
