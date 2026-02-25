"""
Task hierarchy and sequence logic.

Handles indentation, outdentation, reordering, and WBS regeneration.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError
from app.models.project import Project
from app.models.task import Task
from app.service.task_service import recalculate_summary


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
