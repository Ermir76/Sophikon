"""
Shared tool catalog entrypoints for planner and executor.
"""

from copy import deepcopy

from app.service.agent.tool_registry import TOOL_SCHEMAS

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


def get_planner_tools() -> list[dict]:
    return [deepcopy(_DEFINE_PLAN_TOOL)]


def get_execution_tools() -> list[dict]:
    return deepcopy(TOOL_SCHEMAS)
