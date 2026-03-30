"""
Conversation history management.

Loads and saves message turns from/to the DB. Builds the messages list
that gets sent to the LLM each turn: [summary?] + [last 20 verbatim].
Also manages AgentProjectMemory (cross-session persistent memory).
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_project_memory import AgentProjectMemory
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.enums import AIMessageRole
from app.service.agent.context import AgentContext

logger = logging.getLogger(__name__)

_MAX_VERBATIM = 20  # keep last N messages in full; older ones are in summary


# ---------------------------------------------------------------------------
# Loading history from DB
# ---------------------------------------------------------------------------


async def load_messages(ctx: AgentContext) -> list[dict]:
    """Load conversation history from DB and return as LLM-compatible message list."""
    result = await ctx.db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == ctx.conversation_id)
        .order_by(AIMessage.created_at.asc())
    )
    rows = list(result.scalars().all())

    messages = [_row_to_message(row) for row in rows]

    if len(messages) <= _MAX_VERBATIM:
        return messages

    # More than 20 messages: use summary + last 20
    result_conv = await ctx.db.execute(
        select(AIConversation).where(AIConversation.id == ctx.conversation_id)
    )
    conversation = result_conv.scalar_one_or_none()
    summary = conversation.summary if conversation else None

    recent = messages[-_MAX_VERBATIM:]
    if summary:
        return [
            {"role": "user", "content": f"[Previous context summary]\n{summary}"}
        ] + recent
    return recent


def _row_to_message(row: AIMessage) -> dict:
    """Convert an AIMessage DB row back to an LLM message dict."""
    if row.role == AIMessageRole.USER:
        if row.tool_results:
            # Tool result turn — content is a list of tool_result blocks
            results = (
                row.tool_results
                if isinstance(row.tool_results, list)
                else [row.tool_results]
            )
            return {"role": "user", "content": results}
        return {"role": "user", "content": row.content or ""}

    if row.role == AIMessageRole.ASSISTANT:
        if row.tool_calls:
            # Assistant turn with tool calls — reconstruct the blocks list
            calls = (
                row.tool_calls if isinstance(row.tool_calls, list) else [row.tool_calls]
            )
            content: list[dict] = []
            if row.content:
                content.append({"type": "text", "text": row.content})
            content.extend(calls)
            return {"role": "assistant", "content": content}
        return {"role": "assistant", "content": row.content or ""}

    return {"role": str(row.role), "content": row.content or ""}


# ---------------------------------------------------------------------------
# Saving turns to DB
# ---------------------------------------------------------------------------


async def save_user_message(
    db: AsyncSession, *, conversation_id: UUID, content: str
) -> None:
    """Persist a new user text message."""
    msg = AIMessage(
        conversation_id=conversation_id,
        role=AIMessageRole.USER,
        content=content,
    )
    db.add(msg)
    await db.flush()


async def save_assistant_turn(
    db: AsyncSession,
    *,
    conversation_id: UUID,
    text: str,
    tool_calls: list[dict] | None,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> None:
    """Persist an assistant turn (text + optional tool_use blocks)."""
    msg = AIMessage(
        conversation_id=conversation_id,
        role=AIMessageRole.ASSISTANT,
        content=text,
        tool_calls=tool_calls or None,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        finish_reason="tool_use" if tool_calls else "stop",
    )
    db.add(msg)
    await db.flush()


async def save_tool_results_turn(
    db: AsyncSession,
    *,
    conversation_id: UUID,
    results: list[dict],
) -> None:
    """Persist a tool-results user turn (list of tool_result blocks)."""
    msg = AIMessage(
        conversation_id=conversation_id,
        role=AIMessageRole.USER,
        content="",
        tool_results=results,
    )
    db.add(msg)
    await db.flush()


# ---------------------------------------------------------------------------
# Rolling summary
# ---------------------------------------------------------------------------


async def maybe_summarize(ctx: AgentContext, messages: list[dict]) -> None:
    """If history exceeds the verbatim window, compress older messages into the summary.

    The summary is stored on AIConversation.summary. Actual LLM-based summarization
    is deferred: for now we just truncate and note that a summary exists.
    Full LLM summarization will be added when Phase 3 gives us a cheaper call path.
    """
    if len(messages) <= _MAX_VERBATIM:
        return

    result = await ctx.db.execute(
        select(AIConversation).where(AIConversation.id == ctx.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return

    # Build a simple text summary from the older messages (non-LLM for now)
    older = messages[:-_MAX_VERBATIM]
    lines = []
    for msg in older:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, list):
            # Extract text blocks
            text = " ".join(
                b.get("text", b.get("content", ""))
                for b in content
                if isinstance(b, dict)
            )
        else:
            text = str(content)
        if text.strip():
            lines.append(f"{role}: {text.strip()[:200]}")

    conversation.summary = "\n".join(lines[-30:])  # keep last 30 compressed lines
    conversation.updated_at = datetime.now(UTC)
    await ctx.db.flush()


# ---------------------------------------------------------------------------
# Project memory (cross-session)
# ---------------------------------------------------------------------------


async def load_project_memory(db: AsyncSession, project_id: UUID) -> str | None:
    """Return the agent's cross-session memory for this project, or None."""
    result = await db.execute(
        select(AgentProjectMemory).where(AgentProjectMemory.project_id == project_id)
    )
    memory = result.scalar_one_or_none()
    return memory.content if memory else None


async def upsert_project_memory(
    db: AsyncSession,
    *,
    project_id: UUID,
    content: str,
    conversation_id: UUID,
) -> None:
    """Create or update the project's agent memory record."""
    result = await db.execute(
        select(AgentProjectMemory).where(AgentProjectMemory.project_id == project_id)
    )
    memory = result.scalar_one_or_none()

    if memory:
        memory.content = content
        memory.updated_by_conversation_id = conversation_id
    else:
        memory = AgentProjectMemory(
            project_id=project_id,
            content=content,
            updated_by_conversation_id=conversation_id,
        )
        db.add(memory)

    await db.flush()


# ---------------------------------------------------------------------------
# Conversation status helper
# ---------------------------------------------------------------------------


async def set_conversation_status(ctx: AgentContext, status: str) -> None:
    result = await ctx.db.execute(
        select(AIConversation).where(AIConversation.id == ctx.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.status = status
        conversation.updated_at = datetime.now(UTC)
        await ctx.db.flush()


async def get_conversation(
    db: AsyncSession, conversation_id: UUID
) -> AIConversation | None:
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Conversation metadata
# ---------------------------------------------------------------------------


async def set_prompt_metadata(ctx: AgentContext, prompt_version: str) -> None:
    result = await ctx.db.execute(
        select(AIConversation).where(AIConversation.id == ctx.conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return

    snapshot = conversation.context_snapshot or {}
    snapshot["agent_prompt_version"] = prompt_version
    snapshot["agent_provider"] = ctx.provider
    snapshot["agent_model"] = ctx.model
    conversation.context_snapshot = snapshot
    conversation.updated_at = datetime.now(UTC)
    await ctx.db.flush()
