"""
Project and task access dependencies.
"""

from typing import Annotated, NamedTuple
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User

from .auth import get_current_active_user


class ProjectAccess(NamedTuple):
    """Result of project access check."""

    project: Project
    role_name: str


def check_role_name(role_name: str, *allowed: str) -> None:
    """Raise 403 if role_name is not in allowed roles."""
    if role_name not in allowed:
        raise PermissionDeniedError(f"Requires role: {', '.join(allowed)}")


def check_role(access: ProjectAccess, *allowed: str) -> None:
    """Raise 403 if user's project role is not in allowed roles."""
    check_role_name(access.role_name, *allowed)


async def get_project_or_404(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> ProjectAccess:
    """
    Load a project and verify the user has access.

    Returns ProjectAccess(project, role_name) where role_name is:
    - 'owner' if user owns the project
    - The project role name if user is a member

    Raises 404 if project not found or deleted.
    Raises 403 if user has no access.
    """
    return await get_project_membership_for_user(db, project_id, user)


async def get_project_membership_for_user(
    db: AsyncSession,
    project_id: UUID,
    user: User,
) -> ProjectAccess:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found")

    if project.owner_id == user.id:
        return ProjectAccess(project=project, role_name="owner")

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
        raise PermissionDeniedError("You do not have access to this project")
    return ProjectAccess(project=project, role_name=member.role.name)


class TaskAccess(NamedTuple):
    """Result of task access check."""

    task: Task
    project: Project
    role_name: str


async def get_task_with_project_access(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
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
        raise NotFoundError("Task not found")

    project = task.project
    if project.is_deleted:
        raise NotFoundError("Task not found")

    if project.owner_id == user.id:
        return TaskAccess(task=task, project=project, role_name="owner")

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
        raise PermissionDeniedError("You do not have access to this project")

    return TaskAccess(task=task, project=project, role_name=member.role.name)
