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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api.deps import get_current_active_user, get_project_or_404, ProjectAccess
from app.core.database import get_db
from app.models.assignment import Assignment
from app.models.task import Task
from app.models.user import User
from app.models.project_member import ProjectMember
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
    task = await _get_task_in_project(task_id, access, db)
    assignment = await assignment_service.create_assignment(db, task, body)
    return AssignmentResponse.model_validate(assignment)


# ── Flat Assignment Endpoints ──


async def _get_assignment_with_access(
    assignment_id: UUID,
    db: AsyncSession,
    user: User,
) -> Assignment:
    """Get assignment and verify user has access to its project."""
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.task).selectinload(Task.project))
        .where(Assignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    project = assignment.task.project

    # Check access
    if project.owner_id != user.id:
        member_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project",
            )

    return assignment


@assignments_router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    body: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Update an assignment."""
    assignment = await _get_assignment_with_access(assignment_id, db, user)
    assignment = await assignment_service.update_assignment(db, assignment, body)
    return AssignmentResponse.model_validate(assignment)


@assignments_router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Delete an assignment."""
    assignment = await _get_assignment_with_access(assignment_id, db, user)
    await assignment_service.delete_assignment(db, assignment)
