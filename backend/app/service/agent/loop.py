"""
Agent loop — orchestrates plan + execute + memory update.

This is the single entry point that ai_service.prepare_chat_stream() calls.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.service.agent import executor, planner
from app.service.agent import history as history_mod
from app.service.agent.context import AgentContext
from app.service.agent.streaming import (
    event_plan,
    event_plan_approved,
    event_start,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Proactive analysis
# ---------------------------------------------------------------------------


@dataclass
class ProactiveFindings:
    has_issues: bool
    summary: str


async def run_proactive_analysis(ctx: AgentContext) -> ProactiveFindings:
    """Collect project health data via read tools and summarise with one LLM call.

    Returns ProactiveFindings(has_issues=False) if the project looks healthy.
    Called from the Celery proactive agent — no streaming, no plan approval.
    """
    from app.service.agent.tool_registry import execute_tool
    from app.service.ai_service import _complete_from_service
    from app.service.contracts.ai import AICompleteRequest

    summary_result = await execute_tool("get_project_summary", {}, ctx)
    overdue_result = await execute_tool("get_tasks", {"filter_status": "overdue"}, ctx)
    critical_path_result = await execute_tool("get_critical_path", {}, ctx)

    data_context = (
        f"Project summary:\n{summary_result.to_content()}\n\n"
        f"Overdue tasks:\n{overdue_result.to_content()}\n\n"
        f"Critical path:\n{critical_path_result.to_content()}"
    )

    project_memory = await history_mod.load_project_memory(ctx.db, ctx.project_id)
    system_prompt = (
        f"You are a proactive project health monitor for '{ctx.project.name}'. "
        "Analyze the project data provided and identify actionable issues "
        "(overdue tasks, critical path delays, serious risks). "
        "If issues are found, start your response with 'ISSUES FOUND:' and list them concisely in markdown. "
        "If the project is on track with no significant issues, respond only with 'NO ISSUES'."
    )
    if project_memory:
        system_prompt += f"\n\nProject memory:\n{project_memory}"

    request = AICompleteRequest(
        messages=[{"role": "user", "content": data_context}],
        tools=[],
        system_prompt=system_prompt,
        provider=ctx.provider,
        model=ctx.model,
        api_key=ctx.api_key or None,
    )

    text_chunks: list[str] = []
    async for event in _complete_from_service(request):
        if event.type == "chunk" and event.content:
            text_chunks.append(event.content)

    response_text = "".join(text_chunks).strip()
    has_issues = bool(response_text) and not response_text.upper().startswith(
        "NO ISSUES"
    )
    summary = response_text[:500] if has_issues else ""
    return ProactiveFindings(has_issues=has_issues, summary=summary)


# ---------------------------------------------------------------------------
# Plan approval store — in-memory, single server (fine for portfolio/demo)
# ---------------------------------------------------------------------------


@dataclass
class PlanApprovalResult:
    approved: bool
    feedback: str | None = None


_PLAN_APPROVAL_STORE: dict[str, asyncio.Future] = {}


async def resolve_plan_approval(
    conversation_id: str, *, approved: bool, feedback: str | None
) -> None:
    """Called by the plan-approval endpoint to unblock the waiting loop."""
    future = _PLAN_APPROVAL_STORE.get(conversation_id)
    if future is None or future.done():
        from app.core.exceptions import NotFoundError

        raise NotFoundError("No pending plan approval for this conversation")
    future.set_result(PlanApprovalResult(approved=approved, feedback=feedback))


async def _wait_for_plan_approval(conversation_id: str) -> PlanApprovalResult:
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()
    _PLAN_APPROVAL_STORE[conversation_id] = future
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=600.0)
    except TimeoutError:
        return PlanApprovalResult(approved=False, feedback=None)
    finally:
        _PLAN_APPROVAL_STORE.pop(conversation_id, None)


# ---------------------------------------------------------------------------
# run_agent()
# ---------------------------------------------------------------------------


async def run_agent(
    ctx: AgentContext,
    user_message: str,
) -> AsyncGenerator[str]:
    """Full agent run: start → plan → execute → memory → done.

    Yields SSE event strings for the streaming response.
    """

    async def _stream():
        yield event_start(ctx.conversation_id, ctx.model)

        await history_mod.set_conversation_status(ctx, "executing")
        await ctx.db.commit()

        # Load history + inject project memory into system context
        project_memory = await history_mod.load_project_memory(ctx.db, ctx.project_id)
        history = await history_mod.load_messages(ctx)

        # --- Phase 1: Plan ---

        current_plan = await planner.plan(ctx, history)

        if current_plan.needs_execution and current_plan.steps:
            # Emit plan and wait for user approval
            yield event_plan(
                [{"action": s.action, "reason": s.reason} for s in current_plan.steps]
            )
            await history_mod.set_conversation_status(ctx, "awaiting_plan_approval")
            await ctx.db.commit()

            approval = await _wait_for_plan_approval(str(ctx.conversation_id))

            if not approval.approved:
                if approval.feedback:
                    # User redirected — re-plan with their feedback
                    history.append({"role": "user", "content": approval.feedback})
                    await history_mod.save_user_message(
                        ctx.db,
                        conversation_id=ctx.conversation_id,
                        content=approval.feedback,
                    )
                    await ctx.db.commit()
                    current_plan = await planner.plan(ctx, history)
                    if current_plan.steps:
                        yield event_plan(
                            [
                                {"action": s.action, "reason": s.reason}
                                for s in current_plan.steps
                            ]
                        )
                    # Wait for second approval (one redirect allowed)
                    await history_mod.set_conversation_status(
                        ctx, "awaiting_plan_approval"
                    )
                    await ctx.db.commit()
                    approval = await _wait_for_plan_approval(str(ctx.conversation_id))
                    if not approval.approved:
                        await history_mod.set_conversation_status(ctx, "idle")
                        await ctx.db.commit()
                        return
                else:
                    await history_mod.set_conversation_status(ctx, "idle")
                    await ctx.db.commit()
                    return

            yield event_plan_approved()
            await history_mod.set_conversation_status(ctx, "executing")
            await ctx.db.commit()

        # --- Phase 2: Execute ---
        async for sse_event in executor.execute(ctx, history, current_plan):
            yield sse_event

        # --- Post-run: update memory + status ---
        await history_mod.set_conversation_status(ctx, "idle")

        # Reload updated history for summary check
        updated_history = await history_mod.load_messages(ctx)
        await history_mod.maybe_summarize(ctx, updated_history)

        # Update project memory if there is something worth noting
        if project_memory is not None or len(updated_history) > 4:
            await _maybe_update_project_memory(ctx, updated_history, project_memory)

        await ctx.db.commit()

    return _stream()


async def _maybe_update_project_memory(
    ctx: AgentContext,
    messages: list[dict],
    existing_memory: str | None,
) -> None:
    """Extract key decisions from this session and upsert project memory.

    For now, we keep existing memory and append a brief session note.
    Full LLM-based memory curation will be added in Phase 3 when we have
    cheaper/faster completion calls.
    """
    if not messages:
        return

    # Build a brief note from the last assistant message
    last_assistant = next(
        (m for m in reversed(messages) if m.get("role") == "assistant"), None
    )
    if not last_assistant:
        return

    content = last_assistant.get("content", "")
    if isinstance(content, list):
        text = " ".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    else:
        text = str(content)

    if not text.strip():
        return

    session_note = text.strip()[:300]
    new_memory = (
        f"{existing_memory}\n\n[Session {ctx.conversation_id}]\n{session_note}"
        if existing_memory
        else f"[Session {ctx.conversation_id}]\n{session_note}"
    )
    # Trim to ~2000 chars to stay within the ~600 token budget
    new_memory = new_memory[-2000:]

    await history_mod.upsert_project_memory(
        ctx.db,
        project_id=ctx.project_id,
        content=new_memory,
        conversation_id=ctx.conversation_id,
    )
