"""
Comment repository helpers.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.comment import Comment
from app.models.dependency import Dependency
from app.models.enums import CommentEntityType
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User


async def get_project_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> tuple[UUID, str] | None:
    result = await db.execute(
        select(Project.id, Project.name).where(
            Project.id == entity_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    project_id, project_name = row
    return project_id, project_name


async def get_task_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> tuple[UUID, str] | None:
    result = await db.execute(
        select(Task.project_id, Task.name).where(
            Task.id == entity_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    project_id, task_name = row
    return project_id, task_name


async def get_resource_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> tuple[UUID, str] | None:
    result = await db.execute(
        select(Resource.project_id, Resource.name).where(Resource.id == entity_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    project_id, resource_name = row
    return project_id, resource_name


async def get_assignment_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> tuple[UUID, str] | None:
    result = await db.execute(
        select(Task.project_id, Task.name)
        .join(Assignment, Assignment.task_id == Task.id)
        .where(
            Assignment.id == entity_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    project_id, task_name = row
    return project_id, task_name


async def get_dependency_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> UUID | None:
    result = await db.execute(
        select(Dependency.project_id).where(Dependency.id == entity_id)
    )
    return result.scalar_one_or_none()


async def get_project_member_context(
    db: AsyncSession,
    *,
    entity_id: UUID,
) -> tuple[UUID, str | None] | None:
    result = await db.execute(
        select(ProjectMember.project_id, User.full_name)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.id == entity_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    project_id, full_name = row
    return project_id, full_name


async def list_active_for_entity_with_author(
    db: AsyncSession,
    *,
    entity_type: CommentEntityType,
    entity_id: UUID,
) -> list[Comment]:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.entity_type == entity_type,
            Comment.entity_id == entity_id,
            Comment.is_deleted == False,  # noqa: E712
        )
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


async def get_active_by_id_with_author(
    db: AsyncSession,
    *,
    comment_id: UUID,
) -> Comment | None:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.id == comment_id,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def get_parent_chain_row_for_update(
    db: AsyncSession,
    *,
    comment_id: UUID,
) -> tuple[UUID | None, CommentEntityType, UUID, bool] | None:
    result = await db.execute(
        select(
            Comment.parent_comment_id,
            Comment.entity_type,
            Comment.entity_id,
            Comment.is_deleted,
        )
        .where(Comment.id == comment_id)
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        return None
    parent_comment_id, entity_type, entity_id, is_deleted = row
    return parent_comment_id, entity_type, entity_id, is_deleted


async def list_active_for_entity_for_update(
    db: AsyncSession,
    *,
    entity_type: CommentEntityType,
    entity_id: UUID,
) -> list[Comment]:
    result = await db.execute(
        select(Comment)
        .where(
            Comment.entity_type == entity_type,
            Comment.entity_id == entity_id,
            Comment.is_deleted == False,  # noqa: E712
        )
        .with_for_update()
    )
    return list(result.scalars().all())


async def get_project_owner_id(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> UUID | None:
    result = await db.execute(
        select(Project.owner_id).where(
            Project.id == project_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def list_project_member_user_ids(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[UUID]:
    result = await db.execute(
        select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
    )
    return list(result.scalars().all())


async def get_project_name(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> str | None:
    result = await db.execute(select(Project.name).where(Project.id == project_id))
    return result.scalar_one_or_none()
