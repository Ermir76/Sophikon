"""
Organization member endpoints.

GET    /organizations/{org_id}/members              - List members
POST   /organizations/{org_id}/members              - Invite a member
PATCH  /organizations/{org_id}/members/{member_id}  - Change member role
DELETE /organizations/{org_id}/members/{member_id}  - Remove a member
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.organization import check_org_role, get_org_access_or_404
from app.core.database import get_db
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.organization_member import (
    OrgMemberInvite,
    OrgMemberListItem,
    OrgMemberRoleUpdate,
)
from app.service import organization_member_service

router = APIRouter(
    prefix="/organizations/{org_id}/members",
    tags=["organization-members"],
)


@router.get("/me", response_model=OrgMemberListItem)
async def get_my_membership(
    org_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """Get my membership in the organization."""
    access = await get_org_access_or_404(org_id, db, user)
    return OrgMemberListItem.model_validate(access.membership)


@router.get("", response_model=PaginatedResponse[OrgMemberListItem])
async def list_members(
    org_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List all members of an organization."""
    access = await get_org_access_or_404(org_id, db, user)

    members, total = await organization_member_service.list_members(
        db, access.organization, page=page, per_page=per_page
    )
    return PaginatedResponse(
        items=[OrgMemberListItem(**m) for m in members],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=OrgMemberListItem, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: UUID,
    body: OrgMemberInvite,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Invite a user to the organization.

    Requires owner or admin role.
    """
    access = await get_org_access_or_404(org_id, db, user)
    check_org_role(access, "owner", "admin")

    member = await organization_member_service.invite_member(
        db, access.organization, body
    )
    return OrgMemberListItem(**member)


@router.patch("/{member_id}", response_model=OrgMemberListItem)
async def change_member_role(
    org_id: UUID,
    member_id: UUID,
    body: OrgMemberRoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Change a member's role.

    Requires owner role.
    """
    access = await get_org_access_or_404(org_id, db, user)
    check_org_role(access, "owner")

    member = await organization_member_service.change_member_role(
        db, access.organization, member_id, body
    )
    return OrgMemberListItem(**member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Remove a member from the organization.

    Requires owner or admin role.
    """
    access = await get_org_access_or_404(org_id, db, user)
    check_org_role(access, "owner", "admin")

    await organization_member_service.remove_member(db, access.organization, member_id)
