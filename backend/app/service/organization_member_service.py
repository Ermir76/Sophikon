"""
Organization member business logic.

Handles listing, inviting, removing, and changing roles of organization members.
"""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schema.organization_member import OrgMemberInvite, OrgMemberRoleUpdate


async def list_members(
    db: AsyncSession,
    org: Organization,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """
    List members of an organization with user info.

    Returns (members_with_user_info, total_count).
    """
    from sqlalchemy import func

    base_query = (
        select(OrganizationMember, User.email, User.full_name)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == org.id)
    )

    # Get total count
    count_query = select(func.count()).select_from(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == org.id)
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(OrganizationMember.joined_at.asc())
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(paginated_query)
    rows = result.all()

    members = []
    for member, email, full_name in rows:
        members.append(
            {
                "id": member.id,
                "organization_id": member.organization_id,
                "user_id": member.user_id,
                "role": member.role,
                "joined_at": member.joined_at,
                "updated_at": member.updated_at,
                "user_email": email,
                "user_full_name": full_name,
            }
        )

    return members, total


async def invite_member(
    db: AsyncSession,
    org: Organization,
    data: OrgMemberInvite,
) -> dict:
    """Invite a user to an organization by email."""
    # Find the user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found with this email",
        )

    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="User is already a member of this organization",
        )

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=data.role.value,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return {
        "id": member.id,
        "organization_id": member.organization_id,
        "user_id": member.user_id,
        "role": member.role,
        "joined_at": member.joined_at,
        "updated_at": member.updated_at,
        "user_email": user.email,
        "user_full_name": user.full_name,
    }


async def change_member_role(
    db: AsyncSession,
    org: Organization,
    member_id: UUID,
    data: OrgMemberRoleUpdate,
) -> dict:
    """Change a member's role in the organization."""
    result = await db.execute(
        select(OrganizationMember, User.email, User.full_name)
        .join(User, User.id == OrganizationMember.user_id)
        .where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org.id,
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    member, email, full_name = row

    # Prevent demoting the last owner
    if member.role == "owner" and data.role.value != "owner":
        owner_count = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.role == "owner",
            )
        )
        owners = owner_count.scalars().all()
        if len(owners) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last owner",
            )

    member.role = data.role.value
    await db.commit()
    await db.refresh(member)

    return {
        "id": member.id,
        "organization_id": member.organization_id,
        "user_id": member.user_id,
        "role": member.role,
        "joined_at": member.joined_at,
        "updated_at": member.updated_at,
        "user_email": email,
        "user_full_name": full_name,
    }


async def remove_member(
    db: AsyncSession,
    org: Organization,
    member_id: UUID,
) -> None:
    """Remove a member from an organization."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org.id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found",
        )

    # Prevent removing the last owner
    if member.role == "owner":
        owner_count = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.role == "owner",
            )
        )
        owners = owner_count.scalars().all()
        if len(owners) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last owner",
            )

    await db.delete(member)
    await db.commit()
