"""
Project business logic.

Handles listing, creating, updating, and soft-deleting projects.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction
from app.models.project import Project
from app.models.user import User
from app.repository import project_repo
from app.service import activity_log_service, realtime_service
from app.service.activity_log_service import ActivityContext


async def list_projects(
    db: AsyncSession,
    user: User,
    *,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    search: str | None = None,
    organization_id: UUID | None = None,
) -> tuple[list[Project], int]:
    return await project_repo.list_projects_for_user(
        db,
        user_id=user.id,
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        organization_id=organization_id,
    )


async def create_project(
    db: AsyncSession,
    user: User,
    payload: dict[str, Any],
    activity_context: ActivityContext | None = None,
) -> Project:
    """Create a new project owned by the user."""
    owner_role = await project_repo.get_project_owner_role(db)
    if owner_role is None:
        owner_role = await project_repo.create_project_owner_role(db)

    project = await project_repo.create_project(
        db,
        owner_id=user.id,
        payload=payload,
    )

    # Keep owner_id for compatibility, but enforce owner-as-member invariant.
    await project_repo.add_project_member(
        db,
        project_id=project.id,
        user_id=user.id,
        role_id=owner_role.id,
    )
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="project",
        entity_id=project.id,
        entity_name=project.name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project",
        action=AuditAction.CREATED,
        entity_id=project.id,
        entity_name=project.name,
        context=activity_context,
    )

    await realtime_service.commit_and_publish(db)
    await db.refresh(project)
    return project


async def get_project_by_id(
    db: AsyncSession,
    project_id: UUID,
) -> Project | None:
    """Get a project by ID (excludes deleted)."""
    return await project_repo.get_project_by_id(db, project_id=project_id)


async def update_project(
    db: AsyncSession,
    project: Project,
    patch: dict[str, Any],
    activity_context: ActivityContext | None = None,
) -> Project:
    """Update a project with partial data."""
    before = {field: getattr(project, field) for field in patch}
    for field, value in patch.items():
        setattr(project, field, value)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(project, field) for field in patch},
    )
    if changes is not None:
        await activity_log_service.log_activity(
            db,
            project_id=project.id,
            action=AuditAction.UPDATED,
            entity_type="project",
            entity_id=project.id,
            entity_name=project.name,
            changes=changes,
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=project.id,
            entity_type="project",
            action=AuditAction.UPDATED,
            entity_id=project.id,
            entity_name=project.name,
            context=activity_context,
            metadata=changes,
        )

    await realtime_service.commit_and_publish(db)
    await db.refresh(project)
    return project


async def soft_delete_project(
    db: AsyncSession,
    project: Project,
    activity_context: ActivityContext | None = None,
) -> None:
    """Soft delete a project."""
    project_name = project.name
    project.is_deleted = True
    project.deleted_at = datetime.now(UTC)
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.DELETED,
        entity_type="project",
        entity_id=project.id,
        entity_name=project_name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project",
        action=AuditAction.DELETED,
        entity_id=project.id,
        entity_name=project_name,
        context=activity_context,
    )
    await realtime_service.commit_and_publish(db)
