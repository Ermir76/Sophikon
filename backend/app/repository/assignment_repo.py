"""
Assignment repository helpers.
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.resource import Resource
from app.models.task import Task


async def list_for_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> list[Assignment]:
    result = await db.execute(
        select(Assignment)
        .where(Assignment.task_id == task_id)
        .order_by(Assignment.created_at.asc())
    )
    return list(result.scalars().all())


async def get_resource_in_project(
    db: AsyncSession,
    *,
    resource_id: UUID,
    project_id: UUID,
) -> Resource | None:
    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.project_id == project_id,
            Resource.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    task_id: UUID,
    payload: Mapping[str, Any],
) -> Assignment:
    assignment = Assignment(
        task_id=task_id,
        resource_id=payload["resource_id"],
        units=payload["units"],
        start_date=payload["start_date"],
        finish_date=payload["finish_date"],
        work=payload["work"],
        remaining_work=payload["work"],
        work_contour=payload["work_contour"],
        rate_table=payload["rate_table"],
    )
    db.add(assignment)
    await db.flush()
    return assignment


async def get_by_id(
    db: AsyncSession,
    *,
    assignment_id: UUID,
) -> Assignment | None:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    return result.scalar_one_or_none()


async def get_assignment_label_parts(
    db: AsyncSession,
    *,
    assignment: Assignment,
) -> tuple[str | None, str | None]:
    resource_result = await db.execute(
        select(Resource.name).where(Resource.id == assignment.resource_id)
    )
    resource_name = resource_result.scalar_one_or_none()
    task_result = await db.execute(
        select(Task.name).where(Task.id == assignment.task_id)
    )
    task_name = task_result.scalar_one_or_none()
    return resource_name, task_name


async def get_task_project_id(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> UUID | None:
    result = await db.execute(select(Task.project_id).where(Task.id == task_id))
    return result.scalar_one_or_none()
