"""
Planner — Phase 1 of the agent run.

Makes a single LLM call with only the define_plan tool. The LLM must call
it, giving us a structured plan before anything is executed. The user then
approves or redirects.

If the request is purely informational (needs_execution=False), the loop
skips plan approval and goes straight to execution.
"""

import logging
from dataclasses import dataclass, field

from app.service.agent.context import AgentContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plan types
# ---------------------------------------------------------------------------


@dataclass
class PlanStep:
    action: str
    reason: str


@dataclass
class PlanResponse:
    steps: list[PlanStep] = field(default_factory=list)
    needs_execution: bool = False


# ---------------------------------------------------------------------------
# define_plan tool schema
# ---------------------------------------------------------------------------


_DEFINE_PLAN_TOOL: dict = {
    "name": "define_plan",
    "description": (
        "Define the step-by-step plan for the requested operation. "
        "Call this tool once to present your plan before taking any action."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "What you will do in this step.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why this step is needed.",
                        },
                    },
                    "required": ["action", "reason"],
                },
            },
            "needs_execution": {
                "type": "boolean",
                "description": (
                    "True if the request requires creating, modifying, or deleting data. "
                    "False for read-only questions or analysis."
                ),
            },
        },
        "required": ["steps", "needs_execution"],
    },
}

_PLANNER_SYSTEM = (
    "You are a professional Project Manager AI assistant. "
    "Your ONLY task right now is to produce a concise, numbered plan for the user's request. "
    "Do NOT execute anything. Do NOT call any other tools. "
    "Call define_plan exactly once with your proposed steps and whether execution is needed."
)


# ---------------------------------------------------------------------------
# plan()
# ---------------------------------------------------------------------------


async def plan(ctx: AgentContext, messages: list[dict]) -> PlanResponse:
    """Call the LLM once with only the define_plan tool to produce a structured plan."""
    plan_input: dict | None = None
    async for event in _stream_plan(ctx, messages):
        if event.get("type") == "tool_call" and event.get("tool_name") == "define_plan":
            plan_input = event.get("tool_input") or {}
            break

    if plan_input is None:
        logger.warning("Planner did not call define_plan — returning empty plan")
        return PlanResponse(steps=[], needs_execution=False)

    steps = [
        PlanStep(action=s.get("action", ""), reason=s.get("reason", ""))
        for s in plan_input.get("steps", [])
    ]
    return PlanResponse(
        steps=steps, needs_execution=bool(plan_input.get("needs_execution", False))
    )


async def _stream_plan(ctx: AgentContext, messages: list[dict]):
    """Call /v1/complete with only the define_plan tool and the planner system prompt."""
    from app.service.ai_service import complete_from_service
    from app.service.contracts.ai import AICompleteRequest

    request = AICompleteRequest(
        messages=messages,
        tools=[_DEFINE_PLAN_TOOL],
        system_prompt=_PLANNER_SYSTEM,
        provider=ctx.provider,
        model=ctx.model,
        api_key=ctx.api_key or None,
        conversation_id=ctx.conversation_id,
    )

    async for event in complete_from_service(request):
        yield event.model_dump(mode="json", exclude_none=True)
