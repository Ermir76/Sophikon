"""
Organization repository helpers.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int,
    per_page: int,
) -> tuple[list[Organization], int]:
    base_query = (
        select(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(
            Organization.is_deleted.is_(False),
            OrganizationMember.user_id == user_id,
        )
    )
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        base_query.order_by(Organization.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.scalars().all()), total


async def slug_exists(
    db: AsyncSession,
    *,
    slug: str,
    exclude_organization_id: UUID | None = None,
) -> bool:
    query = select(Organization.id).where(Organization.slug == slug)
    if exclude_organization_id is not None:
        query = query.where(Organization.id != exclude_organization_id)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def get_by_slug(
    db: AsyncSession,
    *,
    slug: str,
) -> Organization | None:
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    name: str,
    slug: str,
    is_personal: bool,
) -> Organization:
    organization = Organization(
        name=name,
        slug=slug,
        is_personal=is_personal,
    )
    db.add(organization)
    await db.flush()
    return organization


async def create_member(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    role: str,
) -> OrganizationMember:
    member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    await db.flush()
    return member


async def get_by_id(
    db: AsyncSession,
    *,
    organization_id: UUID,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()
