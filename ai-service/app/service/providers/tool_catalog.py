"""Shared AI tool catalog used across provider adapters."""

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_tasks",
        "description": (
            "Get all tasks for the project. Returns tasks with WBS codes, dates, "
            "progress percentage, priority, and hierarchy. Use this to understand "
            "the project state before answering questions or taking actions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "enum": ["all", "overdue", "in_progress", "completed", "not_started"],
                    "description": "Filter tasks by status. Omit for all tasks.",
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
        "description": "Search tasks by name or filter by condition.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search in task name and notes."},
                "overdue_only": {"type": "boolean"},
                "in_progress_only": {"type": "boolean"},
            },
        },
    },
    {
        "name": "get_dependencies",
        "description": "Get all task dependencies in the project (predecessor -> successor relationships).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_critical_path",
        "description": (
            "Get the critical path - the sequence of tasks that determines the "
            "minimum project duration. Delays to critical path tasks delay the whole project."
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
                "notes": {"type": "string", "description": "Task description or notes."},
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
                "duration": {"type": "integer", "description": "Duration in minutes.", "minimum": 60},
                "notes": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "bulk_create_tasks",
        "description": (
            "Create multiple tasks at once. Use this when generating a project plan "
            "or when the user asks to create many tasks - do not create them one by one."
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
                "successor_id": {"type": "string", "description": "UUID of the task that starts after."},
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
            "properties": {"task_id": {"type": "string", "description": "Task UUID to indent"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "outdent_task",
        "description": "Move a task one level up in the WBS hierarchy (outdent/promote).",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string", "description": "Task UUID to outdent"}},
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
                    "description": "Place task after this task. Null = move to beginning of group.",
                },
                "before_task_id": {
                    "type": "string",
                    "description": "Place task before this task. Null = move to end of group.",
                },
                "new_parent_id": {
                    "type": "string",
                    "description": "Move under this parent task. Null = keep current parent.",
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
        "name": "delete_task",
        "description": (
            "Delete a task (soft delete - recoverable). "
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
                "dependency_id": {"type": "string", "description": "Dependency UUID to remove"},
                "reason": {"type": "string", "description": "Why this dependency should be removed."},
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
                    "enum": ["overview", "tasks", "gantt", "calendar", "resources", "reports"],
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
            "properties": {"task_id": {"type": "string", "description": "Task UUID to open"}},
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
                    "enum": ["all", "overdue", "in_progress", "completed", "critical_path"],
                }
            },
            "required": ["filter"],
        },
    },
]
