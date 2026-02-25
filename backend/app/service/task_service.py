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

    # Set new parent
    task.parent_task_id = prev_sibling.id

    # Regenerate WBS
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

    await regenerate_wbs_codes(db, project.id)
    await db.commit()
    await db.refresh(task)

    return task
