import json
import uuid

from app.service.agent.streaming import (
    event_approval_required,
    event_chunk,
    event_done,
    event_error,
    event_plan,
    event_plan_approved,
    event_reasoning,
    event_start,
    event_tool_call,
    event_tool_result,
    event_ui_action,
)


def _parse(sse: str) -> dict:
    assert sse.startswith("data: "), f"SSE must start with 'data: ', got: {sse!r}"
    assert sse.endswith("\n\n"), f"SSE must end with '\\n\\n', got: {sse!r}"
    return json.loads(sse.removeprefix("data: ").strip())


def test_event_start():
    cid = uuid.uuid4()
    payload = _parse(event_start(cid, "claude-3-7-sonnet-latest"))
    assert payload["type"] == "start"
    assert payload["conversation_id"] == str(cid)
    assert payload["model"] == "claude-3-7-sonnet-latest"


def test_event_plan_contains_steps():
    steps = [{"action": "Get tasks", "reason": "Need to know current state"}]
    payload = _parse(event_plan(steps))
    assert payload["type"] == "plan"
    assert payload["steps"] == steps


def test_event_plan_approved():
    payload = _parse(event_plan_approved())
    assert payload["type"] == "plan_approved"


def test_event_reasoning():
    payload = _parse(event_reasoning("I should first check the schedule..."))
    assert payload["type"] == "reasoning"
    assert payload["content"] == "I should first check the schedule..."


def test_event_tool_call():
    payload = _parse(event_tool_call("abc-123", "get_tasks", {"filter_status": "all"}))
    assert payload["type"] == "tool_call"
    assert payload["tool_use_id"] == "abc-123"
    assert payload["tool_name"] == "get_tasks"
    assert payload["tool_input"] == {"filter_status": "all"}


def test_event_tool_result_success_serializes_data():
    payload = _parse(
        event_tool_result("abc-123", "get_tasks", success=True, data={"tasks": []})
    )
    assert payload["type"] == "tool_result"
    assert payload["tool_use_id"] == "abc-123"
    assert payload["tool_name"] == "get_tasks"
    content = json.loads(payload["content"])
    assert content == {"tasks": []}


def test_event_tool_result_failure_serializes_error():
    payload = _parse(
        event_tool_result(
            "abc-123", "delete_task", success=False, data="Task not found"
        )
    )
    assert payload["type"] == "tool_result"
    content = json.loads(payload["content"])
    assert "error" in content


def test_event_approval_required():
    payload = _parse(
        event_approval_required("appr-1", "tid-1", "delete_task", {"task_id": "x"})
    )
    assert payload["type"] == "approval_required"
    assert payload["approval_id"] == "appr-1"
    assert payload["tool_use_id"] == "tid-1"
    assert payload["tool_name"] == "delete_task"
    assert payload["tool_input"] == {"task_id": "x"}


def test_event_chunk():
    payload = _parse(event_chunk("Hello, here is"))
    assert payload["type"] == "chunk"
    assert payload["content"] == "Hello, here is"


def test_event_ui_action_uses_tool_input_field():
    payload = _parse(event_ui_action("navigate", {"view": "gantt"}))
    assert payload["type"] == "ui_action"
    assert payload["action"] == "navigate"
    assert payload["tool_input"] == {"view": "gantt"}


def test_event_done():
    cid = uuid.uuid4()
    payload = _parse(
        event_done(cid, {"tokens_in": 100, "tokens_out": 200, "model": "mock"})
    )
    assert payload["type"] == "done"
    assert payload["conversation_id"] == str(cid)
    assert payload["usage"]["tokens_in"] == 100
    assert payload["usage"]["tokens_out"] == 200


def test_event_error_uses_error_field():
    payload = _parse(event_error("Something went wrong"))
    assert payload["type"] == "error"
    assert payload["error"] == "Something went wrong"


def test_all_events_produce_valid_json():
    cid = uuid.uuid4()
    events = [
        event_start(cid, "mock"),
        event_plan([{"action": "a", "reason": "r"}]),
        event_plan_approved(),
        event_reasoning("thinking..."),
        event_tool_call("id", "get_tasks", {}),
        event_tool_result("id", "get_tasks", success=True, data={}),
        event_approval_required("aid", "tid", "delete_task", {}),
        event_chunk("text"),
        event_ui_action("navigate", {}),
        event_done(cid, {"tokens_in": 0, "tokens_out": 0, "model": "mock"}),
        event_error("err"),
    ]
    for evt in events:
        parsed = _parse(evt)
        assert "type" in parsed
