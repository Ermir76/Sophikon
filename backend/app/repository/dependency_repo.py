"""
Dependency repository helpers.
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency import Dependency
from app.models.task import Task


async def list_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int,
    per_page: int,
) -> tuple[list[Dependency], int]:
    count_result = await db.execute(
        select(func.count())
        .select_from(Dependency)
        .where(Dependency.project_id == project_id)
    )
    total = int(count_result.scalar() or 0)

    result = await db.execute(
        select(Dependency)
        .where(Dependency.project_id == project_id)
        .order_by(Dependency.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return list(result.scalars().all()), total


async def get_active_task_in_project(
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


async def list_edges_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[tuple[UUID, UUID]]:
    result = await db.execute(
        select(Dependency.predecessor_id, Dependency.successor_id).where(
            Dependency.project_id == project_id
        )
    )
    return list(result.tuples().all())


async def create(
    db: AsyncSession,
    *,
    project_id: UUID,
    payload: Mapping[str, Any],
) -> Dependency:
    dependency = Dependency(
        project_id=project_id,
        predecessor_id=payload["predecessor_id"],
        successor_id=payload["successor_id"],
        type=payload["type"],
        lag=payload["lag"],
        lag_format=payload["lag_format"],
    )
    db.add(dependency)
    await db.flush()
    return dependency


async def get_by_id(
    db: AsyncSession,
    *,
    dependency_id: UUID,
    project_id: UUID,
) -> Dependency | None:
    result = await db.execute(
        select(Dependency).where(
            Dependency.id == dependency_id,
            Dependency.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def get_task_name(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> str | None:
    result = await db.execute(select(Task.name).where(Task.id == task_id))
    return result.scalar_one_or_none()
