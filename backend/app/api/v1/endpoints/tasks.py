"""
Task CRUD endpoints.

GET    /projects/{project_id}/tasks              - List project tasks
POST   /projects/{project_id}/tasks              - Create a new task
GET    /projects/{project_id}/tasks/{task_id}    - Get task details
PATCH  /projects/{project_id}/tasks/{task_id}    - Update task
DELETE /projects/{project_id}/tasks/{task_id}    - Soft delete task
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectAccess, check_role, get_project_or_404
from app.core.database import get_db
from app.schema.common import PaginatedResponse
from app.schema.task import TaskCreate, TaskResponse, TaskUpdate
from app.service import task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    include_deleted: bool = Query(default=False),
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks in the project."""
    if include_deleted:
        check_role(access, "owner", "manager")

    tasks, total = await task_service.list_tasks(
        db,
        access.project,
        page=page,
        per_page=per_page,
        include_deleted=include_deleted,
    )
    return PaginatedResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    body: TaskCreate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task in the project."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.create_task(db, access.project, body)
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Get task details."""
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = await task_service.update_task(db, task, body)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a task."""
    check_role(access, "owner", "manager")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    await task_service.soft_delete_task(db, task)
