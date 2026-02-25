"""
Task hierarchy and sequence logic.

Handles indentation, outdentation, reordering, and WBS regeneration.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.project import Project
from app.models.task import Task
from app.service.task_service import recalculate_summary, regenerate_wbs_codes


async def _renumber_siblings(
    db: AsyncSession,
    project_id: UUID,
    parent_task_id: UUID | None,
) -> None:
    """
    Renumber order_index for all active siblings under parent_task_id.

    Uses negative-index trick to avoid unique constraint collisions:
    Phase 1: set all to negative values, flush
    Phase 2: set all to final positive values, flush
    """
    parent_condition = (
        Task.parent_task_id.is_(None)
        if parent_task_id is None
        else Task.parent_task_id == parent_task_id
    )
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
            parent_condition,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.asc())
    )
    siblings = list(result.scalars().all())

    if not siblings:
        return

    # Phase 1: negative indexes
    for i, t in enumerate(siblings):
        t.order_index = -(i + 1)
    await db.flush()

    # Phase 2: final positive indexes
    for i, t in enumerate(siblings):
        t.order_index = i + 1
    await db.flush()


async def _next_sibling_order(
    db: AsyncSession,
    project_id: UUID,
    parent_task_id: UUID | None,
) -> int:
    """Return the next available order_index in a sibling group."""
    parent_condition = (
        Task.parent_task_id.is_(None)
        if parent_task_id is None
        else Task.parent_task_id == parent_task_id
    )
    result = await db.execute(
        select(func.coalesce(func.max(Task.order_index), 0) + 1).where(
            Task.project_id == project_id,
            parent_condition,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar() or 1


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

    # Set new parent — temp negative index avoids unique constraint
    # collision when autoflush sees the new parent before order_index is updated
    task.order_index = -9999
    await db.flush()

    task.parent_task_id = prev_sibling.id
    task.order_index = await _next_sibling_order(db, project.id, prev_sibling.id)

    await db.flush()

    # Renumber old sibling group (gap left behind)
    await _renumber_siblings(db, project.id, old_parent_id)

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
    if not parent:
        raise InvalidOperationError("Parent task not found or has been deleted.")

    new_parent_id = parent.parent_task_id

    # Following siblings (under old parent) become children of THIS task
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

    # Move task to new parent — temp negative index avoids unique constraint
    # collision when autoflush sees the new parent before order_index is updated
    task.order_index = -9999
    await db.flush()

    task.parent_task_id = new_parent_id
    task.order_index = await _next_sibling_order(db, project.id, new_parent_id)

    await db.flush()

    # Renumber all affected sibling groups
    await _renumber_siblings(db, project.id, old_parent_id)
    await _renumber_siblings(db, project.id, new_parent_id)
    if following_siblings:
        await _renumber_siblings(db, project.id, task.id)

    # Recalculate summaries
    if old_parent_id:
        await recalculate_summary(db, project.id, old_parent_id)
    if new_parent_id:
        await recalculate_summary(db, project.id, new_parent_id)
    await recalculate_summary(db, project.id, task.id)

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
    Moves the task within its sibling group or to a new parent.
    """
    await db.execute(
        select(Project.id).where(Project.id == project.id).with_for_update()
    )

    old_parent_id = task.parent_task_id

    # Validate new parent BEFORE mutating anything
    if new_parent_id is not None:
        if new_parent_id == task.id:
            raise InvalidOperationError("Cannot make a task its own parent")

        parent_result = await db.execute(
            select(Task).where(
                Task.id == new_parent_id,
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        new_parent = parent_result.scalar_one_or_none()
        if not new_parent:
            raise InvalidOperationError("New parent task not found")

        # Check descendant constraint — build hierarchy map from DB state
        all_result = await db.execute(
            select(Task.id, Task.parent_task_id).where(
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        all_rows = all_result.all()
        parent_map = {row.id: row.parent_task_id for row in all_rows}

        children_map: dict[UUID, list[UUID]] = {}
        for tid, pid in parent_map.items():
            if pid is not None:
                children_map.setdefault(pid, []).append(tid)

        descendant_ids: set[UUID] = set()

        def find_descendants(node_id: UUID) -> None:
            for child_id in children_map.get(node_id, []):
                if child_id not in descendant_ids:
                    descendant_ids.add(child_id)
                    find_descendants(child_id)

        find_descendants(task.id)

        if new_parent_id in descendant_ids:
            raise InvalidOperationError(
                "Cannot move a task to be a child of its descendant"
            )

    # Determine target parent
    target_parent_id = new_parent_id if new_parent_id is not None else old_parent_id

    # Load siblings in target group (excluding the task being moved)
    target_parent_condition = (
        Task.parent_task_id.is_(None)
        if target_parent_id is None
        else Task.parent_task_id == target_parent_id
    )
    siblings_result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project.id,
            target_parent_condition,
            Task.id != task.id,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.asc())
    )
    siblings = list(siblings_result.scalars().all())

    # Determine insertion position
    insert_pos = len(siblings)  # Default: append to end

    if after_task_id:
        for i, s in enumerate(siblings):
            if s.id == after_task_id:
                insert_pos = i + 1
                break
    elif before_task_id:
        for i, s in enumerate(siblings):
            if s.id == before_task_id:
                insert_pos = i
                break

    # Insert task into the sibling list
    siblings.insert(insert_pos, task)

    # Set new parent
    task.parent_task_id = target_parent_id

    # Renumber: negative-index trick on the target group
    for i, t in enumerate(siblings):
        t.order_index = -(i + 1)
    await db.flush()

    for i, t in enumerate(siblings):
        t.order_index = i + 1
    await db.flush()

    # If parent changed, renumber old sibling group too
    if new_parent_id is not None and old_parent_id != target_parent_id:
        await _renumber_siblings(db, project.id, old_parent_id)

    # Recalculate summaries
    parents_to_recalc = set()
    if old_parent_id:
        parents_to_recalc.add(old_parent_id)
    if target_parent_id:
        parents_to_recalc.add(target_parent_id)
    for p_id in parents_to_recalc:
        await recalculate_summary(db, project.id, p_id)

    await regenerate_wbs_codes(db, project.id)
    await db.commit()
    await db.refresh(task)

    return task
