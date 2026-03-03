"""
Task hierarchy and ordering.

Helpers:
    _parent_condition       — Build WHERE clause for parent_task_id (handles NULL).
    _lock_project           — Lock project row to prevent concurrent changes.
    _load_siblings          — Get all tasks with the same parent, sorted by order.
    _apply_order_indexes    — Reassign order numbers (1, 2, 3…) to a task list.
    _renumber_siblings      — Reload siblings and fix their order numbers.
    _next_sibling_order     — Get the next order number for a new sibling.
    _find_insert_position   — Find where to insert a task after a given task.

Public:
    indent_task             — Move task one level deeper (under previous sibling).
    outdent_task            — Move task one level up (to grandparent level).
    reorder_task            — Move task to a new position (drag-and-drop).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.project import Project
from app.models.task import Task
from app.service import scheduling_service
from app.service.task_service import recalculate_summary, regenerate_wbs_codes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parent_condition(parent_task_id: UUID | None):
    """SQLAlchemy clause: ``parent_task_id IS NULL`` or ``== value``."""
    if parent_task_id is None:
        return Task.parent_task_id.is_(None)
    return Task.parent_task_id == parent_task_id


async def _lock_project(db: AsyncSession, project_id: UUID) -> None:
    """Acquire a row-level lock to serialize hierarchy mutations."""
    await db.execute(
        select(Project.id).where(Project.id == project_id).with_for_update()
    )


async def _load_siblings(
    db: AsyncSession,
    project_id: UUID,
    parent_task_id: UUID | None,
    *,
    exclude_id: UUID | None = None,
    extra_filters: list | None = None,
) -> list[Task]:
    """Load ordered, non-deleted sibling tasks under *parent_task_id*."""
    conditions = [
        Task.project_id == project_id,
        _parent_condition(parent_task_id),
        Task.is_deleted == False,  # noqa: E712
    ]
    if exclude_id is not None:
        conditions.append(Task.id != exclude_id)
    if extra_filters:
        conditions.extend(extra_filters)

    result = await db.execute(
        select(Task).where(*conditions).order_by(Task.order_index.asc())
    )
    return list(result.scalars().all())


async def _apply_order_indexes(db: AsyncSession, tasks: list[Task]) -> None:
    """
    Assign contiguous order_index values using the negative-index trick
    to avoid unique constraint collisions during flush.
    """
    if not tasks:
        return
    for i, t in enumerate(tasks):
        t.order_index = -(i + 1)
    await db.flush()
    for i, t in enumerate(tasks):
        t.order_index = i + 1
    await db.flush()


async def _renumber_siblings(
    db: AsyncSession,
    project_id: UUID,
    parent_task_id: UUID | None,
) -> None:
    """Reload and renumber all siblings under *parent_task_id*."""
    siblings = await _load_siblings(db, project_id, parent_task_id)
    await _apply_order_indexes(db, siblings)


async def _next_sibling_order(
    db: AsyncSession,
    project_id: UUID,
    parent_task_id: UUID | None,
) -> int:
    """Return the next available order_index in a sibling group."""
    result = await db.execute(
        select(func.coalesce(func.max(Task.order_index), 0) + 1).where(
            Task.project_id == project_id,
            _parent_condition(parent_task_id),
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar() or 1


def _find_insert_position(siblings: list[Task], target_id: UUID) -> int:
    """Return the index *after* *target_id* in *siblings*, or end if not found."""
    for i, s in enumerate(siblings):
        if s.id == target_id:
            return i + 1
    return len(siblings)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def indent_task(
    db: AsyncSession,
    project: Project,
    task: Task,
) -> Task:
    """Make a task a child of its immediate previous sibling."""
    await _lock_project(db, project.id)

    # Find the previous sibling at the same level
    prev_siblings = await _load_siblings(
        db,
        project.id,
        task.parent_task_id,
        extra_filters=[Task.order_index < task.order_index],
    )
    if not prev_siblings:
        raise InvalidOperationError("Cannot indent this task (no previous sibling).")
    prev_sibling = prev_siblings[-1]  # highest order_index below ours

    old_parent_id = task.parent_task_id

    # Temp negative index avoids unique constraint collision on autoflush
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

    if project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    await db.commit()
    await db.refresh(task)
    return task


async def outdent_task(
    db: AsyncSession,
    project: Project,
    task: Task,
) -> Task:
    """Move a task up one level in the hierarchy."""
    await _lock_project(db, project.id)

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

    # Batch all mutations inside no_autoflush to prevent premature flushes
    # that violate the unique order_index constraint.
    with db.no_autoflush:
        following_siblings = await _load_siblings(
            db,
            project.id,
            old_parent_id,
            extra_filters=[Task.order_index > task.order_index],
        )

        # Following siblings become children of THIS task
        for sibling in following_siblings:
            sibling.parent_task_id = task.id

        # Move task to new parent
        task.parent_task_id = new_parent_id
        task.order_index = -9999

        # Load new siblings (excluding task)
        siblings = await _load_siblings(
            db,
            project.id,
            new_parent_id,
            exclude_id=task.id,
        )

    # Insert right after the former parent
    insert_pos = _find_insert_position(siblings, parent.id)
    siblings.insert(insert_pos, task)
    await _apply_order_indexes(db, siblings)

    # Renumber old sibling group (gap left behind)
    await _renumber_siblings(db, project.id, old_parent_id)
    if following_siblings:
        await _renumber_siblings(db, project.id, task.id)

    # Recalculate summaries
    if old_parent_id:
        await recalculate_summary(db, project.id, old_parent_id)
    if new_parent_id:
        await recalculate_summary(db, project.id, new_parent_id)
    await recalculate_summary(db, project.id, task.id)

    await regenerate_wbs_codes(db, project.id)

    if project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

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
    """Move a task via drag-and-drop within or across parents."""
    await _lock_project(db, project.id)

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
        if not parent_result.scalar_one_or_none():
            raise InvalidOperationError("New parent task not found")

        # Check descendant constraint
        all_result = await db.execute(
            select(Task.id, Task.parent_task_id).where(
                Task.project_id == project.id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        children_map: dict[UUID, list[UUID]] = {}
        for row in all_result.all():
            if row.parent_task_id is not None:
                children_map.setdefault(row.parent_task_id, []).append(row.id)

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

    # Determine target parent and load siblings
    target_parent_id = new_parent_id if new_parent_id is not None else old_parent_id

    siblings = await _load_siblings(
        db,
        project.id,
        target_parent_id,
        exclude_id=task.id,
    )

    # Determine insertion position
    insert_pos = len(siblings)
    if after_task_id:
        insert_pos = _find_insert_position(siblings, after_task_id)
    elif before_task_id:
        for i, s in enumerate(siblings):
            if s.id == before_task_id:
                insert_pos = i
                break

    siblings.insert(insert_pos, task)
    task.parent_task_id = target_parent_id
    await _apply_order_indexes(db, siblings)

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

    if project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    await db.commit()
    await db.refresh(task)
    return task
