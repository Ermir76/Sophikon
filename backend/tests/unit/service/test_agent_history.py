import uuid
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.agent_project_memory import AgentProjectMemory
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.enums import AIMessageRole
from app.service.agent import history as history_mod
from app.service.agent.context import AgentContext


async def _seed_project_and_conversation(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> tuple:
    from sqlalchemy import select

    from app.models.project import Project
    from app.models.user import User

    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass1!", "full_name": "History User"},
    )
    assert resp.status_code == 201

    org = await client.post(
        "/api/v1/organizations", json={"name": f"Org {slug}", "slug": slug}
    )
    assert org.status_code == 201

    proj = await client.post(
        "/api/v1/projects",
        json={
            "name": "History Test Project",
            "organization_id": org.json()["id"],
            "start_date": "2026-01-01",
        },
    )
    assert proj.status_code == 201
    project_id = uuid.UUID(proj.json()["id"])

    user = (await session.execute(select(User).where(User.email == email))).scalar_one()
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one()

    conversation = AIConversation(
        id=uuid7(),
        project_id=project_id,
        user_id=user.id,
        title="Test conversation",
        status="idle",
        mode="chat",
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    ctx = AgentContext(
        project_id=project_id,
        user_id=user.id,
        conversation_id=conversation.id,
        db=session,
        project=project,
        provider="mock",
        model="mock",
        api_key="",
    )
    return ctx, conversation, user, project


@pytest.mark.asyncio
async def test_load_messages_returns_empty_for_new_conversation(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, *_ = await _seed_project_and_conversation(
        client, session, email="history-load@example.com", slug="org-history-load"
    )

    messages = await history_mod.load_messages(ctx)

    assert messages == []


@pytest.mark.asyncio
async def test_save_user_message_persists_to_db(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, conversation, *_ = await _seed_project_and_conversation(
        client,
        session,
        email="history-save-user@example.com",
        slug="org-history-save-user",
    )

    await history_mod.save_user_message(
        session, conversation_id=conversation.id, content="What tasks are overdue?"
    )
    await session.commit()

    rows = list(
        (
            await session.execute(
                select(AIMessage).where(AIMessage.conversation_id == conversation.id)
            )
        ).scalars()
    )
    assert len(rows) == 1
    assert rows[0].role == AIMessageRole.USER
    assert rows[0].content == "What tasks are overdue?"


@pytest.mark.asyncio
async def test_save_assistant_turn_persists_text(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, conversation, *_ = await _seed_project_and_conversation(
        client,
        session,
        email="history-save-asst@example.com",
        slug="org-history-save-asst",
    )

    await history_mod.save_assistant_turn(
        session,
        conversation_id=conversation.id,
        text="Here are the overdue tasks...",
        tool_calls=None,
        model="mock",
    )
    await session.commit()

    rows = list(
        (
            await session.execute(
                select(AIMessage).where(AIMessage.conversation_id == conversation.id)
            )
        ).scalars()
    )
    assert len(rows) == 1
    assert rows[0].role == AIMessageRole.ASSISTANT
    assert rows[0].content == "Here are the overdue tasks..."


@pytest.mark.asyncio
async def test_maybe_summarize_is_noop_below_threshold(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, *_ = await _seed_project_and_conversation(
        client,
        session,
        email="history-summarize@example.com",
        slug="org-history-summarize",
    )
    # Fewer than 20 messages — should not summarize
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(5)]

    # Should not raise and should not modify the conversation summary
    await history_mod.maybe_summarize(ctx, messages)

    conv = (
        await session.execute(
            select(AIConversation).where(AIConversation.id == ctx.conversation_id)
        )
    ).scalar_one()
    assert conv.summary is None


@pytest.mark.asyncio
async def test_load_project_memory_returns_none_when_missing(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, *_ = await _seed_project_and_conversation(
        client, session, email="history-memory-load@example.com", slug="org-memory-load"
    )

    content = await history_mod.load_project_memory(session, ctx.project_id)

    assert content is None


@pytest.mark.asyncio
async def test_upsert_project_memory_creates_and_updates(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, conversation, *_ = await _seed_project_and_conversation(
        client,
        session,
        email="history-memory-upsert@example.com",
        slug="org-memory-upsert",
    )

    await history_mod.upsert_project_memory(
        session,
        project_id=ctx.project_id,
        content="Agent decided to use WBS 1.1 for the design phase.",
        conversation_id=conversation.id,
    )
    await session.commit()

    row = (
        await session.execute(
            select(AgentProjectMemory).where(
                AgentProjectMemory.project_id == ctx.project_id
            )
        )
    ).scalar_one_or_none()
    assert row is not None
    assert row.content == "Agent decided to use WBS 1.1 for the design phase."

    # Update
    await history_mod.upsert_project_memory(
        session,
        project_id=ctx.project_id,
        content="Updated memory content.",
        conversation_id=conversation.id,
    )
    await session.commit()
    await session.refresh(row)
    assert row.content == "Updated memory content."


@pytest.mark.asyncio
async def test_set_conversation_status_transitions(
    client: AsyncClient,
    session: AsyncSession,
):
    ctx, conversation, *_ = await _seed_project_and_conversation(
        client, session, email="history-status@example.com", slug="org-history-status"
    )

    await history_mod.set_conversation_status(ctx, "executing")
    await session.commit()
    await session.refresh(conversation)

    assert conversation.status == "executing"


def test_build_system_prompt_returns_non_empty_string():
    ctx = AgentContext(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        db=MagicMock(),
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )

    prompt = history_mod.build_system_prompt(ctx, project_memory=None)

    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_build_system_prompt_injects_project_memory():
    ctx = AgentContext(
        project_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        db=MagicMock(),
        project=MagicMock(),
        provider="mock",
        model="mock",
        api_key="",
    )

    prompt = history_mod.build_system_prompt(ctx, project_memory="Agent chose WBS 1.1")

    assert "Agent chose WBS 1.1" in prompt
