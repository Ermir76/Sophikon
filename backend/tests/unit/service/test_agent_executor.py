import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.service.agent import executor as executor_mod
from app.service.agent.context import AgentContext
from app.service.agent.planner import PlanResponse, PlanStep
from app.service.agent.policy import PolicyDecision, ToolPolicy
from app.service.agent.tool_registry import ToolResult
from app.service.contracts.ai import AIChatEvent, AIUsageMeta


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


def _done_event() -> AIChatEvent:
    return AIChatEvent(
        type="done",
        usage=AIUsageMeta(tokens_in=10, tokens_out=20, model="mock"),
    )


@pytest.mark.asyncio
async def test_execute_yields_done_when_no_tool_calls(monkeypatch: pytest.MonkeyPatch):
    async def fake_complete(request):
        yield AIChatEvent(type="chunk", content="The project is on track.")
        yield _done_event()

    async def fake_save_assistant_turn(*args, **kwargs):
        pass

    async def fake_load_project_memory(*args, **kwargs):
        return None

    import app.service.agent.history as hist
    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)
    monkeypatch.setattr(hist, "save_assistant_turn", fake_save_assistant_turn)
    monkeypatch.setattr(hist, "load_project_memory", fake_load_project_memory)
    monkeypatch.setattr(hist, "build_system_prompt", lambda *a, **kw: "system")

    ctx = _make_ctx()
    events = [e async for e in await _collect(ctx, [])]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert "done" in types
    assert "chunk" in types


@pytest.mark.asyncio
async def test_execute_emits_tool_call_and_tool_result(monkeypatch: pytest.MonkeyPatch):
    call_count = 0

    async def fake_complete(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield AIChatEvent(
                type="tool_call",
                tool_use_id="tc-001",
                tool_name="get_tasks",
                tool_input={"filter_status": "all"},
            )
            yield _done_event()
        else:
            yield AIChatEvent(type="chunk", content="Here are the tasks.")
            yield _done_event()

    async def fake_execute_tool(tool_name, tool_input, ctx):
        return ToolResult(success=True, data={"tasks": []})

    async def fake_save_assistant_turn(*args, **kwargs):
        pass

    async def fake_save_tool_results_turn(*args, **kwargs):
        pass

    async def fake_load_project_memory(*args, **kwargs):
        return None

    import app.service.agent.history as hist
    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)
    monkeypatch.setattr(executor_mod, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(hist, "save_assistant_turn", fake_save_assistant_turn)
    monkeypatch.setattr(hist, "save_tool_results_turn", fake_save_tool_results_turn)
    monkeypatch.setattr(hist, "load_project_memory", fake_load_project_memory)
    monkeypatch.setattr(hist, "build_system_prompt", lambda *a, **kw: "system")

    ctx = _make_ctx()
    events = [e async for e in await _collect(ctx, [])]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types


@pytest.mark.asyncio
async def test_execute_gates_destructive_tools_with_approval_required(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_complete(request):
        yield AIChatEvent(
            type="tool_call",
            tool_use_id="tc-del",
            tool_name="delete_task",
            tool_input={"task_id": str(uuid.uuid4())},
        )
        yield _done_event()

    async def fake_wait_for_approval(approval_id: str) -> bool:
        return False  # user denies

    async def fake_save_assistant_turn(*args, **kwargs):
        pass

    async def fake_save_tool_results_turn(*args, **kwargs):
        pass

    async def fake_load_project_memory(*args, **kwargs):
        return None

    import app.service.agent.history as hist
    import app.service.ai_service as ai_svc

    monkeypatch.setattr(ai_svc, "complete_from_service", fake_complete)
    monkeypatch.setattr(
        executor_mod,
        "check_tool_policy",
        AsyncMock(return_value=PolicyDecision(policy=ToolPolicy.ALLOW_WITH_APPROVAL)),
    )
    monkeypatch.setattr(executor_mod, "_wait_for_tool_approval", fake_wait_for_approval)
    monkeypatch.setattr(hist, "save_assistant_turn", fake_save_assistant_turn)
    monkeypatch.setattr(hist, "save_tool_results_turn", fake_save_tool_results_turn)
    monkeypatch.setattr(hist, "load_project_memory", fake_load_project_memory)
    monkeypatch.setattr(hist, "build_system_prompt", lambda *a, **kw: "system")

    ctx = _make_ctx()
    events = [e async for e in await _collect(ctx, [])]

    types = [json.loads(e.removeprefix("data: ").strip())["type"] for e in events]
    assert "approval_required" in types


@pytest.mark.asyncio
async def test_resolve_tool_approval_raises_for_unknown_id():
    with pytest.raises(NotFoundError):
        await executor_mod.resolve_tool_approval("nonexistent-id", approved=True)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _collect(ctx: AgentContext, messages: list):
    plan = PlanResponse(
        steps=[PlanStep(action="Do it", reason="It needs doing")], needs_execution=True
    )
    return executor_mod.execute(ctx, messages, plan)
