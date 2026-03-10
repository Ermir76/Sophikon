"""
Organization member repository helpers.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_member import OrganizationMember
from app.models.user import User


async def list_with_user_info(
    db: AsyncSession,
    *,
    organization_id: UUID,
    page: int,
    per_page: int,
) -> tuple[list[tuple[OrganizationMember, str | None, str | None]], int]:
    total_result = await db.execute(
        select(func.count())
        .select_from(OrganizationMember)
        .where(OrganizationMember.organization_id == organization_id)
    )
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        select(OrganizationMember, User.email, User.full_name)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == organization_id)
        .order_by(OrganizationMember.joined_at.asc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.all()), total


async def get_user_by_email(
    db: AsyncSession,
    *,
    email: str,
) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_member_by_org_user(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> OrganizationMember | None:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


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


async def get_member_with_user_info(
    db: AsyncSession,
    *,
    organization_id: UUID,
    member_id: UUID,
) -> tuple[OrganizationMember, str | None, str | None] | None:
    result = await db.execute(
        select(OrganizationMember, User.email, User.full_name)
        .join(User, User.id == OrganizationMember.user_id)
        .where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    member, email, full_name = row
    return member, email, full_name


async def count_members_by_role(
    db: AsyncSession,
    *,
    organization_id: UUID,
    role: str,
) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(OrganizationMember)
        .where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.role == role,
        )
    )
    return int(result.scalar() or 0)


async def get_member_by_id(
    db: AsyncSession,
    *,
    organization_id: UUID,
    member_id: UUID,
) -> OrganizationMember | None:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()
