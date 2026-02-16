"""
Organization CRUD endpoints.

GET    /organizations              - List user's organizations
POST   /organizations              - Create a new organization
GET    /organizations/{org_id}     - Get organization details
PATCH  /organizations/{org_id}     - Update organization (owner only)
DELETE /organizations/{org_id}     - Soft delete organization (owner only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_org_membership_or_404
from app.core.database import get_db
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.organization import (
    OrganizationCreate,
    OrganizationDetail,
    OrganizationListItem,
    OrganizationUpdate,
)
from app.service import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=PaginatedResponse[OrganizationListItem])
async def list_organizations(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """List all organizations the user is a member of."""
    orgs, total = await organization_service.list_organizations(
        db, user, page=page, per_page=per_page
    )
    return PaginatedResponse(
        items=[OrganizationListItem.model_validate(o) for o in orgs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=OrganizationDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Create a new organization."""
    org = await organization_service.create_organization(db, user, body)
    return OrganizationDetail.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationDetail)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Get organization details."""
    org, _membership = await get_org_membership_or_404(db, org_id, user)
    return OrganizationDetail.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationDetail)
async def update_organization(
    org_id: UUID,
    body: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Update an organization.

    Requires owner role.
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    org = await organization_service.update_organization(db, org, body)
    return OrganizationDetail.model_validate(org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Soft delete an organization.

    Requires owner role.
    """
    org, membership = await get_org_membership_or_404(db, org_id, user)
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    await organization_service.soft_delete_organization(db, org)
