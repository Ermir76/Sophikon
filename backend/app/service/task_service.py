"""
Task business logic.

Handles listing, creating, updating, and soft-deleting tasks.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.dependency import Dependency
from app.models.project import Project
from app.models.task import Task
from app.schema.task import TaskCreate, TaskUpdate


async def list_tasks(
    db: AsyncSession,
    project: Project,
    *,
    page: int = 1,
    per_page: int = 50,
    include_deleted: bool = False,
) -> tuple[list[Task], int]:
    """
    List tasks for a project, ordered by order_index.

    Returns (tasks, total_count).
    """
    base_query = select(Task).where(Task.project_id == project.id)

    if not include_deleted:
        base_query = base_query.where(Task.is_deleted == False)  # noqa: E712

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Task.order_index.asc()).offset(offset).limit(per_page)
    )

    result = await db.execute(paginated_query)
    tasks = list(result.scalars().all())

    return tasks, total


async def create_task(
    db: AsyncSession,
    project: Project,
    data: TaskCreate,
) -> Task:
    """Create a new task in the project."""

    # Lock the project row — serializes concurrent task creates for this project
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    # Now safe — no other transaction can be here for the same project
    result = await db.execute(
        select(func.coalesce(func.max(Task.order_index), 0) + 1).where(
            Task.project_id == project.id,
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
            raise HTTPException(
                status_code=400,
                detail="Parent task not found in this project",
            )

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
    db.add(task)
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
) -> Task:
    """Update a task with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


async def soft_delete_task(
    db: AsyncSession,
    task: Task,
) -> None:
    """
    Soft delete a task and cascade to children, assignments (hard), dependencies (hard).
    """
    # 1. Soft delete children recursively
    children_result = await db.execute(
        select(Task).where(Task.parent_task_id == task.id, Task.is_deleted == False)  # noqa: E712
    )
    children = children_result.scalars().all()
    for child in children:
        await soft_delete_task(db, child)

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
    await db.commit()
