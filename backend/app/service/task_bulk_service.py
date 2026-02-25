"""
Task bulk operations logic.

Handles creating, updating, and soft-deleting tasks in batch.
"""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.project import Project
from app.models.task import Task
from app.schema.task import TaskBulkUpdateItem, TaskCreate
from app.service.task_service import (
    recalculate_summary,
    regenerate_wbs_codes,
    soft_delete_task,
)


async def bulk_create_tasks(
    db: AsyncSession,
    project: Project,
    data: list[TaskCreate],
) -> tuple[list[Task], list[dict]]:
    """
    Bulk create tasks in a single transaction.
    """
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    # Track max order_index per sibling group (keyed by parent_task_id, None for roots)
    max_order_per_parent: dict[UUID | None, int] = {}

    async def get_next_order(parent_id: UUID | None) -> int:
        if parent_id not in max_order_per_parent:
            parent_condition = (
                Task.parent_task_id.is_(None)
                if parent_id is None
                else Task.parent_task_id == parent_id
            )
            result = await db.execute(
                select(func.coalesce(func.max(Task.order_index), 0)).where(
                    Task.project_id == project.id,
                    parent_condition,
                    Task.is_deleted == False,  # noqa: E712
                )
            )
            max_order_per_parent[parent_id] = result.scalar() or 0
        max_order_per_parent[parent_id] += 1
        return max_order_per_parent[parent_id]

    hours_per_day = project.settings.get("hours_per_day", 8)
    minutes_per_day = hours_per_day * 60

    created_tasks = []
    errors = []
    parent_ids_to_recalc = set()

    for idx, task_data in enumerate(data):
        try:
            async with db.begin_nested():
                if task_data.parent_task_id:
                    parent_result = await db.execute(
                        select(Task).where(
                            Task.id == task_data.parent_task_id,
                            Task.project_id == project.id,
                            Task.is_deleted == False,  # noqa: E712
                        )
                    )
                    parent = parent_result.scalar_one_or_none()
                    if not parent:
                        raise InvalidOperationError(
                            f"Parent task {task_data.parent_task_id} not found"
                        )
                    parent_ids_to_recalc.add(parent.id)

                order_index = await get_next_order(task_data.parent_task_id)
                duration_days = (
                    max(1, task_data.duration // minutes_per_day)
                    if not task_data.is_milestone
                    else 0
                )
                finish_date = task_data.start_date + timedelta(days=duration_days)

                task = Task(
                    project_id=project.id,
                    parent_task_id=task_data.parent_task_id,
                    name=task_data.name,
                    notes=task_data.notes,
                    wbs_code="TEMP",  # Will be fixed by regenerate_wbs_codes
                    outline_level=1,  # Will be fixed by regenerate_wbs_codes
                    order_index=order_index,
                    start_date=task_data.start_date,
                    finish_date=finish_date,
                    duration=task_data.duration,
                    remaining_duration=task_data.duration,
                    is_milestone=task_data.is_milestone,
                    task_type=task_data.task_type,
                    effort_driven=task_data.effort_driven,
                    constraint_type=task_data.constraint_type,
                    constraint_date=task_data.constraint_date,
                    deadline=task_data.deadline,
                    priority=task_data.priority,
                    fixed_cost=task_data.fixed_cost,
                )
                db.add(task)
                await db.flush()  # We need the ID
                created_tasks.append(task)
        except Exception as e:
            errors.append({"index": idx, "message": str(e)})
            continue

    if created_tasks:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        await regenerate_wbs_codes(db, project.id)
        await db.commit()
        for t in created_tasks:
            await db.refresh(t)

    return created_tasks, errors


async def bulk_update_tasks(
    db: AsyncSession,
    project: Project,
    updates: list[TaskBulkUpdateItem],
) -> tuple[int, int, list[dict]]:
    """
    Bulk update tasks in a single transaction.
    """
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    succeeded = 0
    failed = 0
    errors = []
    parent_ids_to_recalc = set()
    needs_wbs_regen = False

    for idx, update_item in enumerate(updates):
        try:
            async with db.begin_nested():
                task_result = await db.execute(
                    select(Task).where(
                        Task.id == update_item.id,
                        Task.project_id == project.id,
                        Task.is_deleted == False,  # noqa: E712
                    )
                )
                task = task_result.scalar_one_or_none()
                if not task:
                    raise InvalidOperationError(f"Task {update_item.id} not found")

                # Store parents for recalculation before mutating
                if task.parent_task_id:
                    parent_ids_to_recalc.add(task.parent_task_id)

                update_data = update_item.data.model_dump(exclude_unset=True)

                # Check if parent changed
                if (
                    "parent_task_id" in update_data
                    and update_data["parent_task_id"] != task.parent_task_id
                ):
                    needs_wbs_regen = True
                    new_p_id = update_data["parent_task_id"]
                    if new_p_id:
                        new_p_result = await db.execute(
                            select(Task).where(
                                Task.id == new_p_id,
                                Task.project_id == project.id,
                                Task.is_deleted == False,  # noqa: E712
                            )
                        )
                        if not new_p_result.scalar_one_or_none():
                            raise InvalidOperationError(
                                f"New parent task {new_p_id} not found"
                            )
                        parent_ids_to_recalc.add(new_p_id)

                for field, value in update_data.items():
                    setattr(task, field, value)

                # Store the current parent if it just changed
                if task.parent_task_id:
                    parent_ids_to_recalc.add(task.parent_task_id)

                await db.flush()
                succeeded += 1
        except Exception as e:
            failed += 1
            errors.append({"index": idx, "task_id": update_item.id, "message": str(e)})
            continue

    if succeeded > 0:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        if needs_wbs_regen:
            await regenerate_wbs_codes(db, project.id)

        await db.commit()
    else:
        # If everything failed, rollback just in case
        await db.rollback()

    return succeeded, failed, errors


async def bulk_delete_tasks(
    db: AsyncSession,
    project: Project,
    task_ids: list[UUID],
) -> tuple[int, int, list[dict]]:
    """
    Bulk soft-delete tasks.
    """
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    succeeded = 0
    failed = 0
    errors = []
    parent_ids_to_recalc = set()

    for idx, task_id in enumerate(task_ids):
        try:
            async with db.begin_nested():
                task_result = await db.execute(
                    select(Task).where(
                        Task.id == task_id,
                        Task.project_id == project.id,
                        Task.is_deleted == False,  # noqa: E712
                    )
                )
                task = task_result.scalar_one_or_none()
                if not task:
                    raise InvalidOperationError(f"Task {task_id} not found")

                if task.parent_task_id:
                    parent_ids_to_recalc.add(task.parent_task_id)

                # Use our existing recursive soft delete
                # (which correctly uses db.flush() internally)
                await soft_delete_task(db, task)

                succeeded += 1
        except Exception as e:
            failed += 1
            errors.append({"index": idx, "task_id": task_id, "message": str(e)})
            continue

    if succeeded > 0:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        await regenerate_wbs_codes(db, project.id)
        await db.commit()
    else:
        await db.rollback()

    return succeeded, failed, errors
