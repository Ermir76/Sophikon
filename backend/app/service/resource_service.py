"""
Resource business logic.

Handles listing, creating, updating, and deleting resources.
Note: Resources use hard delete (no soft delete columns on model).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction
from app.models.project import Project
from app.models.resource import Resource
from app.repository import resource_repo
from app.service import activity_log_service, calendar_service, realtime_service
from app.service.activity_log_service import ActivityContext
from app.service.contracts.resource import ResourceCreateInput, ResourcePatchInput


async def list_resources(
    db: AsyncSession,
    project: Project,
    *,
    page: int = 1,
    per_page: int = 50,
    resource_type: str | None = None,
    include_inactive: bool = False,
) -> tuple[list[Resource], int]:
    """
    List resources for a project.

    Returns (resources, total_count).
    """
    return await resource_repo.list_for_project(
        db,
        project_id=project.id,
        page=page,
        per_page=per_page,
        resource_type=resource_type,
        include_inactive=include_inactive,
    )


async def create_resource(
    db: AsyncSession,
    project: Project,
    payload: ResourceCreateInput,
    activity_context: ActivityContext | None = None,
) -> Resource:
    """Create a new resource in the project."""
    calendar_id = payload.get("calendar_id")
    if calendar_id is not None:
        await calendar_service.ensure_project_or_global_calendar(
            db,
            calendar_id=calendar_id,
            project_id=project.id,
        )

    resource = await resource_repo.create(
        db,
        project_id=project.id,
        payload=payload,
    )
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="resource",
        entity_id=resource.id,
        entity_name=resource.name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="resource",
        action=AuditAction.CREATED,
        entity_id=resource.id,
        entity_name=resource.name,
        context=activity_context,
    )
    await realtime_service.commit_and_publish(db)
    await db.refresh(resource)
    return resource


async def get_resource_by_id(
    db: AsyncSession,
    resource_id: UUID,
    project_id: UUID,
) -> Resource | None:
    """Get a resource by ID within a project."""
    return await resource_repo.get_by_id(
        db,
        resource_id=resource_id,
        project_id=project_id,
    )


async def update_resource(
    db: AsyncSession,
    resource: Resource,
    patch: ResourcePatchInput,
    activity_context: ActivityContext | None = None,
) -> Resource:
    """Update a resource with partial data."""
    if "calendar_id" in patch and patch["calendar_id"] is not None:
        await calendar_service.ensure_project_or_global_calendar(
            db,
            calendar_id=patch["calendar_id"],
            project_id=resource.project_id,
        )

    before = {field: getattr(resource, field) for field in patch}
    for field, value in patch.items():
        setattr(resource, field, value)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(resource, field) for field in patch},
    )
    if changes is not None:
        await activity_log_service.log_activity(
            db,
            project_id=resource.project_id,
            action=AuditAction.UPDATED,
            entity_type="resource",
            entity_id=resource.id,
            entity_name=resource.name,
            changes=changes,
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=resource.project_id,
            entity_type="resource",
            action=AuditAction.UPDATED,
            entity_id=resource.id,
            entity_name=resource.name,
            context=activity_context,
            metadata=changes,
        )

    await realtime_service.commit_and_publish(db)
    await db.refresh(resource)
    return resource


async def delete_resource(
    db: AsyncSession,
    resource: Resource,
    activity_context: ActivityContext | None = None,
) -> None:
    """Hard delete a resource."""
    await activity_log_service.log_activity(
        db,
        project_id=resource.project_id,
        action=AuditAction.DELETED,
        entity_type="resource",
        entity_id=resource.id,
        entity_name=resource.name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=resource.project_id,
        entity_type="resource",
        action=AuditAction.DELETED,
        entity_id=resource.id,
        entity_name=resource.name,
        context=activity_context,
    )
    await db.delete(resource)
    await realtime_service.commit_and_publish(db)
