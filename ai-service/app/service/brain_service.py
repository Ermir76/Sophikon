"""Brain service — routes to Claude API (live) or deterministic mock (fallback).

Live mode:  AI_MODE=live + ANTHROPIC_API_KEY set in environment.
Mock mode:  all other cases — rule-based, no external calls, safe for testing.
"""

import asyncio
import json
import logging
from datetime import date
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import (
    AIUsageMeta,
    ChatEvent,
    ChatRequest,
    EstimateItem,
    EstimateRequest,
    EstimateResponse,
    SuggestionAction,
    SuggestionItem,
    SuggestionsRequest,
    SuggestionsResponse,
)
from app.service.model_catalog import validate_provider_and_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool definitions — passed to Claude as its action space
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    # --- Read tools (always autonomous) ---
    {
        "name": "get_tasks",
        "description": (
            "Get all tasks for the project. Returns tasks with WBS codes, dates, "
            "progress percentage, priority, and hierarchy. Use this to understand "
            "the project state before answering questions or taking actions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "enum": ["all", "overdue", "in_progress", "completed", "not_started"],
                    "description": "Filter tasks by status. Omit for all tasks.",
                },
            },
        },
    },
    {
        "name": "get_task",
        "description": "Get detailed information about a single task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "search_tasks",
        "description": "Search tasks by name or filter by condition.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search in task name and notes.",
                },
                "overdue_only": {"type": "boolean"},
                "in_progress_only": {"type": "boolean"},
            },
        },
    },
    {
        "name": "get_dependencies",
        "description": "Get all task dependencies in the project (predecessor → successor relationships).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_critical_path",
        "description": (
            "Get the critical path — the sequence of tasks that determines the "
            "minimum project duration. Delays to critical path tasks delay the whole project."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_project_summary",
        "description": (
            "Get a high-level project health summary: completion %, overdue count, "
            "in-progress count, upcoming milestones, and schedule status."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_members",
        "description": "Get all project members with their roles (owner, manager, member, viewer).",
        "input_schema": {"type": "object", "properties": {}},
    },
    # --- Write tools (configurable, default autonomous) ---
    {
        "name": "create_task",
        "description": "Create a new task in the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 500},
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "duration": {
                    "type": "integer",
                    "description": "Duration in minutes. 480 = 1 working day, 960 = 2 days.",
                    "minimum": 60,
                },
                "parent_task_id": {
                    "type": "string",
                    "description": "Parent task UUID for creating a subtask. Omit for root task.",
                },
                "notes": {"type": "string", "description": "Task description or notes."},
            },
            "required": ["name", "start_date", "duration"],
        },
    },
    {
        "name": "update_task",
        "description": "Update fields on an existing task (name, dates, progress, notes, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to update"},
                "name": {"type": "string"},
                "percent_complete": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Progress percentage.",
                },
                "start_date": {"type": "string", "format": "date"},
                "duration": {
                    "type": "integer",
                    "description": "Duration in minutes.",
                    "minimum": 60,
                },
                "notes": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "bulk_create_tasks",
        "description": (
            "Create multiple tasks at once. Use this when generating a project plan "
            "or when the user asks to create many tasks — don't create them one by one."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "maxItems": 50,
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "start_date": {"type": "string", "format": "date"},
                            "duration": {"type": "integer", "minimum": 60},
                            "notes": {"type": "string"},
                        },
                        "required": ["name", "start_date", "duration"],
                    },
                },
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "add_dependency",
        "description": "Add a dependency: predecessor must finish before successor can start.",
        "input_schema": {
            "type": "object",
            "properties": {
                "predecessor_id": {
                    "type": "string",
                    "description": "UUID of the task that must finish first.",
                },
                "successor_id": {
                    "type": "string",
                    "description": "UUID of the task that starts after.",
                },
                "type": {
                    "type": "string",
                    "enum": ["FS", "FF", "SS", "SF"],
                    "description": "Dependency type. FS (Finish-to-Start) is most common.",
                },
            },
            "required": ["predecessor_id", "successor_id", "type"],
        },
    },
    {
        "name": "indent_task",
        "description": "Make a task a child of its previous sibling (indent in WBS hierarchy).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to indent"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "outdent_task",
        "description": "Move a task one level up in the WBS hierarchy (outdent/promote).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to outdent"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "reorder_task",
        "description": "Change a task's position in the list, optionally under a different parent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "after_task_id": {
                    "type": "string",
                    "description": "Place task after this task. Null = move to beginning of group.",
                },
                "before_task_id": {
                    "type": "string",
                    "description": "Place task before this task. Null = move to end of group.",
                },
                "new_parent_id": {
                    "type": "string",
                    "description": "Move under this parent task. Null = keep current parent.",
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "calculate_schedule",
        "description": (
            "Run the scheduling engine: recalculates all task dates based on "
            "dependencies, constraints, and critical path. Call this after making "
            "structural changes to keep dates accurate."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    # --- Destructive tools (always require user approval) ---
    {
        "name": "delete_task",
        "description": (
            "Delete a task (soft delete — recoverable). "
            "IMPORTANT: This always requires user approval. "
            "Always include a clear reason so the user can make an informed decision."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to delete"},
                "reason": {
                    "type": "string",
                    "description": "Why this task should be deleted. Shown to user for approval.",
                },
            },
            "required": ["task_id", "reason"],
        },
    },
    {
        "name": "delete_dependency",
        "description": (
            "Remove a dependency between tasks. "
            "IMPORTANT: This always requires user approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dependency_id": {"type": "string", "description": "Dependency UUID to remove"},
                "reason": {"type": "string", "description": "Why this dependency should be removed."},
            },
            "required": ["dependency_id", "reason"],
        },
    },
    # --- UI action tools (configurable, default autonomous) ---
    {
        "name": "navigate",
        "description": "Navigate the user to a different view in the application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "view": {
                    "type": "string",
                    "enum": ["overview", "tasks", "gantt", "calendar", "resources", "reports"],
                },
            },
            "required": ["view"],
        },
    },
    {
        "name": "highlight_tasks",
        "description": "Highlight specific tasks in the current view to draw the user's attention.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of task UUIDs to highlight.",
                },
            },
            "required": ["task_ids"],
        },
    },
    {
        "name": "open_task",
        "description": "Open a task's detail panel so the user can view or edit it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to open"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "filter_view",
        "description": "Apply a filter to the current task list or Gantt view.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["all", "overdue", "in_progress", "completed", "critical_path"],
                },
            },
            "required": ["filter"],
        },
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_runtime_provider_and_model(
    request: ChatRequest,
) -> tuple[str | None, str, str | None]:
    provider, model, error = validate_provider_and_model(request.provider, request.model)
    if settings.AI_MODE != "live":
        return None, model, None
    return provider, model, error


def _estimate_tokens(value: str) -> int:
    return max(1, len(value) // 4)


def _build_system_prompt(request: ChatRequest) -> str:
    ctx = request.project_context
    today = date.today()
    total = len(ctx.tasks)
    overdue = sum(
        1 for t in ctx.tasks if t.percent_complete < 100 and t.finish_date < today
    )
    in_progress = sum(1 for t in ctx.tasks if 0 < t.percent_complete < 100)
    completed = sum(1 for t in ctx.tasks if t.percent_complete >= 100)

    return (
        f'You are Sophikon AI — a project management assistant for "{ctx.name}".\n'
        f"Today: {today}\n"
        f"Project status: {ctx.status} | "
        f"{total} tasks | {completed} completed | {in_progress} in progress | {overdue} overdue\n\n"
        "You have tools to read and act on project data:\n"
        "- Read tools (get_tasks, get_dependencies, etc.): use freely, no approval needed.\n"
        "- Write tools (create_task, update_task, etc.): execute directly unless user restricted them.\n"
        "- Delete tools: ALWAYS require user approval — describe clearly what will be deleted.\n"
        "- UI tools (navigate, highlight_tasks, etc.): execute directly to guide the user.\n\n"
        "Be concise and action-oriented. Show your reasoning. Confirm actions you take.\n"
        "When creating multiple tasks at once, use bulk_create_tasks — not one-by-one.\n"
        "After structural changes (create, delete, reorder), call calculate_schedule to keep dates accurate."
    )


def _build_messages(request: ChatRequest) -> list[dict]:
    messages: list[dict] = []

    for item in request.history:
        messages.append({"role": item.role, "content": item.content})

    if request.tool_results:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tr.tool_use_id,
                    "content": tr.content,
                    **({"is_error": True} if tr.is_error else {}),
                }
                for tr in request.tool_results
            ],
        })
    elif request.message:
        messages.append({"role": "user", "content": request.message})

    return messages


def _stringify_content(value: str | list[dict]) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _build_openai_messages(request: ChatRequest) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for item in request.history:
        role = item.role if item.role in {"user", "assistant", "system"} else "user"
        messages.append({"role": role, "content": _stringify_content(item.content)})

    if request.tool_results:
        tool_results_payload = [
            {
                "tool_use_id": tr.tool_use_id,
                "content": tr.content,
                **({"is_error": True} if tr.is_error else {}),
            }
            for tr in request.tool_results
        ]
        messages.append(
            {
                "role": "user",
                "content": f"Tool results: {json.dumps(tool_results_payload, ensure_ascii=False)}",
            }
        )
    elif request.message:
        messages.append({"role": "user", "content": request.message})

    return messages


def _build_gemini_contents(request: ChatRequest) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for item in request.history:
        role = "model" if item.role == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": _stringify_content(item.content)}]})

    if request.tool_results:
        tool_results_payload = [
            {
                "tool_use_id": tr.tool_use_id,
                "content": tr.content,
                **({"is_error": True} if tr.is_error else {}),
            }
            for tr in request.tool_results
        ]
        contents.append(
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Tool results: {json.dumps(tool_results_payload, ensure_ascii=False)}"
                    }
                ],
            }
        )
    elif request.message:
        contents.append({"role": "user", "parts": [{"text": request.message}]})

    return contents


def _as_openai_tools() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for tool in TOOL_DEFINITIONS:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
        )
    return tools


def _as_gemini_tools() -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for tool in TOOL_DEFINITIONS:
        declarations.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            }
        )
    return [{"functionDeclarations": declarations}]


# ---------------------------------------------------------------------------
# Live mode — real Claude API
# ---------------------------------------------------------------------------


async def _stream_claude(request: ChatRequest, *, model_id: str):
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = _build_messages(request)
    system = _build_system_prompt(request)

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    current_tool_id: str | None = None
    current_tool_name: str | None = None
    tool_input_json = ""
    final_message = None

    try:
        async with client.messages.stream(
            model=model_id,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        ) as stream:
            async for event in stream:
                event_type = getattr(event, "type", None)

                if event_type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        tool_input_json = ""

                elif event_type == "content_block_delta":
                    delta = event.delta
                    if getattr(delta, "type", None) == "text_delta":
                        yield ChatEvent(
                            type="chunk", content=delta.text
                        ).model_dump(mode="json", exclude_none=True)
                    elif getattr(delta, "type", None) == "input_json_delta":
                        tool_input_json += delta.partial_json

                elif event_type == "content_block_stop":
                    if current_tool_id is not None:
                        try:
                            tool_input = json.loads(tool_input_json) if tool_input_json else {}
                        except json.JSONDecodeError:
                            tool_input = {}

                        yield ChatEvent(
                            type="tool_call",
                            tool_use_id=current_tool_id,
                            tool_name=current_tool_name,
                            tool_input=tool_input,
                        ).model_dump(mode="json", exclude_none=True)

                        current_tool_id = None
                        current_tool_name = None
                        tool_input_json = ""

            final_message = await stream.get_final_message()

    except Exception:
        logger.exception("Claude streaming failed")
        yield ChatEvent(
            type="error", error="Claude API call failed"
        ).model_dump(mode="json", exclude_none=True)
        return

    usage = AIUsageMeta(
        tokens_in=final_message.usage.input_tokens if final_message else 0,
        tokens_out=final_message.usage.output_tokens if final_message else 0,
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)


async def _stream_openai(request: ChatRequest, *, model_id: str):
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    messages = _build_openai_messages(request)
    system = _build_system_prompt(request)
    tools = _as_openai_tools()

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system},
                *messages,
            ],
            tools=tools,
            tool_choice="auto",
        )
    except Exception:
        logger.exception("OpenAI chat request failed")
        yield ChatEvent(
            type="error", error="OpenAI API call failed"
        ).model_dump(mode="json", exclude_none=True)
        return

    choice = response.choices[0] if response.choices else None
    message = choice.message if choice else None

    if message and message.content:
        yield ChatEvent(type="chunk", content=message.content).model_dump(
            mode="json", exclude_none=True
        )

    if message and message.tool_calls:
        for call in message.tool_calls:
            raw_args = call.function.arguments or "{}"
            try:
                parsed_input = json.loads(raw_args)
            except json.JSONDecodeError:
                parsed_input = {}
            yield ChatEvent(
                type="tool_call",
                tool_use_id=call.id,
                tool_name=call.function.name,
                tool_input=parsed_input,
            ).model_dump(mode="json", exclude_none=True)

    usage = AIUsageMeta(
        tokens_in=response.usage.prompt_tokens if response.usage else 0,
        tokens_out=response.usage.completion_tokens if response.usage else 0,
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)


async def _stream_gemini(request: ChatRequest, *, model_id: str):
    import httpx

    system = _build_system_prompt(request)
    contents = _build_gemini_contents(request)
    tools = _as_gemini_tools()

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "tools": tools,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                params={"key": settings.GEMINI_API_KEY},
                json=payload,
            )
    except Exception:
        logger.exception("Gemini chat request failed")
        yield ChatEvent(
            type="error", error="Gemini API call failed"
        ).model_dump(mode="json", exclude_none=True)
        return

    if response.status_code >= 400:
        logger.error("Gemini API error status=%s body=%s", response.status_code, response.text)
        yield ChatEvent(
            type="error", error="Gemini API call failed"
        ).model_dump(mode="json", exclude_none=True)
        return

    try:
        data = response.json()
    except ValueError:
        yield ChatEvent(
            type="error", error="Malformed Gemini response"
        ).model_dump(mode="json", exclude_none=True)
        return

    candidate = (data.get("candidates") or [{}])[0]
    parts = ((candidate.get("content") or {}).get("parts")) or []

    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            yield ChatEvent(type="chunk", content=part["text"]).model_dump(
                mode="json", exclude_none=True
            )
        function_call = part.get("functionCall") if isinstance(part, dict) else None
        if function_call:
            yield ChatEvent(
                type="tool_call",
                tool_use_id=str(uuid4()),
                tool_name=function_call.get("name"),
                tool_input=function_call.get("args") or {},
            ).model_dump(mode="json", exclude_none=True)

    usage_meta = data.get("usageMetadata") or {}
    usage = AIUsageMeta(
        tokens_in=int(usage_meta.get("promptTokenCount", 0) or 0),
        tokens_out=int(usage_meta.get("candidatesTokenCount", 0) or 0),
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)


# ---------------------------------------------------------------------------
# Mock mode — deterministic, no external calls
# ---------------------------------------------------------------------------


_KEYWORD_DAY_HINTS: dict[str, float] = {
    "design": 2.0,
    "analysis": 2.0,
    "plan": 1.5,
    "develop": 4.0,
    "implementation": 4.0,
    "integrat": 5.0,
    "api": 3.0,
    "test": 2.5,
    "qa": 2.5,
    "deploy": 2.0,
    "migration": 3.0,
    "security": 3.0,
}


def _chunk_text(value: str, chunk_size: int = 48) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


def _compose_mock_answer(request: ChatRequest) -> str:
    tasks = request.project_context.tasks
    today = date.today()
    overdue = sum(1 for t in tasks if t.percent_complete < 100 and t.finish_date < today)
    in_progress = sum(1 for t in tasks if 0 < t.percent_complete < 100)
    completed = sum(1 for t in tasks if t.percent_complete >= 100)
    total = len(tasks)
    name = request.project_context.name
    question = (request.message or "").lower()

    if "overdue" in question:
        return (
            f"{name} has {overdue} overdue tasks out of {total}. "
            "Prioritize tasks with past finish dates and low completion."
        )
    if "progress" in question or "status" in question:
        return (
            f"{name}: {completed} completed, {in_progress} in progress, {overdue} overdue "
            f"out of {total} total tasks."
        )
    if "suggest" in question or "next" in question:
        return (
            f"Recommended: resolve {overdue} overdue tasks first, then focus on "
            f"{in_progress} active tasks to improve schedule confidence."
        )
    return (
        f"I reviewed {name}: {completed}/{total} tasks complete, "
        f"{in_progress} in progress, {overdue} overdue. "
        "Ask about overdue tasks, progress, or schedule suggestions."
    )


async def _stream_mock(request: ChatRequest, *, model_id: str):
    answer = _compose_mock_answer(request)
    usage = AIUsageMeta(
        tokens_in=_estimate_tokens(request.message or ""),
        tokens_out=_estimate_tokens(answer),
        model=model_id,
    )

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    for chunk in _chunk_text(answer):
        await asyncio.sleep(0)
        yield ChatEvent(type="chunk", content=chunk).model_dump(
            mode="json", exclude_none=True
        )

    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


async def stream_chat_events(request: ChatRequest):
    provider, model_id, error = _resolve_runtime_provider_and_model(request)
    if error:
        yield ChatEvent(type="error", error=error, model=model_id).model_dump(
            mode="json", exclude_none=True
        )
        return

    if provider == "anthropic":
        async for event in _stream_claude(request, model_id=model_id):
            yield event
    elif provider == "openai":
        async for event in _stream_openai(request, model_id=model_id):
            yield event
    elif provider == "gemini":
        async for event in _stream_gemini(request, model_id=model_id):
            yield event
    else:
        async for event in _stream_mock(request, model_id=model_id):
            yield event


def _base_minutes_from_task_name(task_name: str, original_duration: int | None) -> int:
    if original_duration and original_duration > 0:
        return max(240, original_duration)
    lower_name = task_name.lower()
    matched_days = [days for key, days in _KEYWORD_DAY_HINTS.items() if key in lower_name]
    if matched_days:
        return int(max(matched_days) * 480)
    return 2 * 480


def build_estimates(request: EstimateRequest) -> EstimateResponse:
    estimates: list[EstimateItem] = []

    for task in request.task_inputs:
        likely_minutes = _base_minutes_from_task_name(task.task_name, task.duration)
        optimistic_minutes = max(120, int(likely_minutes * 0.7))
        pessimistic_minutes = max(optimistic_minutes + 60, int(likely_minutes * 1.6))
        confidence = 0.78 if task.duration else 0.64
        reasoning = (
            f"Estimated from task context and comparable PM work patterns for '{task.task_name}'."
            if request.include_reasoning
            else None
        )

        estimates.append(
            EstimateItem(
                task_id=task.task_id,
                task_name=task.task_name,
                optimistic_minutes=optimistic_minutes,
                likely_minutes=likely_minutes,
                pessimistic_minutes=pessimistic_minutes,
                recommended_minutes=likely_minutes,
                confidence=confidence,
                reasoning=reasoning,
            )
        )

    usage = AIUsageMeta(
        tokens_in=_estimate_tokens(
            request.project_context.name
            + " ".join(task.task_name for task in request.task_inputs)
        ),
        tokens_out=_estimate_tokens(str(len(estimates))),
        model=settings.AI_MODEL_NAME,
    )
    return EstimateResponse(estimates=estimates, usage=usage)


def build_suggestions(request: SuggestionsRequest) -> SuggestionsResponse:
    suggestions: list[SuggestionItem] = []
    today = date.today()

    for task in request.project_context.tasks:
        if len(suggestions) >= request.limit:
            break
        if task.percent_complete < 100 and task.finish_date < today:
            suggestions.append(
                SuggestionItem(
                    id=f"s-{uuid4()}",
                    type="OVERDUE_TASK",
                    severity="HIGH",
                    title="Task is overdue",
                    description=f"'{task.name}' is past finish date and still incomplete.",
                    affected_task_id=task.id,
                    suggested_action=SuggestionAction(
                        type="SET_PRIORITY",
                        payload={"task_id": str(task.id), "priority": 850},
                    ),
                )
            )

    lower_names = [task.name.lower() for task in request.project_context.tasks]
    has_qa = any("qa" in name or "test" in name for name in lower_names)
    has_deploy = any("deploy" in name or "release" in name for name in lower_names)
    if len(suggestions) < request.limit and has_qa and has_deploy:
        qa_task = next(
            (t for t in request.project_context.tasks if "qa" in t.name.lower() or "test" in t.name.lower()),
            None,
        )
        deploy_task = next(
            (t for t in request.project_context.tasks if "deploy" in t.name.lower() or "release" in t.name.lower()),
            None,
        )
        if qa_task and deploy_task:
            suggestions.append(
                SuggestionItem(
                    id=f"s-{uuid4()}",
                    type="MISSING_DEPENDENCY",
                    severity="MEDIUM",
                    title="Possible missing dependency",
                    description=(
                        f"'{deploy_task.name}' likely depends on '{qa_task.name}'. "
                        "Add dependency to enforce sequence."
                    ),
                    affected_task_id=deploy_task.id,
                    suggested_action=SuggestionAction(
                        type="ADD_DEPENDENCY",
                        payload={
                            "predecessor_id": str(qa_task.id),
                            "successor_id": str(deploy_task.id),
                            "dependency_type": "FS",
                        },
                    ),
                )
            )

    if not suggestions:
        suggestions.append(
            SuggestionItem(
                id=f"s-{uuid4()}",
                type="NO_CRITICAL_ISSUE",
                severity="LOW",
                title="No high-risk issues detected",
                description="Current schedule looks stable based on available task signals.",
                suggested_action=SuggestionAction(type="NONE", payload={}),
            )
        )

    usage = AIUsageMeta(
        tokens_in=_estimate_tokens(
            request.project_context.name + str(len(request.project_context.tasks))
        ),
        tokens_out=_estimate_tokens(str(len(suggestions))),
        model=settings.AI_MODEL_NAME,
    )
    return SuggestionsResponse(suggestions=suggestions[: request.limit], usage=usage)
