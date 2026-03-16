"""
Task bulk operations logic.

Handles creating, updating, and soft-deleting tasks in batch.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.enums import AuditAction
from app.models.project import Project
from app.models.task import Task
from app.service import (
    activity_log_service,
    calendar_service,
    realtime_service,
    scheduling_service,
)
from app.service.activity_log_service import ActivityContext
from app.service.contracts.task_bulk import TaskBulkUpdateInputItem, TaskCreateInput
from app.service.task_rollup_service import (
    sync_leaf_duration_progress,
    validate_summary_rollup_edit,
)
from app.service.task_service import (
    _SCHEDULE_FIELDS,
    _compute_initial_finish_date,
    _resolve_hours_per_day,
    recalculate_summary,
    regenerate_wbs_codes,
    soft_delete_task,
)


async def bulk_create_tasks(
    db: AsyncSession,
    project: Project,
    data: list[TaskCreateInput],
    activity_context: ActivityContext | None = None,
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

    hours_per_day = _resolve_hours_per_day(project.settings)
    minutes_per_day = hours_per_day * 60

    created_tasks = []
    errors = []
    parent_ids_to_recalc = set()

    for idx, task_data in enumerate(data):
        pending_before = len(
            db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY, [])
        )
        try:
            async with db.begin_nested():
                if task_data["parent_task_id"]:
                    parent_result = await db.execute(
                        select(Task).where(
                            Task.id == task_data["parent_task_id"],
                            Task.project_id == project.id,
                            Task.is_deleted == False,  # noqa: E712
                        )
                    )
                    parent = parent_result.scalar_one_or_none()
                    if not parent:
                        raise InvalidOperationError(
                            f"Parent task {task_data['parent_task_id']} not found"
                        )
                        parent_ids_to_recalc.add(parent.id)

                calendar_id = task_data.get("calendar_id")
                if calendar_id is not None:
                    await calendar_service.ensure_project_or_global_calendar(
                        db,
                        calendar_id=calendar_id,
                        project_id=project.id,
                    )

                order_index = await get_next_order(task_data["parent_task_id"])
                finish_date = _compute_initial_finish_date(
                    start_date=task_data["start_date"],
                    duration_minutes=task_data["duration"],
                    is_milestone=task_data["is_milestone"],
                    minutes_per_day=minutes_per_day,
                )

                task = Task(
                    project_id=project.id,
                    parent_task_id=task_data["parent_task_id"],
                    name=task_data["name"],
                    notes=task_data["notes"],
                    wbs_code="TEMP",  # Will be fixed by regenerate_wbs_codes
                    outline_level=1,  # Will be fixed by regenerate_wbs_codes
                    order_index=order_index,
                    start_date=task_data["start_date"],
                    finish_date=finish_date,
                    duration=task_data["duration"],
                    actual_duration=0,
                    remaining_duration=task_data["duration"],
                    is_milestone=task_data["is_milestone"],
                    calendar_id=calendar_id,
                    task_type=task_data["task_type"],
                    effort_driven=task_data["effort_driven"],
                    constraint_type=task_data["constraint_type"],
                    constraint_date=task_data["constraint_date"],
                    deadline=task_data["deadline"],
                    priority=task_data["priority"],
                    fixed_cost=task_data["fixed_cost"],
                )
                sync_leaf_duration_progress(task)
                db.add(task)
                await db.flush()  # We need the ID
                if activity_context is not None:
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
                created_tasks.append(task)
        except Exception as e:
            pending = db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY)
            if pending is not None:
                del pending[pending_before:]
            errors.append({"index": idx, "message": str(e)})
            continue

    if created_tasks:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        await regenerate_wbs_codes(db, project.id)

        # Auto-recalculate schedule after bulk creation
        if project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

        await realtime_service.commit_and_publish(db)
        for t in created_tasks:
            await db.refresh(t)

    return created_tasks, errors


async def bulk_update_tasks(
    db: AsyncSession,
    project: Project,
    updates: list[TaskBulkUpdateInputItem],
    activity_context: ActivityContext | None = None,
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
    needs_schedule_recalc = False

    for idx, update_item in enumerate(updates):
        pending_before = len(
            db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY, [])
        )
        try:
            async with db.begin_nested():
                task_result = await db.execute(
                    select(Task).where(
                        Task.id == update_item["id"],
                        Task.project_id == project.id,
                        Task.is_deleted == False,  # noqa: E712
                    )
                )
                task = task_result.scalar_one_or_none()
                if not task:
                    raise InvalidOperationError(f"Task {update_item['id']} not found")

                # Store parents for recalculation before mutating
                if task.parent_task_id:
                    parent_ids_to_recalc.add(task.parent_task_id)

                update_data = dict(update_item["data"])
                before = {field: getattr(task, field) for field in update_data}

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

                if (
                    "calendar_id" in update_data
                    and update_data["calendar_id"] is not None
                ):
                    await calendar_service.ensure_project_or_global_calendar(
                        db,
                        calendar_id=update_data["calendar_id"],
                        project_id=project.id,
                    )

                if update_data.keys() & _SCHEDULE_FIELDS:
                    needs_schedule_recalc = True

                validate_summary_rollup_edit(task, update_data)

                for field, value in update_data.items():
                    setattr(task, field, value)
                if not task.is_summary:
                    sync_leaf_duration_progress(task)

                # Store the current parent if it just changed
                if task.parent_task_id:
                    parent_ids_to_recalc.add(task.parent_task_id)

                await db.flush()
                changes = activity_log_service.build_change_set(
                    before,
                    {field: getattr(task, field) for field in update_data},
                )
                if changes is not None and activity_context is not None:
                    await activity_log_service.log_activity(
                        db,
                        project_id=project.id,
                        action=AuditAction.UPDATED,
                        entity_type="task",
                        entity_id=task.id,
                        entity_name=task.name,
                        changes=changes,
                        context=activity_context,
                    )
                    realtime_service.queue_entity_event(
                        db,
                        project_id=project.id,
                        entity_type="task",
                        action=AuditAction.UPDATED,
                        entity_id=task.id,
                        entity_name=task.name,
                        context=activity_context,
                        metadata=changes,
                    )
                succeeded += 1
        except Exception as e:
            pending = db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY)
            if pending is not None:
                del pending[pending_before:]
            failed += 1
            errors.append(
                {"index": idx, "task_id": update_item["id"], "message": str(e)}
            )
            continue

    if succeeded > 0:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        if needs_wbs_regen:
            await regenerate_wbs_codes(db, project.id)

        if needs_schedule_recalc and project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

        await realtime_service.commit_and_publish(db)
    else:
        # If everything failed, rollback just in case
        await realtime_service.rollback_and_clear(db)

    return succeeded, failed, errors


async def bulk_delete_tasks(
    db: AsyncSession,
    project: Project,
    task_ids: list[UUID],
    activity_context: ActivityContext | None = None,
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
        pending_before = len(
            db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY, [])
        )
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
                await soft_delete_task(db, task, activity_context=activity_context)

                succeeded += 1
        except Exception as e:
            pending = db.info.get(realtime_service.PENDING_REALTIME_EVENTS_KEY)
            if pending is not None:
                del pending[pending_before:]
            failed += 1
            errors.append({"index": idx, "task_id": task_id, "message": str(e)})
            continue

    if succeeded > 0:
        for p_id in parent_ids_to_recalc:
            await recalculate_summary(db, project.id, p_id)

        await regenerate_wbs_codes(db, project.id)

        # Auto-recalculate schedule after bulk deletion
        if project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

        await realtime_service.commit_and_publish(db)
    else:
        await realtime_service.rollback_and_clear(db)

    return succeeded, failed, errors
