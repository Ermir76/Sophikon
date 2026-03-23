"""
Task business logic.

Handles listing, creating, updating, and soft-deleting tasks.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.enums import AuditAction, ConstraintType, TaskStatus, TaskType
from app.models.project import Project
from app.models.task import Task
from app.repository import task_repo
from app.service import (
    activity_log_service,
    calendar_service,
    realtime_service,
    scheduling_service,
)
from app.service.activity_log_service import ActivityContext
from app.service.task_rollup_service import (
    apply_summary_rollup,
    clear_summary_rollup,
    load_project_rollup_calendar,
    sync_leaf_duration_progress,
    validate_summary_rollup_edit,
)

# Fields that affect the schedule — changes trigger auto-recalculation
_SCHEDULE_FIELDS = {
    "duration",
    "start_date",
    "finish_date",
    "constraint_type",
    "constraint_date",
    "is_milestone",
    "calendar_id",
}


async def _load_task_comment_counts(
    db: AsyncSession,
    task_ids: list[UUID],
) -> dict[UUID, int]:
    return await task_repo.count_comments_for_tasks(db, task_ids=task_ids)


def _resolve_hours_per_day(settings: object) -> int:
    """Return a safe working-hours default for duration-to-date math."""
    if not isinstance(settings, dict):
        return 8
    value = settings.get("hours_per_day")
    if isinstance(value, int) and value > 0:
        return value
    return 8


def _compute_initial_finish_date(
    *,
    start_date,
    duration_minutes: int,
    is_milestone: bool,
    minutes_per_day: int,
):
    """
    Compute initial finish date using inclusive day semantics.
    1 working day (minutes_per_day) => finish_date == start_date.
    """
    if is_milestone:
        return start_date
    duration_days = max(1, -(-duration_minutes // minutes_per_day))
    return start_date + timedelta(days=duration_days - 1)


async def list_tasks(
    db: AsyncSession,
    project: Project,
    *,
    page: int = 1,
    per_page: int = 50,
    include_deleted: bool = False,
) -> tuple[list[Task], int]:
    """
    List tasks for a project in tree order (depth-first).

    Returns (tasks, total_count).
    """
    tasks, total = await task_repo.list_tasks_for_project(
        db,
        project_id=project.id,
        page=page,
        per_page=per_page,
        include_deleted=include_deleted,
    )
    task_ids = [task.id for task in tasks]
    comment_counts = await _load_task_comment_counts(db, task_ids)
    assignment_map = await task_repo.list_assignments_for_tasks(db, task_ids=task_ids)
    for task in tasks:
        task.comments_count = comment_counts.get(task.id, 0)
        task.assignment_summaries = assignment_map.get(task.id, [])

    return tasks, total


async def regenerate_wbs_codes(db: AsyncSession, project_id: UUID) -> None:
    """
    Regenerate WBS codes, outline levels, sort_order, and summary flags
    for all tasks in a project. Fixes orphaned tasks and flushes without committing.
    """
    tasks = await task_repo.list_tasks_for_wbs_regen(db, project_id=project_id)

    task_map = {task.id: task for task in tasks}
    children_map: dict[UUID, list[Task]] = {}
    roots: list[Task] = []

    for task in tasks:
        if task.parent_task_id:
            if task.parent_task_id not in task_map:
                task.parent_task_id = None
                roots.append(task)
            else:
                children_map.setdefault(task.parent_task_id, []).append(task)
        else:
            roots.append(task)

    counter = 0

    def traverse(node: Task, current_wbs_prefix: str, level: int) -> None:
        nonlocal counter
        counter += 1
        node.sort_order = counter
        node.outline_level = level
        children = children_map.get(node.id, [])
        node.is_summary = len(children) > 0

        for i, child in enumerate(children, start=1):
            child_wbs = f"{current_wbs_prefix}.{i}"
            child.wbs_code = child_wbs
            traverse(child, child_wbs, level + 1)

    for i, root in enumerate(roots, start=1):
        root.wbs_code = str(i)
        traverse(root, str(i), 1)

    await db.flush()


async def create_task(
    db: AsyncSession,
    project: Project,
    payload: dict[str, Any],
    activity_context: ActivityContext | None = None,
) -> Task:
    """Create a new task in the project."""
    calendar_id = payload.get("calendar_id")
    if calendar_id is not None:
        await calendar_service.ensure_project_or_global_calendar(
            db,
            calendar_id=calendar_id,
            project_id=project.id,
        )

    # Lock the project row — serializes concurrent task creates for this project
    await task_repo.lock_project_row(db, project_id=project.id)

    # Now safe — no other transaction can be here for the same project
    # Per-sibling-group order_index: MAX within the same parent
    parent_task_id = payload.get("parent_task_id")
    order_index = await task_repo.get_next_order_index(
        db,
        project_id=project.id,
        parent_task_id=parent_task_id,
    )

    # Calculate outline_level and wbs_code
    outline_level = 1
    wbs_code = str(order_index)

    if parent_task_id:
        parent = await task_repo.get_active_task(
            db,
            task_id=parent_task_id,
            project_id=project.id,
        )
        if not parent:
            raise InvalidOperationError("Parent task not found in this project")

        outline_level = parent.outline_level + 1
        # Count siblings under this parent
        sibling_count = await task_repo.count_active_siblings(
            db,
            project_id=project.id,
            parent_task_id=parent_task_id,
        )
        wbs_code = f"{parent.wbs_code}.{sibling_count + 1}"

        # Mark parent as summary
        parent.is_summary = True

    # Calculate finish_date based on duration (simple: 1 day = 480 minutes)
    hours_per_day = _resolve_hours_per_day(project.settings)
    minutes_per_day = hours_per_day * 60
    finish_date = _compute_initial_finish_date(
        start_date=payload["start_date"],
        duration_minutes=payload["duration"],
        is_milestone=payload.get("is_milestone", False),
        minutes_per_day=minutes_per_day,
    )

    task = Task(
        project_id=project.id,
        parent_task_id=parent_task_id,
        name=payload["name"],
        notes=payload.get("notes"),
        wbs_code=wbs_code,
        outline_level=outline_level,
        order_index=order_index,
        start_date=payload["start_date"],
        finish_date=finish_date,
        duration=payload["duration"],
        actual_duration=0,
        remaining_duration=payload["duration"],
        is_milestone=payload.get("is_milestone", False),
        calendar_id=calendar_id,
        task_type=payload.get("task_type", TaskType.FIXED_UNITS),
        effort_driven=payload.get("effort_driven", True),
        constraint_type=payload.get("constraint_type", ConstraintType.ASAP),
        constraint_date=payload.get("constraint_date"),
        deadline=payload.get("deadline"),
        priority=payload.get("priority", 500),
        fixed_cost=payload.get("fixed_cost", 0),
        status=payload.get("status", TaskStatus.BACKLOG),
    )
    sync_leaf_duration_progress(task)
    db.add(task)
    await db.flush()
    if parent_task_id:
        await recalculate_summary(db, project.id, parent_task_id)

    await regenerate_wbs_codes(db, project.id)

    # Auto-recalculate schedule after task creation
    if project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="task",
        entity_id=task.id,
        entity_name=task.name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="task",
        action=AuditAction.CREATED,
        entity_id=task.id,
        entity_name=task.name,
        context=activity_context,
    )
    await realtime_service.commit_and_publish(db)
    await db.refresh(task)
    task.comments_count = 0
    return task


async def get_task_by_id(
    db: AsyncSession,
    task_id: UUID,
    project_id: UUID,
) -> Task | None:
    """Get a task by ID within a project (excludes deleted)."""
    row = await task_repo.get_task_with_comment_count(
        db,
        task_id=task_id,
        project_id=project_id,
    )
    if row is None:
        return None

    task, comments_count = row
    task.comments_count = comments_count
    return task


async def update_task(
    db: AsyncSession,
    task: Task,
    patch: dict[str, Any],
    project: Project | None = None,
    activity_context: ActivityContext | None = None,
) -> Task:
    """Update a task with partial data."""
    if "calendar_id" in patch and patch["calendar_id"] is not None:
        await calendar_service.ensure_project_or_global_calendar(
            db,
            calendar_id=patch["calendar_id"],
            project_id=task.project_id,
        )

    before = {field: getattr(task, field) for field in patch}
    validate_summary_rollup_edit(task, patch)

    for field, value in patch.items():
        setattr(task, field, value)
    if not task.is_summary:
        sync_leaf_duration_progress(task)

    # If parent changed, recalculate for both old and new parents
    # But update_task doesn't currently allow changing parent_task_id directly based on schema
    # Just recalculate the current parent
    await db.flush()
    if task.parent_task_id:
        # Need the project_id, which we don't have easily accessible in update_task params,
        # but we can get it from the task object.
        await recalculate_summary(db, task.project_id, task.parent_task_id)

    # Auto-recalculate schedule if scheduling-relevant fields changed
    if project and patch.keys() & _SCHEDULE_FIELDS:
        if project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(task, field) for field in patch},
    )
    if changes is not None:
        await activity_log_service.log_activity(
            db,
            project_id=task.project_id,
            action=AuditAction.UPDATED,
            entity_type="task",
            entity_id=task.id,
            entity_name=task.name,
            changes=changes,
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=task.project_id,
            entity_type="task",
            action=AuditAction.UPDATED,
            entity_id=task.id,
            entity_name=task.name,
            context=activity_context,
            metadata=changes,
        )

    await realtime_service.commit_and_publish(db)
    await db.refresh(task)
    counts = await _load_task_comment_counts(db, [task.id])
    task.comments_count = counts.get(task.id, 0)
    return task


async def soft_delete_task(
    db: AsyncSession,
    task: Task,
    project: Project | None = None,
    activity_context: ActivityContext | None = None,
) -> None:
    """
    Soft delete a task and cascade to children, assignments (hard), dependencies (hard).

    NOTE: This function calls `await db.flush()` but NOT `commit()`.
    Because it recurses to delete children, the CALLER MUST COMMIT the transaction
    after the top-level call finishes, to ensure atomicity.
    """
    # 1. Soft delete children recursively
    children = await task_repo.list_active_children(db, parent_task_id=task.id)
    for child in children:
        # Pass None for project in recursive calls to prevent redundant recalculations
        await soft_delete_task(db, child, project=None, activity_context=None)

    # 2. Hard delete assignments (Assignments belong to task -> remove)
    # Using CORE delete for efficiency

    await task_repo.delete_assignments_for_task(db, task_id=task.id)

    # 3. Hard delete dependencies (Predecessor/Successor relationships involving this task)
    await task_repo.delete_dependencies_for_task(db, task_id=task.id)

    # 4. Soft delete comments for this task entity
    comments = await task_repo.list_active_task_comments(db, task_id=task.id)
    deleted_at = datetime.now(UTC)
    for comment in comments:
        comment.is_deleted = True
        comment.deleted_at = deleted_at

    # 5. Soft delete the task itself
    task.is_deleted = True
    task.deleted_at = deleted_at
    await db.flush()

    if task.parent_task_id:
        await recalculate_summary(db, task.project_id, task.parent_task_id)

    # Auto-recalculate schedule after task deletion (top-level only)
    if project and project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    if activity_context is not None:
        await activity_log_service.log_activity(
            db,
            project_id=task.project_id,
            action=AuditAction.DELETED,
            entity_type="task",
            entity_id=task.id,
            entity_name=task.name,
            context=activity_context,
        )
        # TODO(2026-03-08): This function queues realtime events but does not commit.
        # Keep call sites on realtime_service.commit_and_publish(db), or move to a
        # single wrapper API that enforces commit+publish for task deletions.
        realtime_service.queue_entity_event(
            db,
            project_id=task.project_id,
            entity_type="task",
            action=AuditAction.DELETED,
            entity_id=task.id,
            entity_name=task.name,
            context=activity_context,
        )


async def recalculate_summary(
    db: AsyncSession, project_id: UUID, parent_task_id: UUID | None
) -> None:
    """
    Recalculate summary task metrics based on its children, and recurse upwards.
    Called when a child task is mutated.
    """
    if parent_task_id is None:
        return

    project = await task_repo.get_project_by_id(db, project_id=project_id)
    if not project:
        return
    work_week, exceptions = await load_project_rollup_calendar(db, project)

    parent = await task_repo.get_task_for_rollup(
        db,
        task_id=parent_task_id,
        project_id=project_id,
    )
    if not parent:
        return

    children = await task_repo.list_children_for_rollup(
        db,
        parent_task_id=parent.id,
        project_id=project_id,
    )

    if not children:
        clear_summary_rollup(parent, work_week, exceptions)
        await db.flush()
        # Recurse up in case this parent is itself a child
        await recalculate_summary(db, project_id, parent.parent_task_id)
        return

    apply_summary_rollup(parent, children, work_week, exceptions)
    await db.flush()
    await recalculate_summary(db, project_id, parent.parent_task_id)
