"""
Assignment CRUD endpoints.

Nested under tasks:
GET    /projects/{project_id}/tasks/{task_id}/assignments     - List assignments
POST   /projects/{project_id}/tasks/{task_id}/assignments     - Create assignment

Flat for update/delete:
PATCH  /assignments/{assignment_id}                           - Update assignment
DELETE /assignments/{assignment_id}                           - Delete assignment
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AssignmentAccess,
    ProjectAccess,
    check_role,
    check_role_name,
    get_assignment_with_access,
    get_project_or_404,
)
from app.core.database import get_db
from app.models.task import Task
from app.schema.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from app.service import assignment_service

# Router for nested task assignments (list/create)
task_assignments_router = APIRouter(
    prefix="/projects/{project_id}/tasks/{task_id}/assignments",
    tags=["assignments"],
)

# Router for flat assignment operations (update/delete)
assignments_router = APIRouter(prefix="/assignments", tags=["assignments"])


async def _get_task_in_project(
    task_id: UUID,
    access: ProjectAccess,
    db: AsyncSession,
) -> Task:
    """Get a task within the project context."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == access.project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@task_assignments_router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    task_id: UUID,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """List all assignments for a task."""
    task = await _get_task_in_project(task_id, access, db)
    assignments = await assignment_service.list_assignments_by_task(db, task)
    return [AssignmentResponse.model_validate(a) for a in assignments]


@task_assignments_router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    task_id: UUID,
    body: AssignmentCreate,
    access: ProjectAccess = Depends(get_project_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assignment for a task."""
    check_role(access, "owner", "manager", "member")
    task = await _get_task_in_project(task_id, access, db)
    assignment = await assignment_service.create_assignment(db, task, body)
    return AssignmentResponse.model_validate(assignment)


# ── Flat Assignment Endpoints ──


@assignments_router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    body: AssignmentUpdate,
    access: AssignmentAccess = Depends(get_assignment_with_access),
    db: AsyncSession = Depends(get_db),
):
    """Update an assignment."""
    check_role_name(access.role_name, "owner", "manager", "member")
    assignment = await assignment_service.update_assignment(db, access.assignment, body)
    return AssignmentResponse.model_validate(assignment)


@assignments_router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    access: AssignmentAccess = Depends(get_assignment_with_access),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assignment."""
    check_role_name(access.role_name, "owner", "manager")
    await assignment_service.delete_assignment(db, access.assignment)
