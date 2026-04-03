"""
Utilization repository helpers.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.resource import Resource
from app.models.task import Task


async def get_assignments_in_range(
    db: AsyncSession,
    *,
    project_id: UUID,
    start_date: date,
    end_date: date,
    resource_id: UUID | None = None,
) -> list[Assignment]:
    query = (
        select(Assignment)
        .join(Task, Assignment.task_id == Task.id)
        .where(
            Task.project_id == project_id,
            Task.is_deleted == False,  # noqa: E712
            Assignment.start_date <= end_date,
            Assignment.finish_date >= start_date,
        )
        .options(selectinload(Assignment.task))
    )
    if resource_id is not None:
        query = query.where(Assignment.resource_id == resource_id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_active_resources_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[Resource]:
    result = await db.execute(
        select(Resource)
        .where(
            Resource.project_id == project_id,
            Resource.is_active == True,  # noqa: E712
        )
        .order_by(Resource.name.asc())
    )
    return list(result.scalars().all())


async def get_assignments_in_range_for_projects(
    db: AsyncSession,
    *,
    project_ids: list[UUID],
    start_date: date,
    end_date: date,
) -> list[Assignment]:
    if not project_ids:
        return []

    result = await db.execute(
        select(Assignment)
        .join(Task, Assignment.task_id == Task.id)
        .where(
            Task.project_id.in_(project_ids),
            Task.is_deleted == False,  # noqa: E712
            Assignment.start_date <= end_date,
            Assignment.finish_date >= start_date,
        )
    )
    return list(result.scalars().all())
