"""
Dependency CRUD endpoints.

GET    /projects/{project_id}/dependencies                    - List dependencies
POST   /projects/{project_id}/dependencies                    - Create dependency
PATCH  /projects/{project_id}/dependencies/{dependency_id}    - Update dependency
DELETE /projects/{project_id}/dependencies/{dependency_id}    - Delete dependency
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectAccess, get_project_or_404
from app.core.database import get_db
from app.schema.dependency import DependencyCreate, DependencyResponse, DependencyUpdate
from app.service import dependency_service

router = APIRouter(prefix="/projects/{project_id}/dependencies", tags=["dependencies"])


@router.get("", response_model=list[DependencyResponse])
async def list_dependencies(
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """List all dependencies in the project."""
    dependencies = await dependency_service.list_dependencies(db, access.project)
    return [DependencyResponse.model_validate(d) for d in dependencies]


@router.post(
    "",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dependency(
    body: DependencyCreate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Create a new dependency between tasks."""
    dependency = await dependency_service.create_dependency(db, access.project, body)
    return DependencyResponse.model_validate(dependency)


@router.patch("/{dependency_id}", response_model=DependencyResponse)
async def update_dependency(
    dependency_id: UUID,
    body: DependencyUpdate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Update a dependency."""
    dependency = await dependency_service.get_dependency_by_id(
        db, dependency_id, access.project.id
    )
    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    dependency = await dependency_service.update_dependency(db, dependency, body)
    return DependencyResponse.model_validate(dependency)


@router.delete("/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    dependency_id: UUID,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Delete a dependency."""
    dependency = await dependency_service.get_dependency_by_id(
        db, dependency_id, access.project.id
    )
    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )

    await dependency_service.delete_dependency(db, dependency)
