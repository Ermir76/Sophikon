import uuid
from unittest.mock import MagicMock

import pytest

from app.service.agent import planner as planner_mod
from app.service.agent.context import AgentContext
from app.service.contracts.ai import AIChatEvent, AIUsageMeta


def _make_ctx() -> AgentContext:
    return AgentContext(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_name="owner",
        conversation_id=uuid.uuid4(),
        db=MagicMock(),
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )


def _tool_call_event(steps: list[dict], needs_execution: bool) -> AIChatEvent:
    return AIChatEvent(
        type="tool_call",
        tool_use_id="plan-001",
        tool_name="define_plan",
        tool_input={"steps": steps, "needs_execution": needs_execution},
    )


@pytest.mark.asyncio
async def test_plan_returns_steps_when_llm_calls_define_plan(
    monkeypatch: pytest.MonkeyPatch,
):
    steps = [
        {"action": "Get overdue tasks", "reason": "Need to assess current state"},
        {"action": "Update priorities", "reason": "Resolve blocking items"},
    ]

    async def fake_complete(request):
        yield _tool_call_event(steps, needs_execution=True)
        yield AIChatEvent(
            type="done", usage=MagicMock(tokens_in=10, tokens_out=20, model="mock")
        )

    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)

    ctx = _make_ctx()
    result = await planner_mod.plan(
        ctx, [{"role": "user", "content": "Fix overdue tasks"}]
    )

    assert result.needs_execution is True
    assert len(result.steps) == 2
    assert result.steps[0].action == "Get overdue tasks"
    assert result.steps[1].action == "Update priorities"


@pytest.mark.asyncio
async def test_plan_returns_empty_when_llm_does_not_call_define_plan(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_complete(request):
        yield AIChatEvent(type="chunk", content="Sure, the project is on track.")
        yield AIChatEvent(
            type="done", usage=AIUsageMeta(tokens_in=5, tokens_out=15, model="mock")
        )

    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)

    ctx = _make_ctx()
    result = await planner_mod.plan(
        ctx, [{"role": "user", "content": "How are we doing?"}]
    )

    assert result.needs_execution is False
    assert result.steps == []


@pytest.mark.asyncio
async def test_plan_read_only_request_sets_needs_execution_false(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_complete(request):
        yield _tool_call_event(
            [{"action": "Read tasks", "reason": "Answer the question"}],
            needs_execution=False,
        )
        yield AIChatEvent(
            type="done", usage=MagicMock(tokens_in=5, tokens_out=10, model="mock")
        )

    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)

    ctx = _make_ctx()
    result = await planner_mod.plan(
        ctx, [{"role": "user", "content": "Which tasks are critical?"}]
    )

    assert result.needs_execution is False
    assert len(result.steps) == 1
