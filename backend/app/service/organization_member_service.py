"""
Organization member business logic.

Handles listing, inviting, removing, and changing roles of organization members.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidOperationError,
    NotFoundError,
    ResourceConflictError,
)
from app.models.organization import Organization
from app.repository import organization_member_repo
from app.service.contracts.organization_member import (
    OrganizationMemberInviteInput,
    OrganizationMemberRolePatchInput,
)


def _role_name(value: object) -> str:
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value)


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
    rows, total = await organization_member_repo.list_with_user_info(
        db,
        organization_id=org.id,
        page=page,
        per_page=per_page,
    )

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
    payload: OrganizationMemberInviteInput,
) -> dict:
    """Invite a user to an organization by email."""
    user = await organization_member_repo.get_user_by_email(
        db,
        email=payload["email"],
    )

    if not user:
        raise NotFoundError("User not found with this email")

    # Check if already a member
    existing = await organization_member_repo.get_member_by_org_user(
        db,
        organization_id=org.id,
        user_id=user.id,
    )
    if existing is not None:
        raise ResourceConflictError("User is already a member of this organization")

    member = await organization_member_repo.create_member(
        db,
        organization_id=org.id,
        user_id=user.id,
        role=_role_name(payload["role"]),
    )
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
    patch: OrganizationMemberRolePatchInput,
) -> dict:
    """Change a member's role in the organization."""
    row = await organization_member_repo.get_member_with_user_info(
        db,
        organization_id=org.id,
        member_id=member_id,
    )

    if not row:
        raise NotFoundError("Member not found")

    member, email, full_name = row

    # Prevent demoting the last owner
    next_role = _role_name(patch["role"])
    if member.role == "owner" and next_role != "owner":
        owner_count = await organization_member_repo.count_members_by_role(
            db,
            organization_id=org.id,
            role="owner",
        )
        if owner_count <= 1:
            raise InvalidOperationError("Cannot demote the last owner")

    member.role = next_role
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
    member = await organization_member_repo.get_member_by_id(
        db,
        organization_id=org.id,
        member_id=member_id,
    )

    if not member:
        raise NotFoundError("Member not found")

    # Prevent removing the last owner
    if member.role == "owner":
        owner_count = await organization_member_repo.count_members_by_role(
            db,
            organization_id=org.id,
            role="owner",
        )
        if owner_count <= 1:
            raise InvalidOperationError("Cannot remove the last owner")

    await db.delete(member)
    await db.commit()
