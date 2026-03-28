import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.agent.context import AgentContext
from app.service.agent.policy import ToolPolicy, check_tool_policy


def _make_ctx(role_name: str) -> AgentContext:
    return AgentContext(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_name=role_name,
        conversation_id=uuid.uuid4(),
        db=AsyncMock(),
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )


@pytest.mark.asyncio
async def test_check_tool_policy_viewer_blocked_from_write_tool():
    ctx = _make_ctx("viewer")

    decision = await check_tool_policy("create_task", {}, ctx)

    assert decision.policy == ToolPolicy.DENY
    assert decision.reason is not None
    assert "viewers cannot execute write tools" in decision.reason


@pytest.mark.asyncio
async def test_check_tool_policy_member_allowed_write_tool():
    ctx = _make_ctx("member")

    decision = await check_tool_policy("create_task", {}, ctx)

    assert decision.policy == ToolPolicy.ALLOW


@pytest.mark.asyncio
async def test_check_tool_policy_denies_unknown_tool():
    ctx = _make_ctx("owner")

    decision = await check_tool_policy("not_a_real_tool", {}, ctx)

    assert decision.policy == ToolPolicy.DENY
    assert decision.reason is not None
    assert "unknown tool" in decision.reason


@pytest.mark.asyncio
async def test_check_tool_policy_denies_scope_violation(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.service.agent.policy as policy_mod

    ctx = _make_ctx("member")
    task_id = str(uuid.uuid4())
    monkeypatch.setattr(
        policy_mod.task_service,
        "get_task_by_id",
        AsyncMock(return_value=None),
    )

    decision = await check_tool_policy(
        "update_task",
        {"task_id": task_id, "notes": "Out of scope"},
        ctx,
    )

    assert decision.policy == ToolPolicy.DENY
    assert decision.reason is not None
    assert "Scope violation" in decision.reason


@pytest.mark.asyncio
async def test_check_tool_policy_destructive_requires_approval_for_manager():
    ctx = _make_ctx("manager")

    decision = await check_tool_policy("delete_task", {}, ctx)

    assert decision.policy == ToolPolicy.ALLOW_WITH_APPROVAL
