"""
Organization member endpoints.

GET    /organizations/{org_id}/members              - List members
POST   /organizations/{org_id}/members              - Invite a member
PATCH  /organizations/{org_id}/members/{member_id}  - Change member role
DELETE /organizations/{org_id}/members/{member_id}  - Remove a member
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_org_membership_or_404
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
    org_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Get my membership in the organization."""
    _org, membership = await get_org_membership_or_404(db, org_id, user)
    return OrgMemberListItem.model_validate(membership)


@router.get("", response_model=PaginatedResponse[OrgMemberListItem])
async def list_members(
    org_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """List all members of an organization."""
    org, _membership = await get_org_membership_or_404(db, org_id, user)

    members, total = await organization_member_service.list_members(
        db, org, page=page, per_page=per_page
    )
    return PaginatedResponse(
        items=[OrgMemberListItem(**m) for m in members],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=OrgMemberListItem,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    org_id: str,
    body: OrgMemberInvite,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Invite a user to the organization.

    Requires owner or admin role.
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    if membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Owner or admin role required")

    member = await organization_member_service.invite_member(db, org, body)
    return OrgMemberListItem(**member)


@router.patch("/{member_id}", response_model=OrgMemberListItem)
async def change_member_role(
    org_id: str,
    member_id: UUID,
    body: OrgMemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Change a member's role.

    Requires owner role.
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    member = await organization_member_service.change_member_role(
        db, org, member_id, body
    )
    return OrgMemberListItem(**member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: str,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Remove a member from the organization.

    Requires owner or admin role.
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    if membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Owner or admin role required")

    await organization_member_service.remove_member(db, org, member_id)
