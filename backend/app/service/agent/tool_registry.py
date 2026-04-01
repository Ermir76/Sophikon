"""
Tool registry — schemas (what the LLM sees) and dispatch (what runs when called).

The backend owns all tool execution. Tools call existing service functions
through the standard service → repository → DB chain.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from app.core.exceptions import AppException, InvalidOperationError
from app.models.assignment import Assignment
from app.models.enums import (
    CommentEntityType,
    ConstraintType,
    DependencyType,
    LagFormat,
    NotificationType,
    RateTable,
    TaskStatus,
    TaskType,
    WorkContour,
)
from app.models.resource import Resource
from app.service import (
    activity_log_service,
    assignment_service,
    calendar_service,
    comment_service,
    dependency_service,
    insights_service,
    notification_service,
    project_member_service,
    resource_service,
    scheduling_service,
    task_bulk_service,
    task_hierarchy_service,
    task_service,
    utilization_service,
)
from app.service.agent.context import AgentContext
from app.service.contracts.assignment import AssignmentCreateInput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool classification
# ---------------------------------------------------------------------------

DESTRUCTIVE_TOOLS: frozenset[str] = frozenset({"delete_task", "delete_dependency"})
UI_TOOLS: frozenset[str] = frozenset(
    {"navigate", "highlight_tasks", "open_task", "filter_view"}
)

# ---------------------------------------------------------------------------
# Tool result
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    success: bool
    data: dict | list | str | int | float | bool | None = field(default=None)
    error: str | None = field(default=None)
    is_ui_action: bool = field(default=False)

    def to_content(self) -> str:
        if self.success:
            return json.dumps(self.data, default=str)
        return json.dumps({"error": self.error or "Tool failed"})


# ---------------------------------------------------------------------------
# Tool schemas — what the LLM sees
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_tasks",
        "description": (
            "Get tasks for the project. Pass parent_task_id to get only direct "
            "children of a summary task — use this to drill into subtasks "
            "efficiently instead of loading the full project. Returns WBS codes, "
            "dates, progress, priority, and hierarchy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "enum": [
                        "all",
                        "overdue",
                        "in_progress",
                        "completed",
                        "not_started",
                    ],
                    "description": "Filter tasks by status. Omit for all tasks.",
                },
                "parent_task_id": {
                    "type": "string",
                    "description": (
                        "If provided, return only direct children of this task. "
                        "Use to drill into a summary task's subtasks."
                    ),
                },
            },
        },
    },
    {
        "name": "get_task",
        "description": "Get detailed information about a single task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string", "description": "Task UUID"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "search_tasks",
        "description": (
            "Search tasks by text in task name/notes. Supports status filtering, "
            "overdue-only filter, and optional parent inclusion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search in task name and notes.",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "BACKLOG",
                        "TODO",
                        "IN_PROGRESS",
                        "IN_REVIEW",
                        "DONE",
                    ],
                },
                "overdue_only": {"type": "boolean"},
                "include_parents": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 250},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_dependencies",
        "description": "Get all task dependencies (predecessor → successor relationships).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_critical_path",
        "description": (
            "Get the critical path — the sequence of tasks that determines the "
            "minimum project duration. Delays to critical-path tasks delay the whole project."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_project_summary",
        "description": (
            "Get a high-level project health summary: completion %, overdue count, "
            "in-progress count, upcoming milestones, and schedule status."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_members",
        "description": "Get all project members with their roles (owner, manager, member, viewer).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_resources",
        "description": (
            "Get all resources (people, materials, costs) for the project. "
            "Returns type, availability (max_units), standard rate, and active status. "
            "Use before assigning resources to tasks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "include_inactive": {
                    "type": "boolean",
                    "description": "Include inactive resources. Defaults to false.",
                }
            },
        },
    },
    {
        "name": "get_utilization",
        "description": (
            "Get resource utilization for the project — how much each resource is "
            "allocated, whether anyone is over-allocated. "
            "Defaults to the project's date range if no window is specified."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start of utilization window (YYYY-MM-DD). Defaults to project start.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End of utilization window (YYYY-MM-DD). Defaults to project finish or today+90d.",
                },
            },
        },
    },
    {
        "name": "get_assignments",
        "description": (
            "Get resource assignments. Filter by task_id or resource_id. "
            "If no filter is given, returns all assignments for all tasks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Filter assignments for this task UUID.",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Filter assignments for this resource UUID.",
                },
            },
        },
    },
    {
        "name": "get_activity_log",
        "description": (
            "Get the project activity log — recent changes made by team members. "
            "Shows who created, updated, or deleted tasks, resources, assignments, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": [
                        "task",
                        "resource",
                        "assignment",
                        "dependency",
                        "comment",
                        "project",
                    ],
                    "description": "Filter by entity type. Omit for all.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Number of entries to return. Defaults to 50.",
                },
            },
        },
    },
    {
        "name": "get_comments",
        "description": (
            "Get comments on the project or on a specific task. "
            "Defaults to project-level comments if no task_id is given."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Get comments for this task UUID. Omit for project-level comments.",
                }
            },
        },
    },
    {
        "name": "get_calendar",
        "description": (
            "Get the project's working calendars — defines working days and hours. "
            "The scheduler uses these to calculate task durations."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_insights",
        "description": (
            "Get a comprehensive project health dashboard: task status counts, "
            "schedule health, cost metrics, critical path, upcoming milestones, "
            "overdue tasks, and resource over-allocation. "
            "Call this at the start of any health assessment or planning session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "window": {
                    "type": "string",
                    "enum": ["7d", "30d", "90d"],
                    "description": "Time window for trend analysis. Defaults to 30d.",
                }
            },
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task in the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 500},
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "duration": {
                    "type": "integer",
                    "description": "Duration in minutes. 480 = 1 working day, 960 = 2 days.",
                    "minimum": 60,
                },
                "parent_task_id": {
                    "type": "string",
                    "description": "Parent task UUID for creating a subtask. Omit for root task.",
                },
                "notes": {
                    "type": "string",
                    "description": "Task description or notes.",
                },
            },
            "required": ["name", "start_date", "duration"],
        },
    },
    {
        "name": "update_task",
        "description": "Update fields on an existing task (name, dates, progress, notes, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to update"},
                "name": {"type": "string"},
                "percent_complete": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Progress percentage.",
                },
                "start_date": {"type": "string", "format": "date"},
                "duration": {
                    "type": "integer",
                    "description": "Duration in minutes.",
                    "minimum": 60,
                },
                "notes": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "bulk_create_tasks",
        "description": (
            "Create multiple tasks at once. Use this when generating a project plan "
            "or when the user asks to create many tasks — do not create them one by one."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "maxItems": 50,
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "start_date": {"type": "string", "format": "date"},
                            "duration": {"type": "integer", "minimum": 60},
                            "notes": {"type": "string"},
                        },
                        "required": ["name", "start_date", "duration"],
                    },
                },
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "add_dependency",
        "description": "Add a dependency: predecessor must finish before successor can start.",
        "input_schema": {
            "type": "object",
            "properties": {
                "predecessor_id": {
                    "type": "string",
                    "description": "UUID of the task that must finish first.",
                },
                "successor_id": {
                    "type": "string",
                    "description": "UUID of the task that starts after.",
                },
                "type": {
                    "type": "string",
                    "enum": ["FS", "FF", "SS", "SF"],
                    "description": "Dependency type. FS (Finish-to-Start) is most common.",
                },
            },
            "required": ["predecessor_id", "successor_id", "type"],
        },
    },
    {
        "name": "indent_task",
        "description": "Make a task a child of its previous sibling (indent in WBS hierarchy).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to indent"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "outdent_task",
        "description": "Move a task one level up in the WBS hierarchy (outdent/promote).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to outdent"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "reorder_task",
        "description": "Change a task's position in the list, optionally under a different parent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "after_task_id": {
                    "type": "string",
                    "description": "Place task after this task. Omit to move to beginning.",
                },
                "before_task_id": {
                    "type": "string",
                    "description": "Place task before this task. Omit to move to end.",
                },
                "new_parent_id": {
                    "type": "string",
                    "description": "Move under this parent task. Omit to keep current parent.",
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "calculate_schedule",
        "description": (
            "Run the scheduling engine: recalculates all task dates based on "
            "dependencies, constraints, and critical path. Call this after making "
            "structural changes to keep dates accurate."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "assign_resource",
        "description": (
            "Assign a resource to a task. Use get_resources for resource IDs, "
            "get_tasks for task IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID."},
                "resource_id": {"type": "string", "description": "Resource UUID."},
                "units": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 10.0,
                    "description": "Allocation units. 1.0 = 100% capacity. Defaults to 1.0.",
                },
            },
            "required": ["task_id", "resource_id"],
        },
    },
    {
        "name": "unassign_resource",
        "description": "Remove a resource assignment from a task. Get assignment IDs from get_assignments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "string",
                    "description": "Assignment UUID to remove.",
                }
            },
            "required": ["assignment_id"],
        },
    },
    {
        "name": "post_comment",
        "description": (
            "Post a comment on the project or on a specific task. "
            "Use to leave notes, document decisions, or communicate findings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Comment text."},
                "task_id": {
                    "type": "string",
                    "description": "Post on this task. Omit to post on the project.",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "send_notification",
        "description": (
            "Send a notification to a project member. "
            "Use get_members to find the member's user_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "UUID of the member to notify.",
                },
                "title": {
                    "type": "string",
                    "maxLength": 255,
                    "description": "Notification title.",
                },
                "message": {"type": "string", "description": "Notification body."},
            },
            "required": ["user_id", "title", "message"],
        },
    },
    {
        "name": "delete_task",
        "description": (
            "Delete a task (soft delete — recoverable). "
            "IMPORTANT: This always requires user approval. "
            "Always include a clear reason so the user can make an informed decision."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to delete"},
                "reason": {
                    "type": "string",
                    "description": "Why this task should be deleted. Shown to user for approval.",
                },
            },
            "required": ["task_id", "reason"],
        },
    },
    {
        "name": "delete_dependency",
        "description": (
            "Remove a dependency between tasks. "
            "IMPORTANT: This always requires user approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dependency_id": {
                    "type": "string",
                    "description": "Dependency UUID to remove",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this dependency should be removed.",
                },
            },
            "required": ["dependency_id", "reason"],
        },
    },
    {
        "name": "navigate",
        "description": "Navigate the user to a different view in the application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "view": {
                    "type": "string",
                    "enum": [
                        "overview",
                        "tasks",
                        "gantt",
                        "calendar",
                        "resources",
                        "reports",
                    ],
                }
            },
            "required": ["view"],
        },
    },
    {
        "name": "highlight_tasks",
        "description": "Highlight specific tasks in the current view to draw the user's attention.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of task UUIDs to highlight.",
                }
            },
            "required": ["task_ids"],
        },
    },
    {
        "name": "open_task",
        "description": "Open a task's detail panel so the user can view or edit it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task UUID to open"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "filter_view",
        "description": "Apply a filter to the current task list or Gantt view.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": [
                        "all",
                        "overdue",
                        "in_progress",
                        "completed",
                        "critical_path",
                    ],
                }
            },
            "required": ["filter"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatch — calls real service functions
# ---------------------------------------------------------------------------


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    ctx: AgentContext,
) -> ToolResult:
    try:
        data = await _dispatch(tool_name, tool_input, ctx)
        is_ui = tool_name in UI_TOOLS
        return ToolResult(success=True, data=data, is_ui_action=is_ui)
    except AppException as exc:
        return ToolResult(success=False, error=exc.message)
    except Exception:
        logger.exception("Unexpected error in tool '%s'", tool_name)
        return ToolResult(
            success=False, error=f"Tool '{tool_name}' failed unexpectedly"
        )


async def _dispatch(tool_name: str, tool_input: dict, ctx: AgentContext) -> object:
    db = ctx.db
    project = ctx.project
    today = date.today()

    # --- Read tools ---

    if tool_name == "get_tasks":
        filter_status = tool_input.get("filter_status", "all")
        parent_filter = tool_input.get("parent_task_id")
        tasks, _ = await task_service.list_tasks(db, project, per_page=250)

        if parent_filter:
            parent_uuid = UUID(parent_filter)
            tasks = [t for t in tasks if t.parent_task_id == parent_uuid]

        # Batch-load assignees for all tasks in one query
        task_ids = [t.id for t in tasks]
        id_to_name = {t.id: t.name for t in tasks}
        assignee_rows = await db.execute(
            select(Assignment, Resource)
            .join(Resource, Assignment.resource_id == Resource.id)
            .where(Assignment.task_id.in_(task_ids))
        )
        assignees_by_task: dict = {}
        for asgn, res in assignee_rows:
            assignees_by_task.setdefault(asgn.task_id, []).append(
                {"name": res.name, "units": float(asgn.units)}
            )

        result = []
        for t in tasks:
            pct = float(t.percent_complete)
            if filter_status == "overdue" and not (pct < 100 and t.finish_date < today):
                continue
            if filter_status == "in_progress" and not (0 < pct < 100):
                continue
            if filter_status == "completed" and pct < 100:
                continue
            if filter_status == "not_started" and pct != 0:
                continue
            result.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "wbs_code": t.wbs_code,
                    "start_date": str(t.start_date),
                    "finish_date": str(t.finish_date),
                    "duration": t.duration,
                    "percent_complete": pct,
                    "priority": t.priority,
                    "is_summary": t.is_summary,
                    "is_critical": t.is_critical,
                    "is_milestone": t.is_milestone,
                    "notes": t.notes,
                    "parent_task_id": str(t.parent_task_id)
                    if t.parent_task_id
                    else None,
                    "parent_name": id_to_name.get(t.parent_task_id)
                    if t.parent_task_id
                    else None,
                    "color": t.color,
                    "assignees": assignees_by_task.get(t.id, []),
                }
            )
        return {"tasks": result, "total": len(result)}

    if tool_name == "get_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        parent_name = None
        if task.parent_task_id:
            parent = await task_service.get_task_by_id(
                db, task.parent_task_id, project.id
            )
            parent_name = parent.name if parent else None
        assignee_rows = await db.execute(
            select(Assignment, Resource)
            .join(Resource, Assignment.resource_id == Resource.id)
            .where(Assignment.task_id == task_id)
        )
        assignees = [
            {"name": res.name, "units": float(asgn.units)}
            for asgn, res in assignee_rows
        ]
        return {
            "id": str(task.id),
            "name": task.name,
            "wbs_code": task.wbs_code,
            "start_date": str(task.start_date),
            "finish_date": str(task.finish_date),
            "duration": task.duration,
            "percent_complete": float(task.percent_complete),
            "priority": task.priority,
            "is_summary": task.is_summary,
            "is_critical": task.is_critical,
            "is_milestone": task.is_milestone,
            "notes": task.notes,
            "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
            "parent_name": parent_name,
            "color": task.color,
            "assignees": assignees,
        }

    if tool_name == "search_tasks":
        query = (tool_input.get("query") or "").strip()
        if not query:
            raise InvalidOperationError("Search query cannot be empty")
        overdue_only = tool_input.get("overdue_only", False)
        include_parents = tool_input.get("include_parents", False)
        raw_limit = tool_input.get("limit", 50)
        limit = raw_limit if isinstance(raw_limit, int) else 50
        status_input = tool_input.get("status")
        status: TaskStatus | None = None
        if isinstance(status_input, str):
            try:
                status = TaskStatus(status_input)
            except ValueError as exc:
                raise InvalidOperationError(
                    "Invalid status filter for search_tasks"
                ) from exc
        tasks = await task_service.search_tasks(
            db,
            project,
            query=query,
            status=status,
            overdue_only=overdue_only,
            include_parents=include_parents,
            limit=max(1, min(limit, 250)),
        )
        return {
            "tasks": [
                {
                    "id": str(task.id),
                    "name": task.name,
                    "wbs_code": task.wbs_code,
                    "percent_complete": float(task.percent_complete),
                    "finish_date": str(task.finish_date),
                    "status": task.status,
                    "is_critical": task.is_critical,
                    "is_summary": task.is_summary,
                    "parent_task_id": str(task.parent_task_id)
                    if task.parent_task_id
                    else None,
                }
                for task in tasks
            ]
        }

    if tool_name == "get_dependencies":
        deps, _ = await dependency_service.list_dependencies(db, project, per_page=500)
        return {
            "dependencies": [
                {
                    "id": str(d.id),
                    "predecessor_id": str(d.predecessor_id),
                    "successor_id": str(d.successor_id),
                    "type": d.type,
                    "lag": d.lag,
                }
                for d in deps
            ]
        }

    if tool_name == "get_critical_path":
        tasks = await scheduling_service.get_critical_path_tasks(db, project)
        return {
            "critical_path": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "start_date": str(t.start_date),
                    "finish_date": str(t.finish_date),
                    "duration": t.duration,
                }
                for t in tasks
            ]
        }

    if tool_name == "get_project_summary":
        from app.service.ai_service import build_project_context

        ctx_data = await build_project_context(db, project)
        total = len(ctx_data.tasks)
        overdue = sum(
            1
            for t in ctx_data.tasks
            if t.percent_complete < 100 and t.finish_date < today
        )
        in_progress = sum(1 for t in ctx_data.tasks if 0 < t.percent_complete < 100)
        completed = sum(1 for t in ctx_data.tasks if t.percent_complete >= 100)
        return {
            "name": ctx_data.name,
            "status": ctx_data.status,
            "start_date": str(ctx_data.start_date),
            "finish_date": str(ctx_data.finish_date) if ctx_data.finish_date else None,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
        }

    if tool_name == "get_members":
        members, _ = await project_member_service.list_members(
            db, project, per_page=100
        )
        return {"members": members}

    if tool_name == "get_resources":
        include_inactive = tool_input.get("include_inactive", False)
        resources, _ = await resource_service.list_resources(
            db, project, per_page=100, include_inactive=include_inactive
        )
        util_start = project.start_date
        util_end = project.finish_date or today + timedelta(days=90)
        # NOTE: get_project_utilization_summary computes full daily allocations for every
        # resource across the entire project date range (O(days × resources) in Python).
        # We only use two aggregate values from the result: average_utilization and
        # is_over_allocated. For large projects this adds noticeable latency mid-agent-loop.
        # TODO: replace with a lightweight SQL query that computes just the two aggregates
        #       directly, without building the full daily breakdown.
        util_summary = await utilization_service.get_project_utilization_summary(
            db, project, util_start, util_end
        )
        util_by_id: dict = {str(r["resource_id"]): r for r in util_summary["resources"]}
        return {
            "resources": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "type": str(r.type),
                    "max_units": float(r.max_units),
                    "standard_rate": float(r.standard_rate),
                    "is_active": r.is_active,
                    "email": r.email,
                    "group_name": r.group_name,
                    "user_id": str(r.user_id) if r.user_id else None,
                    "current_utilization": float(
                        util_by_id.get(str(r.id), {}).get("average_utilization", 0.0)
                    ),
                    "is_over_allocated": any(
                        d["is_over_allocated"]
                        for d in util_by_id.get(str(r.id), {}).get(
                            "daily_allocations", []
                        )
                    ),
                }
                for r in resources
            ],
            "total": len(resources),
        }

    if tool_name == "get_utilization":
        start_raw = tool_input.get("start_date")
        end_raw = tool_input.get("end_date")
        util_start = date.fromisoformat(start_raw) if start_raw else project.start_date
        util_end = (
            date.fromisoformat(end_raw)
            if end_raw
            else (project.finish_date or today + timedelta(days=90))
        )
        summary = await utilization_service.get_project_utilization_summary(
            db, project, util_start, util_end
        )
        compact = []
        for r in summary["resources"]:
            over_days = [
                {"date": str(d["date"]), "allocated": float(d["allocated_units"])}
                for d in r["daily_allocations"]
                if d["is_over_allocated"]
            ]
            compact.append(
                {
                    "resource_id": str(r["resource_id"]),
                    "resource_name": r["resource_name"],
                    "max_units": float(r["max_units"]),
                    "peak_units": float(r["peak_units"]),
                    "average_utilization": float(r["average_utilization"]),
                    "is_over_allocated": len(over_days) > 0,
                    "over_allocated_days": over_days,
                }
            )
        return {
            "resources": compact,
            "window": {"start": str(util_start), "end": str(util_end)},
        }

    if tool_name == "get_assignments":
        task_id_filter = tool_input.get("task_id")
        resource_id_filter = tool_input.get("resource_id")
        if task_id_filter:
            task = await task_service.get_task_by_id(
                db, UUID(task_id_filter), project.id
            )
            if not task:
                return {"error": "Task not found"}
            assignments = await assignment_service.list_assignments_by_task(db, task)
        else:
            tasks, _ = await task_service.list_tasks(db, project, per_page=250)
            assignments = []
            for t in tasks:
                assignments.extend(
                    await assignment_service.list_assignments_by_task(db, t)
                )
        if resource_id_filter:
            rid = str(UUID(resource_id_filter))
            assignments = [a for a in assignments if str(a.resource_id) == rid]
        return {
            "assignments": [
                {
                    "id": str(a.id),
                    "task_id": str(a.task_id),
                    "resource_id": str(a.resource_id),
                    "units": float(a.units),
                    "start_date": str(a.start_date),
                    "finish_date": str(a.finish_date),
                    "work": a.work,
                    "actual_work": a.actual_work,
                    "percent_work_complete": float(a.percent_work_complete),
                }
                for a in assignments
            ],
            "total": len(assignments),
        }

    if tool_name == "get_activity_log":
        limit = max(1, min(100, int(tool_input.get("limit", 50))))
        entity_type_raw = tool_input.get("entity_type")
        items, total = await activity_log_service.list_activity(
            db,
            project_id=project.id,
            page=1,
            per_page=limit,
            entity_type=entity_type_raw,
        )
        return {
            "entries": [
                {
                    "id": str(item["id"]),
                    "action": str(item["action"]),
                    "entity_type": item["entity_type"],
                    "entity_id": str(item["entity_id"]) if item["entity_id"] else None,
                    "entity_name": item["entity_name"],
                    "user": {
                        "id": str(item["user"]["id"]),
                        "full_name": item["user"]["full_name"],
                    }
                    if item.get("user")
                    else None,
                    "created_at": str(item["created_at"]),
                }
                for item in items
            ],
            "total": total,
        }

    if tool_name == "get_comments":
        task_id_raw = tool_input.get("task_id")
        if task_id_raw:
            entity_type = CommentEntityType.TASK
            entity_id = UUID(task_id_raw)
        else:
            entity_type = CommentEntityType.PROJECT
            entity_id = project.id
        comment_ctx = await comment_service.resolve_entity_context(
            db, entity_type=entity_type, entity_id=entity_id
        )
        comments = await comment_service.list_comments(db, context=comment_ctx)
        return {
            "comments": [
                {
                    "id": str(c["id"]),
                    "author": c["author"]["full_name"],
                    "content": c["content"],
                    "created_at": str(c["created_at"]),
                    "reply_count": len(c["replies"]),
                }
                for c in comments
            ],
            "total": len(comments),
        }

    if tool_name == "get_calendar":
        calendars = await calendar_service.list_calendars(db, project)
        return {
            "calendars": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "is_base": c.is_base,
                    "is_global": c.project_id is None,
                    "work_week": c.work_week,
                }
                for c in calendars
            ]
        }

    if tool_name == "get_insights":
        window = tool_input.get("window", "30d")
        window_days = {"7d": 7, "30d": 30, "90d": 90}.get(window, 30)
        ins_start = today - timedelta(days=window_days - 1)
        return await insights_service.get_project_dashboard(
            db, project, ins_start, today
        )

    # --- Write tools ---

    if tool_name == "create_task":
        payload = {
            "name": tool_input["name"],
            "start_date": date.fromisoformat(tool_input["start_date"]),
            "duration": int(tool_input["duration"]),
            "parent_task_id": UUID(tool_input["parent_task_id"])
            if tool_input.get("parent_task_id")
            else None,
            "notes": tool_input.get("notes"),
            "is_milestone": False,
            "task_type": TaskType.STANDARD,
            "effort_driven": False,
            "constraint_type": ConstraintType.ASAP,
            "constraint_date": None,
            "deadline": None,
            "priority": 0,
            "fixed_cost": Decimal("0"),
            "calendar_id": None,
            "color": None,
        }
        task = await task_service.create_task(db, project, payload)
        return {
            "created": {
                "id": str(task.id),
                "name": task.name,
                "wbs_code": task.wbs_code,
            }
        }

    if tool_name == "update_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        patch = {
            k: v for k, v in tool_input.items() if k != "task_id" and v is not None
        }
        skipped: list[str] = []
        if task.is_summary:
            _rollup_fields = {
                "start_date",
                "finish_date",
                "duration",
                "percent_complete",
            }
            skipped = [f for f in _rollup_fields if f in patch]
            for f in skipped:
                del patch[f]
        if "start_date" in patch:
            patch["start_date"] = date.fromisoformat(patch["start_date"])
        if "percent_complete" in patch:
            patch["percent_complete"] = Decimal(str(patch["percent_complete"]))
        updated = await task_service.update_task(db, task, patch, project=project)
        result: dict = {"updated": {"id": str(updated.id), "name": updated.name}}
        if skipped:
            result["note"] = (
                f"{', '.join(skipped)} skipped — summary task values are auto-calculated from children"
            )
        return result

    if tool_name == "bulk_create_tasks":
        from app.service.contracts.task_bulk import TaskCreateInput

        items: list[TaskCreateInput] = []
        for t in tool_input.get("tasks", []):
            items.append(
                {
                    "name": t["name"],
                    "start_date": date.fromisoformat(t["start_date"]),
                    "duration": int(t["duration"]),
                    "parent_task_id": None,
                    "notes": t.get("notes"),
                    "is_milestone": False,
                    "task_type": TaskType.STANDARD,
                    "effort_driven": False,
                    "constraint_type": ConstraintType.ASAP,
                    "constraint_date": None,
                    "deadline": None,
                    "priority": 0,
                    "fixed_cost": Decimal("0"),
                    "calendar_id": None,
                    "color": None,
                }
            )
        created, _ = await task_bulk_service.bulk_create_tasks(db, project, items)
        return {
            "created_count": len(created),
            "tasks": [{"id": str(t.id), "name": t.name} for t in created],
        }

    if tool_name == "add_dependency":
        from app.service.contracts.dependency import DependencyCreateInput

        payload: DependencyCreateInput = {
            "predecessor_id": UUID(tool_input["predecessor_id"]),
            "successor_id": UUID(tool_input["successor_id"]),
            "type": DependencyType(tool_input.get("type", "FS")),
            "lag": 0,
            "lag_format": LagFormat.DURATION,
        }
        dep = await dependency_service.create_dependency(db, project, payload)
        return {"created": {"id": str(dep.id), "type": str(dep.type)}}

    if tool_name == "indent_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        updated = await task_hierarchy_service.indent_task(db, project, task)
        return {
            "indented": {
                "id": str(updated.id),
                "name": updated.name,
                "wbs_code": updated.wbs_code,
            }
        }

    if tool_name == "outdent_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        updated = await task_hierarchy_service.outdent_task(db, project, task)
        return {
            "outdented": {
                "id": str(updated.id),
                "name": updated.name,
                "wbs_code": updated.wbs_code,
            }
        }

    if tool_name == "reorder_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        after_id = (
            UUID(tool_input["after_task_id"])
            if tool_input.get("after_task_id")
            else None
        )
        before_id = (
            UUID(tool_input["before_task_id"])
            if tool_input.get("before_task_id")
            else None
        )
        new_parent = (
            UUID(tool_input["new_parent_id"])
            if tool_input.get("new_parent_id")
            else None
        )
        updated = await task_hierarchy_service.reorder_task(
            db, project, task, after_id, before_id, new_parent
        )
        return {"reordered": {"id": str(updated.id), "name": updated.name}}

    if tool_name == "calculate_schedule":
        result = await scheduling_service.calculate_schedule(db, project)
        return {
            "scheduled": True,
            "tasks_updated": result.tasks_updated,
            "critical_path_tasks": len(result.critical_path_task_ids),
            "project_finish_date": str(result.project_finish_date)
            if result.project_finish_date
            else None,
        }

    if tool_name == "assign_resource":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        payload: AssignmentCreateInput = {
            "resource_id": UUID(tool_input["resource_id"]),
            "units": Decimal(str(tool_input.get("units", 1.0))),
            "start_date": task.start_date,
            "finish_date": task.finish_date,
            "work": 0,
            "work_contour": WorkContour.FLAT,
            "rate_table": RateTable.A,
        }
        assignment = await assignment_service.create_assignment(db, task, payload)
        return {
            "assigned": {
                "id": str(assignment.id),
                "task_id": str(assignment.task_id),
                "resource_id": str(assignment.resource_id),
                "units": float(assignment.units),
                "start_date": str(assignment.start_date),
                "finish_date": str(assignment.finish_date),
            }
        }

    if tool_name == "unassign_resource":
        assignment_id = UUID(tool_input["assignment_id"])
        assignment = await assignment_service.get_assignment_by_id(db, assignment_id)
        if not assignment:
            return {"error": "Assignment not found"}
        task = await task_service.get_task_by_id(db, assignment.task_id, project.id)
        if not task:
            return {"error": "Assignment does not belong to this project"}
        await assignment_service.delete_assignment(db, assignment)
        return {
            "unassigned": {
                "assignment_id": str(assignment_id),
                "task_id": str(assignment.task_id),
                "resource_id": str(assignment.resource_id),
            }
        }

    if tool_name == "post_comment":
        from app.models.user import User

        content = tool_input["content"]
        task_id_raw = tool_input.get("task_id")
        if task_id_raw:
            entity_type = CommentEntityType.TASK
            entity_id = UUID(task_id_raw)
        else:
            entity_type = CommentEntityType.PROJECT
            entity_id = project.id
        result = await db.execute(select(User).where(User.id == ctx.user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {"error": "Agent user not found"}
        comment_ctx = await comment_service.resolve_entity_context(
            db, entity_type=entity_type, entity_id=entity_id
        )
        comment = await comment_service.create_comment(
            db, context=comment_ctx, author=user, content=content
        )
        return {
            "posted": {
                "id": str(comment.id),
                "entity_type": str(entity_type),
                "entity_id": str(entity_id),
                "content": comment.content,
            }
        }

    if tool_name == "send_notification":
        target_user_id = UUID(tool_input["user_id"])
        notification = await notification_service.create_notification(
            db,
            user_id=target_user_id,
            type=NotificationType.TASK_UPDATED,
            title=tool_input["title"],
            message=tool_input.get("message"),
            entity_type="project",
            entity_id=project.id,
            actor_id=ctx.user_id,
        )
        await db.commit()
        return {
            "sent": {
                "notification_id": str(notification.id),
                "user_id": str(target_user_id),
                "title": tool_input["title"],
            }
        }

    # --- Destructive tools ---

    if tool_name == "delete_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        await task_service.soft_delete_task(db, task, project=project)
        return {"deleted": {"id": str(task_id), "name": task.name}}

    if tool_name == "delete_dependency":
        dep_id = UUID(tool_input["dependency_id"])
        dep = await dependency_service.get_dependency_by_id(db, dep_id, project.id)
        if not dep:
            return {"error": "Dependency not found"}
        await dependency_service.delete_dependency(db, dep, project=project)
        return {"deleted": {"id": str(dep_id)}}

    # --- UI tools (no DB — frontend handles these via the ui_action SSE event) ---

    if tool_name in UI_TOOLS:
        return {"action": tool_name, "payload": tool_input, "status": "dispatched"}

    raise InvalidOperationError(f"Unknown tool: {tool_name}")
