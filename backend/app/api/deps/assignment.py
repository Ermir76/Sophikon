"""
Assignment access dependencies.
"""

from typing import Annotated, NamedTuple
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.assignment import Assignment
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User

from .auth import get_current_active_user


class AssignmentAccess(NamedTuple):
    """Result of assignment access check."""

    assignment: Assignment
    project: Project
    role_name: str


async def get_assignment_with_access(
    assignment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
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
        raise NotFoundError("Assignment not found")

    task = assignment.task
    if task.is_deleted:
        raise NotFoundError("Assignment not found")

    project = task.project
    if project.is_deleted:
        raise NotFoundError("Assignment not found")

    if project.owner_id == user.id:
        return AssignmentAccess(
            assignment=assignment,
            project=project,
            role_name="owner",
        )

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

    return AssignmentAccess(
        assignment=assignment,
        project=project,
        role_name=member.role.name,
    )
