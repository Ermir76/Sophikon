"""
Project CRUD and dashboard endpoints.

GET    /projects                        - List user's projects
POST   /projects                        - Create a new project
GET    /projects/{project_id}           - Get project details
GET    /projects/{project_id}/dashboard - Get project dashboard
PATCH  /projects/{project_id}           - Update project (owner/manager only)
DELETE /projects/{project_id}           - Soft delete project (owner only)
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectAccess,
    check_role,
    get_current_active_user,
    get_org_membership_or_404,
    get_project_or_404,
)
from app.api.v1.endpoints._insights_window import resolve_window_or_422
from app.core.database import get_db
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.insights import InsightsWindowPreset, ProjectDashboardResponse
from app.schema.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectUpdate,
)
from app.service import insights_service, project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectListItem])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    organization_id: Annotated[str | None, Query()] = None,
):
    """List all projects the user owns or is a member of."""
    # Verify org membership before listing (same pattern as create_project)
    if organization_id:
        await get_org_membership_or_404(db, organization_id, user)

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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a new project."""
    await get_org_membership_or_404(db, body.organization_id, user)
    project = await project_service.create_project(db, user, body)
    return ProjectDetail.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
):
    """Get project details."""
    return ProjectDetail.model_validate(access.project)


@router.get("/{project_id}/dashboard", response_model=ProjectDashboardResponse)
async def get_project_dashboard(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_preset: Annotated[InsightsWindowPreset, Query()] = "30d",
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
):
    """Get the dashboard summary for a project."""
    window_start, window_end = resolve_window_or_422(
        window_preset,
        start_date,
        end_date,
    )
    return await insights_service.get_project_dashboard(
        db,
        access.project,
        window_start,
        window_end,
    )


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
    body: ProjectUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Soft delete a project.

    Requires owner role.
    """
    check_role(access, "owner")

    await project_service.soft_delete_project(db, access.project)
