"""
Task repository helpers.
"""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.comment import Comment
from app.models.dependency import Dependency
from app.models.project import Project
from app.models.task import Task


async def list_tasks_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int,
    per_page: int,
    include_deleted: bool,
) -> tuple[list[Task], int]:
    base_query = select(Task).where(Task.project_id == project_id)
    if not include_deleted:
        base_query = base_query.where(Task.is_deleted == False)  # noqa: E712

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Task.sort_order.asc()).offset(offset).limit(per_page)
    )
    result = await db.execute(paginated_query)
    return list(result.scalars().all()), total


async def count_comments_for_tasks(
    db: AsyncSession,
    *,
    task_ids: list[UUID],
) -> dict[UUID, int]:
    if not task_ids:
        return {}
    result = await db.execute(
        select(Comment.entity_id, func.count(Comment.id))
        .where(
            Comment.entity_type == "task",
            Comment.entity_id.in_(task_ids),
            Comment.is_deleted == False,  # noqa: E712
        )
        .group_by(Comment.entity_id)
    )
    return {entity_id: count for entity_id, count in result.tuples().all()}


async def get_task_with_comment_count(
    db: AsyncSession,
    *,
    task_id: UUID,
    project_id: UUID,
) -> tuple[Task, int] | None:
    comment_count_subquery = (
        select(func.count(Comment.id))
        .where(
            Comment.entity_type == "task",
            Comment.entity_id == Task.id,
            Comment.is_deleted == False,  # noqa: E712
        )
        .correlate(Task)
        .scalar_subquery()
    )
    result = await db.execute(
        select(Task, comment_count_subquery.label("comments_count")).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    task, comments_count = row
    return task, int(comments_count or 0)


async def lock_project_row(db: AsyncSession, *, project_id: UUID) -> None:
    await db.execute(
        select(Project.id).where(Project.id == project_id).with_for_update()
    )


async def get_next_order_index(
    db: AsyncSession,
    *,
    project_id: UUID,
    parent_task_id: UUID | None,
) -> int:
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
    return int(result.scalar() or 1)


async def count_active_siblings(
    db: AsyncSession,
    *,
    project_id: UUID,
    parent_task_id: UUID,
) -> int:
    result = await db.execute(
        select(func.count()).where(
            Task.parent_task_id == parent_task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return int(result.scalar() or 0)


async def get_active_task(
    db: AsyncSession,
    *,
    task_id: UUID,
    project_id: UUID,
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def list_active_children(
    db: AsyncSession,
    *,
    parent_task_id: UUID,
) -> list[Task]:
    result = await db.execute(
        select(Task).where(
            Task.parent_task_id == parent_task_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def delete_assignments_for_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> None:
    await db.execute(delete(Assignment).where(Assignment.task_id == task_id))


async def delete_dependencies_for_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> None:
    await db.execute(
        delete(Dependency).where(
            (Dependency.predecessor_id == task_id)
            | (Dependency.successor_id == task_id)
        )
    )


async def list_active_task_comments(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> list[Comment]:
    result = await db.execute(
        select(Comment).where(
            Comment.entity_type == "task",
            Comment.entity_id == task_id,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def list_tasks_for_wbs_regen(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[Task]:
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
        .order_by(Task.order_index.asc())
    )
    return list(result.scalars().all())


async def get_project_by_id(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> Project | None:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def get_task_for_rollup(
    db: AsyncSession,
    *,
    task_id: UUID,
    project_id: UUID,
) -> Task | None:
    return await get_active_task(db, task_id=task_id, project_id=project_id)


async def list_children_for_rollup(
    db: AsyncSession,
    *,
    parent_task_id: UUID,
    project_id: UUID,
) -> list[Task]:
    result = await db.execute(
        select(Task).where(
            Task.parent_task_id == parent_task_id,
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())
