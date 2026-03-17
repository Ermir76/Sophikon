"""
SSE event builders for the agent streaming protocol.

Each function constructs an AIChatEvent, serializes it, and returns a
formatted SSE string: "data: {...}\n\n"
"""

import json
from uuid import UUID

from app.service.contracts.ai import AIChatEvent, AIUsageMeta


def _fmt(event: AIChatEvent) -> str:
    payload = event.model_dump(mode="json", exclude_none=True)
    return f"data: {json.dumps(payload)}\n\n"


def event_start(conversation_id: UUID, model: str) -> str:
    return _fmt(AIChatEvent(type="start", conversation_id=conversation_id, model=model))


def event_plan(steps: list[dict]) -> str:
    return _fmt(AIChatEvent(type="plan", steps=steps))


def event_plan_approved() -> str:
    return _fmt(AIChatEvent(type="plan_approved"))


def event_reasoning(content: str) -> str:
    return _fmt(AIChatEvent(type="reasoning", content=content))


def event_tool_call(tool_use_id: str, tool_name: str, tool_input: dict) -> str:
    return _fmt(
        AIChatEvent(
            type="tool_call",
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )
    )


# TODO: Phase 4 — spec (agent-platform-plan.md §4.1) defines tool_result as
# { success: boolean, data: unknown } but current frontend types.ts uses
# { content: string }. Update both this function and frontend types.ts together.
def event_tool_result(
    tool_use_id: str, tool_name: str, *, success: bool, data: object
) -> str:
    content = (
        json.dumps(data, default=str)
        if success
        else json.dumps({"error": str(data) if data else "Tool failed"})
    )
    return _fmt(
        AIChatEvent(
            type="tool_result",
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            content=content,
        )
    )


def event_approval_required(
    approval_id: str, tool_use_id: str, tool_name: str, tool_input: dict
) -> str:
    return _fmt(
        AIChatEvent(
            type="approval_required",
            approval_id=approval_id,
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )
    )


def event_chunk(content: str) -> str:
    return _fmt(AIChatEvent(type="chunk", content=content))


# TODO: Phase 4 — spec defines ui_action as { action, payload } but AIChatEvent
# uses tool_input field for the payload. Update AIChatEvent to add a payload field
# and align frontend types.ts at the same time.
def event_ui_action(action: str, payload: dict) -> str:
    return _fmt(AIChatEvent(type="ui_action", action=action, tool_input=payload))


def event_done(conversation_id: UUID, usage: dict) -> str:
    return _fmt(
        AIChatEvent(
            type="done",
            conversation_id=conversation_id,
            usage=AIUsageMeta(
                tokens_in=usage.get("tokens_in", 0),
                tokens_out=usage.get("tokens_out", 0),
                model=usage.get("model"),
            ),
        )
    )


# TODO: Phase 4 — spec defines error as { message: string } but AIChatEvent uses
# the error field. Update both AIChatEvent and frontend types.ts together.
def event_error(message: str) -> str:
    return _fmt(AIChatEvent(type="error", error=message))
