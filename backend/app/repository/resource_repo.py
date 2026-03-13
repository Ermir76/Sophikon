"""
Resource repository helpers.
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource


async def list_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int,
    per_page: int,
    resource_type: str | None,
    include_inactive: bool,
) -> tuple[list[Resource], int]:
    base_query = select(Resource).where(Resource.project_id == project_id)

    if not include_inactive:
        base_query = base_query.where(Resource.is_active == True)  # noqa: E712

    if resource_type:
        base_query = base_query.where(Resource.type == resource_type)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        base_query.order_by(Resource.name.asc()).offset(offset).limit(per_page)
    )
    return list(result.scalars().all()), total


async def create(
    db: AsyncSession,
    *,
    project_id: UUID,
    payload: Mapping[str, Any],
) -> Resource:
    resource = Resource(
        project_id=project_id,
        name=payload["name"],
        type=payload["type"],
        initials=payload.get("initials"),
        email=payload.get("email"),
        material_label=payload.get("material_label"),
        max_units=payload["max_units"],
        calendar_id=payload.get("calendar_id"),
        group_name=payload.get("group_name"),
        code=payload.get("code"),
        is_generic=payload["is_generic"],
        standard_rate=payload["standard_rate"],
        overtime_rate=payload["overtime_rate"],
        cost_per_use=payload["cost_per_use"],
        accrue_at=payload["accrue_at"],
    )
    db.add(resource)
    await db.flush()
    return resource


async def get_by_id(
    db: AsyncSession,
    *,
    resource_id: UUID,
    project_id: UUID,
) -> Resource | None:
    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()
