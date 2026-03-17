import uuid
from unittest.mock import MagicMock

from app.service.agent.context import AgentContext


def _make_context(**overrides) -> AgentContext:
    defaults = dict(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        db=MagicMock(),
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )
    return AgentContext(**{**defaults, **overrides})


def test_agent_context_stores_all_fields():
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    db = MagicMock()
    project = MagicMock()

    ctx = AgentContext(
        project_id=project_id,
        user_id=user_id,
        conversation_id=conversation_id,
        db=db,
        project=project,
        provider="anthropic",
        model="claude-3-7-sonnet-latest",
        api_key="sk-test",
    )

    assert ctx.project_id == project_id
    assert ctx.user_id == user_id
    assert ctx.conversation_id == conversation_id
    assert ctx.db is db
    assert ctx.project is project
    assert ctx.provider == "anthropic"
    assert ctx.model == "claude-3-7-sonnet-latest"
    assert ctx.api_key == "sk-test"


def test_each_agent_run_gets_its_own_context():
    ctx_a = _make_context(provider="anthropic")
    ctx_b = _make_context(provider="gemini")

    assert ctx_a is not ctx_b
    assert ctx_a.provider != ctx_b.provider
    assert ctx_a.project_id != ctx_b.project_id
