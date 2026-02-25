"""
Task business logic.

Handles listing, creating, updating, and soft-deleting tasks.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.assignment import Assignment
from app.models.dependency import Dependency
from app.models.project import Project
from app.models.task import Task
from app.schema.task import TaskBulkUpdateItem, TaskCreate, TaskUpdate


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
    await db.flush()
    if data.parent_task_id:
        await recalculate_summary(db, project.id, data.parent_task_id)

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

    # If parent changed, recalculate for both old and new parents
    # But update_task doesn't currently allow changing parent_task_id directly based on schema
    # Just recalculate the current parent
    await db.flush()
    if task.parent_task_id:
        # Need the project_id, which we don't have easily accessible in update_task params,
        # but we can get it from the task object.
        await recalculate_summary(db, task.project_id, task.parent_task_id)

    await db.commit()
    await db.refresh(task)
    return task


async def soft_delete_task(
    db: AsyncSession,
    task: Task,
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
    await db.flush()

    if task.parent_task_id:
        await recalculate_summary(db, task.project_id, task.parent_task_id)


async def regenerate_wbs_codes(db: AsyncSession, project_id: UUID) -> None:
    """
    Regenerate WBS codes, outline levels, and summary flags for all tasks in a project.
    Fixes orphaned tasks and flushes changes without committing.
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

    def traverse(node: Task, current_wbs_prefix: str, level: int) -> None:
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


async def indent_task(
    db: AsyncSession,
    project: Project,
    task: Task,
) -> Task:
    """
    Indent a task, making it a child of its immediate previous sibling.
    """
    # Lock the project row to serialize hierarchy mutations
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    parent_condition = (
        Task.parent_task_id.is_(None)
        if task.parent_task_id is None
        else Task.parent_task_id == task.parent_task_id
    )

    query = (
        select(Task)
        .where(
            Task.project_id == project.id,
            parent_condition,
            Task.order_index < task.order_index,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.desc())
        .limit(1)
    )

    result = await db.execute(query)
    prev_sibling = result.scalar_one_or_none()

    if not prev_sibling:
        raise InvalidOperationError("Cannot indent this task (no previous sibling).")

    old_parent_id = task.parent_task_id

    # Set new parent
    task.parent_task_id = prev_sibling.id

    # Regenerate WBS
    await db.flush()
    if old_parent_id:
        await recalculate_summary(db, project.id, old_parent_id)
    await recalculate_summary(db, project.id, task.parent_task_id)
    await regenerate_wbs_codes(db, project.id)

    await db.commit()
    await db.refresh(task)

    return task


async def outdent_task(
    db: AsyncSession,
    project: Project,
    task: Task,
) -> Task:
    """
    Outdent a task, moving it up one level in the hierarchy.
    """
    # Lock the project row
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    if task.parent_task_id is None:
        raise InvalidOperationError(
            "Task is already at the root level and cannot be outdented."
        )

    old_parent_id = task.parent_task_id

    parent_result = await db.execute(
        select(Task).where(
            Task.id == old_parent_id,
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    parent = parent_result.scalar_one_or_none()

    if parent:
        task.parent_task_id = parent.parent_task_id
    else:
        task.parent_task_id = None

    # Following siblings become children of THIS task
    following_siblings_result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.parent_task_id == old_parent_id,
            Task.order_index > task.order_index,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    following_siblings = list(following_siblings_result.scalars().all())

    for sibling in following_siblings:
        sibling.parent_task_id = task.id

    await db.flush()

    # Recalculate summaries for the old parent and the new parent (if any)
    if old_parent_id:
        await recalculate_summary(db, project.id, old_parent_id)
    if task.parent_task_id:
        await recalculate_summary(db, project.id, task.parent_task_id)
    # The outdented task itself might now be a summary task due to the following siblings
    await recalculate_summary(db, project.id, task.id)

    # Regenerate WBS
    await regenerate_wbs_codes(db, project.id)
    await db.commit()
    await db.refresh(task)

    return task


async def reorder_task(
    db: AsyncSession,
    project: Project,
    task: Task,
    after_task_id: UUID | None,
    before_task_id: UUID | None,
    new_parent_id: UUID | None,
) -> Task:
    """
    Reorder a task via drag-and-drop.
    Extracts the task and its descendants as a block and re-inserts it.
    """
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    if new_parent_id:
        parent_result = await db.execute(
            select(Task).where(
                Task.id == new_parent_id,
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise InvalidOperationError("New parent task not found")
        task.parent_task_id = parent.id

    # Load all tasks ordered by order_index
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.asc())
    )
    all_tasks = list(result.scalars().all())

    # Build hierarchy map to identify descendants
    children_map: dict[UUID, list[Task]] = {}
    for t in all_tasks:
        if t.parent_task_id:
            children_map.setdefault(t.parent_task_id, []).append(t)

    # Find the target task and all its descendants
    descendant_ids = set()

    def find_descendants(node_id: UUID):
        for child in children_map.get(node_id, []):
            descendant_ids.add(child.id)
            find_descendants(child.id)

    find_descendants(task.id)

    if new_parent_id and new_parent_id in descendant_ids:
        raise InvalidOperationError(
            "Cannot move a task to be a child of its descendant"
        )

    if new_parent_id == task.id:
        raise InvalidOperationError("Cannot make a task its own parent")

    # Extract the block of tasks being moved
    block = []
    remaining = []

    for t in all_tasks:
        if t.id == task.id or t.id in descendant_ids:
            block.append(t)
        else:
            remaining.append(t)

    insert_index = len(remaining)  # Default to end

    remaining_map = {t.id: t for t in remaining}

    # Helper to check if child is a descendant of parent
    def is_descendant(child_id: UUID, parent_id: UUID) -> bool:
        if child_id == parent_id:
            return True
        child_node = remaining_map.get(child_id)
        if not child_node or not child_node.parent_task_id:
            return False
        return is_descendant(child_node.parent_task_id, parent_id)

    if after_task_id:
        for i, t in enumerate(remaining):
            if t.id == after_task_id:
                insert_index = i + 1
                # Skip over the descendants of the after_task_id so
                # we don't insert the block right in the middle of them
                while insert_index < len(remaining):
                    if is_descendant(remaining[insert_index].id, after_task_id):
                        insert_index += 1
                    else:
                        break
                break
    elif before_task_id:
        for i, t in enumerate(remaining):
            if t.id == before_task_id:
                insert_index = i
                break

    # Reassemble the list
    new_order = remaining[:insert_index] + block + remaining[insert_index:]

    # Re-assign sequential order_index 1-based
    for idx, t in enumerate(new_order, start=1):
        t.order_index = idx

    await db.flush()

    # If the parent changed, we'd need to recalculate old and new parent summaries.
    # Since reorder_task can change parents, let's recalculate all parents involved.
    parents_to_recalc = {t.parent_task_id for t in all_tasks if t.parent_task_id}
    for p_id in parents_to_recalc:
        await recalculate_summary(db, project.id, p_id)

    await regenerate_wbs_codes(db, project.id)
    await db.commit()
    await db.refresh(task)

    return task


async def recalculate_summary(
    db: AsyncSession, project_id: UUID, parent_task_id: UUID | None
) -> None:
    """
    Recalculate summary task metrics based on its children, and recurse upwards.
    Called when a child task is mutated.
    """
    if parent_task_id is None:
        return

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
        parent.is_summary = False
        await db.flush()
        # Recurse up in case this parent is itself a child
        await recalculate_summary(db, project_id, parent.parent_task_id)
        return

    parent.is_summary = True
    parent.start_date = min(c.start_date for c in children)
    parent.finish_date = max(c.finish_date for c in children)

    # SUM fields
    parent.work = sum(c.work for c in children)
    parent.actual_work = sum(c.actual_work for c in children)
    parent.actual_cost = sum(c.actual_cost for c in children)
    parent.total_cost = sum(c.total_cost for c in children)

    # Weighted percent complete by duration
    total_duration = sum(c.duration for c in children)
    if total_duration > 0:
        weighted_pc = (
            sum(c.percent_complete * c.duration for c in children) / total_duration
        )
        parent.percent_complete = weighted_pc
    else:
        parent.percent_complete = Decimal(0)

    # actual_start = MIN (where not null)
    actual_starts = [c.actual_start for c in children if c.actual_start is not None]
    parent.actual_start = min(actual_starts) if actual_starts else None

    # actual_finish = MAX (only if ALL children have it)
    if all(c.actual_finish is not None for c in children):
        parent.actual_finish = max(c.actual_finish for c in children)  # type: ignore
    else:
        parent.actual_finish = None

    await db.flush()
    await recalculate_summary(db, project_id, parent.parent_task_id)


# ── Bulk Operations ──


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

    result = await db.execute(
        select(func.coalesce(func.max(Task.order_index), 0)).where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    max_order_index = result.scalar() or 0

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

                max_order_index += 1
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
                    order_index=max_order_index,
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
