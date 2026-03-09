"""
Organization access dependencies.
"""

from typing import Annotated, NamedTuple
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.user import User

from .auth import get_current_active_user


class OrgAccess(NamedTuple):
    """Result of organization access check."""

    organization: Organization
    membership: OrganizationMember
    role_name: str


async def get_org_membership_or_404(
    db: AsyncSession,
    org_id: UUID,
    user: User,
) -> tuple[Organization, OrganizationMember]:
    """
    Load an organization and verify the user is a member.

    Raises 404 if organization not found or deleted.
    Raises 403 if user is not a member.
    """
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_deleted.is_(False),
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization not found")

    member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    membership = member_result.scalar_one_or_none()
    if not membership:
        raise PermissionDeniedError("You do not have access to this organization")

    return org, membership


async def get_org_access_or_404(
    org_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> OrgAccess:
    """
    Load an organization and verify the user has access.
    Returns OrgAccess(organization, membership, role_name).
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    return OrgAccess(
        organization=org,
        membership=membership,
        role_name=membership.role,
    )


def check_org_role(access: OrgAccess, *allowed: str) -> None:
    """Raise 403 if user's organization role is not in allowed roles."""
    if access.role_name not in allowed:
        raise PermissionDeniedError(f"Requires role: {', '.join(allowed)}")
