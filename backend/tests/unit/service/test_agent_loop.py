import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.service.agent import loop as loop_mod
from app.service.agent.context import AgentContext
from app.service.agent.planner import PlanResponse, PlanStep


def _make_ctx() -> AgentContext:
    db = AsyncMock()
    db.commit = AsyncMock()
    return AgentContext(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_name="owner",
        conversation_id=uuid.uuid4(),
        db=db,
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )


def _done_sse() -> str:
    return f"data: {json.dumps({'type': 'done', 'usage': {'tokens_in': 0, 'tokens_out': 0, 'model': 'mock'}})}\n\n"


@pytest.mark.asyncio
async def test_run_agent_emits_start_event(monkeypatch: pytest.MonkeyPatch):
    import app.service.agent.executor as executor_mod
    import app.service.agent.history as hist
    import app.service.agent.planner as planner_mod

    monkeypatch.setattr(hist, "set_conversation_status", AsyncMock())
    monkeypatch.setattr(hist, "set_prompt_metadata", AsyncMock())
    monkeypatch.setattr(hist, "load_project_memory", AsyncMock(return_value=None))
    monkeypatch.setattr(hist, "load_messages", AsyncMock(return_value=[]))
    monkeypatch.setattr(hist, "maybe_summarize", AsyncMock())

    empty_plan = PlanResponse(steps=[], needs_execution=False)
    monkeypatch.setattr(planner_mod, "plan", AsyncMock(return_value=empty_plan))

    async def fake_execute(ctx, messages, plan):
        yield _done_sse()

    monkeypatch.setattr(executor_mod, "execute", fake_execute)

    ctx = _make_ctx()
    stream = await loop_mod.run_agent(ctx, "What's the status?")
    events = [e async for e in stream]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert "start" in types
    assert types[0] == "start"


@pytest.mark.asyncio
async def test_run_agent_skips_plan_approval_when_needs_execution_false(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.service.agent.executor as executor_mod
    import app.service.agent.history as hist
    import app.service.agent.planner as planner_mod

    monkeypatch.setattr(hist, "set_conversation_status", AsyncMock())
    monkeypatch.setattr(hist, "set_prompt_metadata", AsyncMock())
    monkeypatch.setattr(hist, "load_project_memory", AsyncMock(return_value=None))
    monkeypatch.setattr(hist, "load_messages", AsyncMock(return_value=[]))
    monkeypatch.setattr(hist, "maybe_summarize", AsyncMock())

    # Plan has steps but needs_execution=False — approval must NOT be awaited
    read_only_plan = PlanResponse(
        steps=[PlanStep(action="Read tasks", reason="Answer the question")],
        needs_execution=False,
    )
    monkeypatch.setattr(planner_mod, "plan", AsyncMock(return_value=read_only_plan))

    async def fake_execute(ctx, messages, plan):
        yield _done_sse()

    monkeypatch.setattr(executor_mod, "execute", fake_execute)

    ctx = _make_ctx()
    stream = await loop_mod.run_agent(ctx, "Which tasks are critical?")
    events = [e async for e in stream]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    # Plan event should NOT have been emitted (no approval gate for read-only)
    assert "plan" not in types
    assert "done" in types


@pytest.mark.asyncio
async def test_run_agent_emits_plan_event_when_needs_execution_true(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.service.agent.executor as executor_mod
    import app.service.agent.history as hist
    import app.service.agent.planner as planner_mod

    monkeypatch.setattr(hist, "set_conversation_status", AsyncMock())
    monkeypatch.setattr(hist, "set_prompt_metadata", AsyncMock())
    monkeypatch.setattr(hist, "load_project_memory", AsyncMock(return_value=None))
    monkeypatch.setattr(hist, "load_messages", AsyncMock(return_value=[]))
    monkeypatch.setattr(hist, "maybe_summarize", AsyncMock())

    action_plan = PlanResponse(
        steps=[PlanStep(action="Create task", reason="User asked")],
        needs_execution=True,
    )
    monkeypatch.setattr(planner_mod, "plan", AsyncMock(return_value=action_plan))

    # Simulate user approving the plan
    async def fake_wait_for_plan_approval(conversation_id: str):
        from app.service.agent.loop import PlanApprovalResult

        return PlanApprovalResult(approved=True, feedback=None)

    monkeypatch.setattr(
        loop_mod, "_wait_for_plan_approval", fake_wait_for_plan_approval
    )

    async def fake_execute(ctx, messages, plan):
        yield _done_sse()

    monkeypatch.setattr(executor_mod, "execute", fake_execute)

    ctx = _make_ctx()
    stream = await loop_mod.run_agent(ctx, "Create a task for me")
    events = [e async for e in stream]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert "plan" in types
    assert "plan_approved" in types
    assert "done" in types


@pytest.mark.asyncio
async def test_resolve_plan_approval_raises_for_unknown_conversation():
    with pytest.raises(NotFoundError):
        await loop_mod.resolve_plan_approval(
            "nonexistent-conversation-id", approved=True, feedback=None
        )


@pytest.mark.asyncio
async def test_run_agent_replans_once_then_stops_if_second_approval_denied(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.service.agent.executor as executor_mod
    import app.service.agent.history as hist
    import app.service.agent.planner as planner_mod
    from app.service.agent.loop import PlanApprovalResult

    monkeypatch.setattr(hist, "set_conversation_status", AsyncMock())
    monkeypatch.setattr(hist, "set_prompt_metadata", AsyncMock())
    monkeypatch.setattr(hist, "load_project_memory", AsyncMock(return_value=None))
    monkeypatch.setattr(hist, "load_messages", AsyncMock(return_value=[]))
    monkeypatch.setattr(hist, "save_user_message", AsyncMock())
    monkeypatch.setattr(hist, "maybe_summarize", AsyncMock())

    first_plan = PlanResponse(
        steps=[PlanStep(action="Initial action", reason="Initial reason")],
        needs_execution=True,
    )
    second_plan = PlanResponse(
        steps=[PlanStep(action="Replanned action", reason="Use feedback")],
        needs_execution=True,
    )
    monkeypatch.setattr(
        planner_mod, "plan", AsyncMock(side_effect=[first_plan, second_plan])
    )

    approvals = iter(
        [
            PlanApprovalResult(approved=False, feedback="Do something else"),
            PlanApprovalResult(approved=False, feedback=None),
        ]
    )

    async def fake_wait_for_plan_approval(conversation_id: str):
        return next(approvals)

    monkeypatch.setattr(
        loop_mod, "_wait_for_plan_approval", fake_wait_for_plan_approval
    )
    execute_mock = AsyncMock()
    monkeypatch.setattr(executor_mod, "execute", execute_mock)

    ctx = _make_ctx()
    stream = await loop_mod.run_agent(ctx, "Create a task")
    events = [e async for e in stream]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert types.count("plan") == 2
    assert "plan_approved" not in types
    assert execute_mock.await_count == 0
