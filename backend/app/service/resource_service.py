"""
Resource business logic.

Handles listing, creating, updating, and deleting resources.
Note: Resources use hard delete (no soft delete columns on model).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction
from app.models.project import Project
from app.models.resource import Resource
from app.schema.resource import ResourceCreate, ResourceUpdate
from app.service import activity_log_service
from app.service.activity_log_service import ActivityContext


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
    base_query = select(Resource).where(Resource.project_id == project.id)

    if not include_inactive:
        base_query = base_query.where(Resource.is_active == True)  # noqa: E712

    if resource_type:
        base_query = base_query.where(Resource.type == resource_type)

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Resource.name.asc()).offset(offset).limit(per_page)
    )

    result = await db.execute(paginated_query)
    resources = list(result.scalars().all())

    return resources, total


async def create_resource(
    db: AsyncSession,
    project: Project,
    data: ResourceCreate,
    activity_context: ActivityContext | None = None,
) -> Resource:
    """Create a new resource in the project."""
    resource = Resource(
        project_id=project.id,
        name=data.name,
        type=data.type,
        initials=data.initials,
        email=data.email,
        material_label=data.material_label,
        max_units=data.max_units,
        group_name=data.group_name,
        code=data.code,
        is_generic=data.is_generic,
        standard_rate=data.standard_rate,
        overtime_rate=data.overtime_rate,
        cost_per_use=data.cost_per_use,
        accrue_at=data.accrue_at,
    )
    db.add(resource)
    await db.flush()
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="resource",
        entity_id=resource.id,
        entity_name=resource.name,
        context=activity_context,
    )
    await db.commit()
    await db.refresh(resource)
    return resource


async def get_resource_by_id(
    db: AsyncSession,
    resource_id: UUID,
    project_id: UUID,
) -> Resource | None:
    """Get a resource by ID within a project."""
    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def update_resource(
    db: AsyncSession,
    resource: Resource,
    data: ResourceUpdate,
    activity_context: ActivityContext | None = None,
) -> Resource:
    """Update a resource with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    before = {field: getattr(resource, field) for field in update_data}
    for field, value in update_data.items():
        setattr(resource, field, value)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(resource, field) for field in update_data},
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

    await db.commit()
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
    await db.delete(resource)
    await db.commit()
