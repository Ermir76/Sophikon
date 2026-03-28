from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.service import (
    assignment_service,
    dependency_service,
    resource_service,
    task_service,
)
from app.service.agent.context import AgentContext
from app.service.agent.tool_registry import DESTRUCTIVE_TOOLS, TOOL_SCHEMAS, UI_TOOLS


class ToolPolicy(StrEnum):
    ALLOW = "allow"
    ALLOW_WITH_APPROVAL = "allow_with_approval"
    DENY = "deny"


@dataclass
class PolicyDecision:
    policy: ToolPolicy
    reason: str | None = None


_ALLOWED_TOOLS = frozenset(
    schema.get("name") for schema in TOOL_SCHEMAS if isinstance(schema.get("name"), str)
)
_WRITE_TOOLS = frozenset(
    name
    for name in _ALLOWED_TOOLS
    if name not in DESTRUCTIVE_TOOLS
    and name not in UI_TOOLS
    and not name.startswith("get_")
    and not name.startswith("search_")
)


def _role_decision(role_name: str, tool_name: str) -> PolicyDecision:
    if role_name == "viewer":
        if tool_name in DESTRUCTIVE_TOOLS or tool_name in _WRITE_TOOLS:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Permission denied: viewers cannot execute write tools.",
            )
        return PolicyDecision(policy=ToolPolicy.ALLOW)

    if role_name == "member":
        if tool_name in DESTRUCTIVE_TOOLS:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Permission denied: members cannot execute destructive tools.",
            )
        return PolicyDecision(policy=ToolPolicy.ALLOW)

    if role_name in {"manager", "owner"}:
        if tool_name in DESTRUCTIVE_TOOLS:
            return PolicyDecision(policy=ToolPolicy.ALLOW_WITH_APPROVAL)
        return PolicyDecision(policy=ToolPolicy.ALLOW)

    return PolicyDecision(
        policy=ToolPolicy.DENY,
        reason=f"Permission denied: unsupported role '{role_name}'.",
    )


def _to_uuid(value: object) -> UUID | None:
    if not isinstance(value, str):
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


async def _verify_scope(
    tool_name: str, tool_input: dict, ctx: AgentContext
) -> PolicyDecision:
    db = ctx.db
    project_id = ctx.project_id

    task_id_keys = {
        "task_id",
        "parent_task_id",
        "before_task_id",
        "after_task_id",
        "new_parent_id",
        "predecessor_id",
        "successor_id",
    }
    for key in task_id_keys:
        raw = tool_input.get(key)
        if raw in (None, ""):
            continue
        task_id = _to_uuid(raw)
        if task_id is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason=f"Invalid {key}: must be a UUID string.",
            )
        task = await task_service.get_task_by_id(db, task_id, project_id)
        if task is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason=f"Scope violation: {key} does not belong to this project.",
            )

    if tool_name == "bulk_create_tasks":
        tasks = tool_input.get("tasks")
        if isinstance(tasks, list):
            for idx, item in enumerate(tasks):
                if not isinstance(item, dict):
                    continue
                raw_parent_id = item.get("parent_task_id")
                if raw_parent_id in (None, ""):
                    continue
                parent_id = _to_uuid(raw_parent_id)
                if parent_id is None:
                    return PolicyDecision(
                        policy=ToolPolicy.DENY,
                        reason=f"Invalid tasks[{idx}].parent_task_id: must be a UUID string.",
                    )
                parent_task = await task_service.get_task_by_id(
                    db, parent_id, project_id
                )
                if parent_task is None:
                    return PolicyDecision(
                        policy=ToolPolicy.DENY,
                        reason=(
                            f"Scope violation: tasks[{idx}].parent_task_id does not belong "
                            "to this project."
                        ),
                    )

    raw_dependency_id = tool_input.get("dependency_id")
    if raw_dependency_id not in (None, ""):
        dependency_id = _to_uuid(raw_dependency_id)
        if dependency_id is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Invalid dependency_id: must be a UUID string.",
            )
        dependency = await dependency_service.get_dependency_by_id(
            db, dependency_id, project_id
        )
        if dependency is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Scope violation: dependency_id does not belong to this project.",
            )

    raw_resource_id = tool_input.get("resource_id")
    if raw_resource_id not in (None, ""):
        resource_id = _to_uuid(raw_resource_id)
        if resource_id is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Invalid resource_id: must be a UUID string.",
            )
        resource = await resource_service.get_resource_by_id(
            db, resource_id, project_id
        )
        if resource is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Scope violation: resource_id does not belong to this project.",
            )

    raw_assignment_id = tool_input.get("assignment_id")
    if raw_assignment_id not in (None, ""):
        assignment_id = _to_uuid(raw_assignment_id)
        if assignment_id is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Invalid assignment_id: must be a UUID string.",
            )
        assignment = await assignment_service.get_assignment_by_id(db, assignment_id)
        if assignment is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Scope violation: assignment_id does not exist.",
            )
        assignment_task = await task_service.get_task_by_id(
            db, assignment.task_id, project_id
        )
        if assignment_task is None:
            return PolicyDecision(
                policy=ToolPolicy.DENY,
                reason="Scope violation: assignment_id does not belong to this project.",
            )

    return PolicyDecision(policy=ToolPolicy.ALLOW)


async def check_tool_policy(
    tool_name: str,
    tool_input: dict,
    ctx: AgentContext,
) -> PolicyDecision:
    if tool_name not in _ALLOWED_TOOLS:
        return PolicyDecision(
            policy=ToolPolicy.DENY,
            reason=f"Permission denied: unknown tool '{tool_name}'.",
        )

    decision = _role_decision(ctx.role_name, tool_name)
    if decision.policy == ToolPolicy.DENY:
        return decision

    if tool_name in UI_TOOLS or (
        tool_name not in _WRITE_TOOLS and tool_name not in DESTRUCTIVE_TOOLS
    ):
        return decision

    scope_decision = await _verify_scope(tool_name, tool_input, ctx)
    if scope_decision.policy == ToolPolicy.DENY:
        return scope_decision

    return decision
