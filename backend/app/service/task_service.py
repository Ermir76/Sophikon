"""
Task business logic.

Handles listing, creating, updating, and soft-deleting tasks.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.assignment import Assignment
from app.models.dependency import Dependency
from app.models.enums import AuditAction
from app.models.project import Project
from app.models.task import Task
from app.schema.task import TaskCreate, TaskUpdate
from app.service import activity_log_service, scheduling_service
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
}


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
    base_query = select(Task).where(Task.project_id == project.id)

    if not include_deleted:
        base_query = base_query.where(Task.is_deleted == False)  # noqa: E712

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering by sort_order (global DFS traversal order)
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Task.sort_order.asc()).offset(offset).limit(per_page)
    )

    result = await db.execute(paginated_query)
    tasks = list(result.scalars().all())

    return tasks, total


async def regenerate_wbs_codes(db: AsyncSession, project_id: UUID) -> None:
    """
    Regenerate WBS codes, outline levels, sort_order, and summary flags
    for all tasks in a project. Fixes orphaned tasks and flushes without committing.
    """
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.asc())
    )
    tasks = list(result.scalars().all())

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
    data: TaskCreate,
    activity_context: ActivityContext | None = None,
) -> Task:
    """Create a new task in the project."""

    # Lock the project row — serializes concurrent task creates for this project
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    # Now safe — no other transaction can be here for the same project
    # Per-sibling-group order_index: MAX within the same parent
    parent_condition = (
        Task.parent_task_id.is_(None)
        if data.parent_task_id is None
        else Task.parent_task_id == data.parent_task_id
    )
    result = await db.execute(
        select(func.coalesce(func.max(Task.order_index), 0) + 1).where(
            Task.project_id == project.id,
            parent_condition,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    order_index = result.scalar() or 1

    # Calculate outline_level and wbs_code
    outline_level = 1
    wbs_code = str(order_index)

    if data.parent_task_id:
        parent_result = await db.execute(
            select(Task).where(
                Task.id == data.parent_task_id,
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise InvalidOperationError("Parent task not found in this project")

        outline_level = parent.outline_level + 1
        # Count siblings under this parent
        sibling_count_result = await db.execute(
            select(func.count()).where(
                Task.parent_task_id == data.parent_task_id,
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        sibling_count = sibling_count_result.scalar() or 0
        wbs_code = f"{parent.wbs_code}.{sibling_count + 1}"

        # Mark parent as summary
        parent.is_summary = True

    # Calculate finish_date based on duration (simple: 1 day = 480 minutes)
    hours_per_day = project.settings.get("hours_per_day", 8)
    minutes_per_day = hours_per_day * 60
    duration_days = (
        max(1, data.duration // minutes_per_day) if not data.is_milestone else 0
    )
    # TODO(2026-03-07): Align finish_date convention with scheduling/calendar math
    # (inclusive vs exclusive end date) across create, rollup, and scheduler flows.
    finish_date = data.start_date + timedelta(days=duration_days)

    task = Task(
        project_id=project.id,
        parent_task_id=data.parent_task_id,
        name=data.name,
        notes=data.notes,
        wbs_code=wbs_code,
        outline_level=outline_level,
        order_index=order_index,
        start_date=data.start_date,
        finish_date=finish_date,
        duration=data.duration,
        actual_duration=0,
        remaining_duration=data.duration,
        is_milestone=data.is_milestone,
        task_type=data.task_type,
        effort_driven=data.effort_driven,
        constraint_type=data.constraint_type,
        constraint_date=data.constraint_date,
        deadline=data.deadline,
        priority=data.priority,
        fixed_cost=data.fixed_cost,
    )
    sync_leaf_duration_progress(task)
    db.add(task)
    await db.flush()
    if data.parent_task_id:
        await recalculate_summary(db, project.id, data.parent_task_id)

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
    await db.commit()
    await db.refresh(task)
    return task


async def get_task_by_id(
    db: AsyncSession,
    task_id: UUID,
    project_id: UUID,
) -> Task | None:
    """Get a task by ID within a project (excludes deleted)."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdate,
    project: Project | None = None,
    activity_context: ActivityContext | None = None,
) -> Task:
    """Update a task with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    before = {field: getattr(task, field) for field in update_data}
    validate_summary_rollup_edit(task, update_data)

    for field, value in update_data.items():
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
    if project and update_data.keys() & _SCHEDULE_FIELDS:
        if project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(task, field) for field in update_data},
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

    await db.commit()
    await db.refresh(task)
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
    children_result = await db.execute(
        select(Task).where(Task.parent_task_id == task.id, Task.is_deleted == False)  # noqa: E712
    )
    children = children_result.scalars().all()
    for child in children:
        # Pass None for project in recursive calls to prevent redundant recalculations
        await soft_delete_task(db, child, project=None, activity_context=None)

    # 2. Hard delete assignments (Assignments belong to task -> remove)
    # Using CORE delete for efficiency

    await db.execute(delete(Assignment).where(Assignment.task_id == task.id))

    # 3. Hard delete dependencies (Predecessor/Successor relationships involving this task)
    await db.execute(
        delete(Dependency).where(
            (Dependency.predecessor_id == task.id)
            | (Dependency.successor_id == task.id)
        )
    )

    # 4. Soft delete the task itself
    task.is_deleted = True
    task.deleted_at = datetime.now(UTC)
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


async def recalculate_summary(
    db: AsyncSession, project_id: UUID, parent_task_id: UUID | None
) -> None:
    """
    Recalculate summary task metrics based on its children, and recurse upwards.
    Called when a child task is mutated.
    """
    if parent_task_id is None:
        return

    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        return
    work_week, exceptions = await load_project_rollup_calendar(db, project)

    parent_result = await db.execute(
        select(Task).where(
            Task.id == parent_task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    parent = parent_result.scalar_one_or_none()
    if not parent:
        return

    children_result = await db.execute(
        select(Task).where(
            Task.parent_task_id == parent.id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    children = list(children_result.scalars().all())

    if not children:
        clear_summary_rollup(parent, work_week, exceptions)
        await db.flush()
        # Recurse up in case this parent is itself a child
        await recalculate_summary(db, project_id, parent.parent_task_id)
        return

    apply_summary_rollup(parent, children, work_week, exceptions)
    await db.flush()
    await recalculate_summary(db, project_id, parent.parent_task_id)
