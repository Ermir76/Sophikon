"""
Resource CRUD endpoints.

GET    /projects/{project_id}/resources                  - List project resources
POST   /projects/{project_id}/resources                  - Create a new resource
GET    /projects/{project_id}/resources/{resource_id}    - Get resource details
PATCH  /projects/{project_id}/resources/{resource_id}    - Update resource
DELETE /projects/{project_id}/resources/{resource_id}    - Delete resource (hard)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectAccess,
    check_role,
    get_current_active_user,
    get_project_or_404,
)
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.resource import ResourceCreate, ResourceResponse, ResourceUpdate
from app.service import activity_log_service, resource_service

router = APIRouter(prefix="/projects/{project_id}/resources", tags=["resources"])


@router.get("", response_model=PaginatedResponse[ResourceResponse])
async def list_resources(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=200)] = 50,
    type: Annotated[str | None, Query(alias="type")] = None,
    include_inactive: Annotated[bool, Query()] = False,
):
    """List all resources in the project."""
    resources, total = await resource_service.list_resources(
        db,
        access.project,
        page=page,
        per_page=per_page,
        resource_type=type,
        include_inactive=include_inactive,
    )
    return PaginatedResponse(
        items=[ResourceResponse.model_validate(r) for r in resources],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    body: ResourceCreate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Create a new resource in the project."""
    check_role(access, "owner", "manager", "member")
    resource = await resource_service.create_resource(
        db,
        access.project,
        body,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return ResourceResponse.model_validate(resource)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get resource details."""
    resource = await resource_service.get_resource_by_id(
        db, resource_id, access.project.id
    )
    if not resource:
        raise NotFoundError("Resource not found")
    return ResourceResponse.model_validate(resource)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: UUID,
    body: ResourceUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Update a resource."""
    check_role(access, "owner", "manager", "member")
    resource = await resource_service.get_resource_by_id(
        db, resource_id, access.project.id
    )
    if not resource:
        raise NotFoundError("Resource not found")

    resource = await resource_service.update_resource(
        db,
        resource,
        body,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return ResourceResponse.model_validate(resource)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Delete a resource (hard delete)."""
    check_role(access, "owner", "manager")
    resource = await resource_service.get_resource_by_id(
        db, resource_id, access.project.id
    )
    if not resource:
        raise NotFoundError("Resource not found")

    await resource_service.delete_resource(
        db,
        resource,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
