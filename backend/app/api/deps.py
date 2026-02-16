"""
FastAPI dependency injection for authentication.
"""

from typing import NamedTuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User
from app.service.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


# ── Organization Access Dependencies ──


async def get_org_membership_or_404(
    db: AsyncSession,
    org_id: UUID,
    user: User,
) -> tuple:
    """
    Load an organization and verify the user is a member.

    Returns (organization, membership).

    Raises 404 if organization not found or deleted.
    Raises 403 if user is not a member.
    """

    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.is_deleted.is_(False),
        )
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    membership = member_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization",
        )

    return org, membership


# ── Project Access Dependencies ──


class ProjectAccess(NamedTuple):
    """Result of project access check."""

    project: Project
    role_name: str


def check_role_name(role_name: str, *allowed: str) -> None:
    """Raise 403 if role_name is not in allowed roles."""
    if role_name not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role: {', '.join(allowed)}",
        )


def check_role(access: ProjectAccess, *allowed: str) -> None:
    """Raise 403 if user's project role is not in allowed roles."""
    check_role_name(access.role_name, *allowed)


async def get_project_or_404(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> ProjectAccess:
    """
    Load a project and verify the user has access.

    Returns ProjectAccess(project, role_name) where role_name is:
    - 'owner' if user owns the project
    - The project role name if user is a member

    Raises 404 if project not found or deleted.
    Raises 403 if user has no access.
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is owner
    if project.owner_id == user.id:
        return ProjectAccess(project=project, role_name="owner")

    # Check if user is a member
    member_result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.role))
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return ProjectAccess(project=project, role_name=member.role.name)


class TaskAccess(NamedTuple):
    """Result of task access check."""

    task: Task
    project: Project
    role_name: str


async def get_task_with_project_access(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> TaskAccess:
    """
    Load a task and verify the user has access to its project.

    Returns TaskAccess(task, project, role_name).

    Raises 404 if task not found or deleted.
    Raises 403 if user has no access to the task's project.
    """
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.project))
        .where(Task.id == task_id, Task.is_deleted.is_(False))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    project = task.project
    if project.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check if user is owner
    if project.owner_id == user.id:
        return TaskAccess(task=task, project=project, role_name="owner")

    # Check if user is a member
    member_result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.role))
        .where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return TaskAccess(task=task, project=project, role_name=member.role.name)


class AssignmentAccess(NamedTuple):
    """Result of assignment access check."""

    assignment: Assignment
    project: Project
    role_name: str


async def get_assignment_with_access(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> AssignmentAccess:
    """
    Load an assignment and verify the user has access to its project.

    Checks if assignment, task, or project are deleted.
    Returns AssignmentAccess(assignment, project, role_name).
    """
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

    task = assignment.task
    if task.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    project = task.project
    if project.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Check if user is owner
    if project.owner_id == user.id:
        return AssignmentAccess(
            assignment=assignment, project=project, role_name="owner"
        )

    # Check if user is a member
    member_result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.role))
        .where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return AssignmentAccess(
        assignment=assignment, project=project, role_name=member.role.name
    )
