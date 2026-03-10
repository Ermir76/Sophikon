"""
Insights repository helpers.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task


async def get_projects_for_organization(
    db: AsyncSession,
    *,
    organization_id: UUID,
) -> list[Project]:
    result = await db.execute(
        select(Project).where(
            Project.organization_id == organization_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def get_tasks_for_projects(
    db: AsyncSession,
    *,
    project_ids: list[UUID],
) -> list[Task]:
    if not project_ids:
        return []
    result = await db.execute(
        select(Task).where(
            Task.project_id.in_(project_ids),
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def get_resources_for_projects(
    db: AsyncSession,
    *,
    project_ids: list[UUID],
) -> list[Resource]:
    if not project_ids:
        return []
    result = await db.execute(
        select(Resource).where(Resource.project_id.in_(project_ids))
    )
    return list(result.scalars().all())


async def get_tasks_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[Task]:
    result = await db.execute(
        select(Task).where(
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def get_active_resources_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[Resource]:
    result = await db.execute(
        select(Resource).where(
            Resource.project_id == project_id,
            Resource.is_active == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())
