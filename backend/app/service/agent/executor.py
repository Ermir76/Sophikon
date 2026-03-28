"""
Executor — Phase 2 of the agent run: the real agentic while loop.

Calls ai-service /v1/complete for one turn, streams events, executes tools,
feeds results back, and repeats until the LLM stops issuing tool calls.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from uuid import uuid4

from app.service.agent import history as history_mod
from app.service.agent.context import AgentContext
from app.service.agent.planner import PlanResponse
from app.service.agent.policy import ToolPolicy, check_tool_policy
from app.service.agent.streaming import (
    event_approval_required,
    event_chunk,
    event_done,
    event_error,
    event_tool_call,
    event_tool_result,
    event_ui_action,
)
from app.service.agent.tool_registry import (
    DESTRUCTIVE_TOOLS,
    TOOL_SCHEMAS,
    execute_tool,
)
from app.service.contracts.ai import AIChatEvent, AICompleteRequest, AIUsageMeta

logger = logging.getLogger(__name__)

_MAX_ITERATIONS = 12  # safety ceiling — prevents infinite loops

# ---------------------------------------------------------------------------
# Per-run approval store (same pattern as loop._PLAN_APPROVAL_STORE)
# ---------------------------------------------------------------------------


_APPROVAL_STORE: dict[str, asyncio.Future] = {}


async def resolve_tool_approval(approval_id: str, approved: bool) -> None:
    """Called by the approval endpoint to unblock a waiting tool call."""
    future = _APPROVAL_STORE.get(approval_id)
    if future is None or future.done():
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Approval not found or already resolved")
    future.set_result(approved)


async def _wait_for_tool_approval(approval_id: str) -> bool:
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()
    _APPROVAL_STORE[approval_id] = future
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=300.0)
    except TimeoutError:
        return False
    finally:
        _APPROVAL_STORE.pop(approval_id, None)


# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------


async def execute(
    ctx: AgentContext,
    messages: list[dict],
    plan: PlanResponse | None,
) -> AsyncGenerator[str]:
    """Run the agentic tool loop.

    Yields SSE event strings. Persists each turn to DB as it goes.
    """
    from app.service.ai_service import complete_from_service

    current_messages = list(messages)

    # If we have an approved plan, append it as context so the LLM knows what was agreed
    if plan and plan.steps:
        plan_text = "\n".join(
            f"{i + 1}. {s.action} — {s.reason}" for i, s in enumerate(plan.steps)
        )
        current_messages.append(
            {
                "role": "user",
                "content": (
                    f"[Plan approved by user]\n{plan_text}\n\n"
                    "Now execute this plan step by step."
                ),
            }
        )

    total_usage = AIUsageMeta()

    try:
        project_memory = await history_mod.load_project_memory(ctx.db, ctx.project_id)
        system_prompt = history_mod.build_system_prompt(ctx, project_memory)

        for iteration in range(_MAX_ITERATIONS):
            request = AICompleteRequest(
                messages=current_messages,
                tools=TOOL_SCHEMAS,
                system_prompt=system_prompt,
                provider=ctx.provider,
                model=ctx.model,
                api_key=ctx.api_key or None,
                conversation_id=ctx.conversation_id,
            )

            tool_call_events: list[AIChatEvent] = []
            text_chunks: list[str] = []

            async for event in complete_from_service(request):
                if event.type == "start" and iteration == 0:
                    pass  # start was already emitted by loop.py

                elif event.type == "chunk" and event.content:
                    text_chunks.append(event.content)
                    yield event_chunk(event.content)

                elif event.type == "tool_call":
                    tool_call_events.append(event)
                    yield event_tool_call(
                        event.tool_use_id or "",
                        event.tool_name or "",
                        event.tool_input or {},
                    )

                elif event.type == "done":
                    if event.usage:
                        total_usage.tokens_in += event.usage.tokens_in
                        total_usage.tokens_out += event.usage.tokens_out
                        total_usage.model = event.usage.model

                elif event.type == "error":
                    yield event_error(event.error or "AI service error")
                    return

            if not tool_call_events:
                # LLM produced only text — we're done
                if text_chunks:
                    await history_mod.save_assistant_turn(
                        ctx.db,
                        conversation_id=ctx.conversation_id,
                        text="".join(text_chunks),
                        tool_calls=None,
                        model=total_usage.model,
                        tokens_in=total_usage.tokens_in or None,
                        tokens_out=total_usage.tokens_out or None,
                    )
                    await ctx.db.commit()
                break

            # Build assistant turn content (text + tool_use blocks)
            assistant_content: list[dict] = []
            if text_chunks:
                assistant_content.append({"type": "text", "text": "".join(text_chunks)})
            for tc in tool_call_events:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tc.tool_use_id,
                        "name": tc.tool_name,
                        "input": tc.tool_input or {},
                    }
                )

            # Execute tools and collect result blocks
            tool_result_blocks: list[dict] = []
            for tc in tool_call_events:
                tool_name = tc.tool_name or ""
                tool_input = tc.tool_input or {}
                tool_use_id = tc.tool_use_id or ""

                policy_decision = await check_tool_policy(tool_name, tool_input, ctx)
                if policy_decision.policy == ToolPolicy.DENY:
                    denied_reason = (
                        policy_decision.reason
                        or "Permission denied for this tool call."
                    )
                    result_block = {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": denied_reason,
                        "is_error": True,
                    }
                    yield event_tool_result(
                        tool_use_id,
                        tool_name,
                        success=False,
                        data={"error": denied_reason, "denied": True},
                    )
                    tool_result_blocks.append(result_block)
                    continue

                needs_approval = (
                    policy_decision.policy == ToolPolicy.ALLOW_WITH_APPROVAL
                    or tool_name in DESTRUCTIVE_TOOLS
                )
                if needs_approval:
                    approval_id = str(uuid4())
                    yield event_approval_required(
                        approval_id, tool_use_id, tool_name, tool_input
                    )
                    approved = await _wait_for_tool_approval(approval_id)
                    if not approved:
                        result_block = {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": "User denied this action.",
                            "is_error": True,
                        }
                        yield event_tool_result(
                            tool_use_id, tool_name, success=False, data={"denied": True}
                        )
                        tool_result_blocks.append(result_block)
                        continue

                result = await execute_tool(tool_name, tool_input, ctx)

                if result.is_ui_action:
                    yield event_ui_action(tool_name, result.data or {})

                yield event_tool_result(
                    tool_use_id, tool_name, success=result.success, data=result.data
                )

                tool_result_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": result.to_content(),
                        **({"is_error": True} if not result.success else {}),
                    }
                )

            # Persist assistant turn + tool results to DB
            tool_use_blocks = [
                b for b in assistant_content if b.get("type") == "tool_use"
            ]
            await history_mod.save_assistant_turn(
                ctx.db,
                conversation_id=ctx.conversation_id,
                text="".join(text_chunks),
                tool_calls=tool_use_blocks if tool_use_blocks else None,
                model=total_usage.model,
            )
            await history_mod.save_tool_results_turn(
                ctx.db,
                conversation_id=ctx.conversation_id,
                results=tool_result_blocks,
            )
            await ctx.db.commit()

            # Append to in-memory messages for next iteration
            current_messages.append({"role": "assistant", "content": assistant_content})
            current_messages.append({"role": "user", "content": tool_result_blocks})

        yield event_done(
            ctx.conversation_id,
            {
                "tokens_in": total_usage.tokens_in,
                "tokens_out": total_usage.tokens_out,
                "model": total_usage.model,
            },
        )

    except Exception:
        logger.exception("Executor failed for conversation %s", ctx.conversation_id)
        yield event_error("Agent execution failed unexpectedly")
