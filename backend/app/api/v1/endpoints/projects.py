"""
Project CRUD endpoints.

GET    /projects              - List user's projects
POST   /projects              - Create a new project
GET    /projects/{project_id} - Get project details
PATCH  /projects/{project_id} - Update project (owner/manager only)
DELETE /projects/{project_id} - Soft delete project (owner only)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectAccess,
    check_role,
    get_current_active_user,
    get_project_or_404,
)
from app.core.database import get_db
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectUpdate,
)
from app.service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectListItem])
async def list_projects(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    organization_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """List all projects the user owns or is a member of."""
    projects, total = await project_service.list_projects(
        db,
        user,
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        organization_id=organization_id,
    )
    return PaginatedResponse(
        items=[ProjectListItem.model_validate(p) for p in projects],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=ProjectDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Create a new project."""
    project = await project_service.create_project(db, user, body)
    return ProjectDetail.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    access: ProjectAccess = Depends(get_project_or_404),
):
    """Get project details."""
    return ProjectDetail.model_validate(access.project)


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
    body: ProjectUpdate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a project.

    Requires owner or manager role.
    """
    check_role(access, "owner", "manager")

    project = await project_service.update_project(db, access.project, body)
    return ProjectDetail.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a project.

    Requires owner role.
    """
    check_role(access, "owner")

    await project_service.soft_delete_project(db, access.project)
