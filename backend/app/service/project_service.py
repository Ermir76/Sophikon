"""
Project business logic.

Handles listing, creating, updating, and soft-deleting projects.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.schema.project import ProjectCreate, ProjectUpdate
from app.service import activity_log_service, realtime_service
from app.service.activity_log_service import ActivityContext


def escape_like(value: str) -> str:
    """
    Escape SQL LIKE wildcards to prevent pattern injection.

    Characters % and _ are wildcards in SQL LIKE patterns.
    This function escapes them so they're treated as literals.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
    """
    List projects the user owns or is a member of.

    When organization_id is provided, returns only projects within that
    organization. Caller must verify org membership before calling.
    Otherwise, returns all projects the user can see across orgs.

    Returns (projects, total_count).
    """
    if organization_id:
        # Scoped to a specific organization
        base_query = select(Project).where(
            Project.is_deleted.is_(False),
            Project.organization_id == organization_id,
        )
    else:
        # All projects the user owns OR is a member of
        base_query = (
            select(Project)
            .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                Project.is_deleted.is_(False),
                or_(
                    Project.owner_id == user.id,
                    ProjectMember.user_id == user.id,
                ),
            )
            .distinct()
        )

    # Apply filters
    if status:
        base_query = base_query.where(Project.status == status)

    if search:
        escaped_search = escape_like(search)
        base_query = base_query.where(
            Project.name.ilike(f"%{escaped_search}%", escape="\\")
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Project.updated_at.desc()).offset(offset).limit(per_page)
    )

    result = await db.execute(paginated_query)
    projects = list(result.scalars().all())

    return projects, total


async def create_project(
    db: AsyncSession,
    user: User,
    data: ProjectCreate,
    activity_context: ActivityContext | None = None,
) -> Project:
    """Create a new project owned by the user."""
    owner_role_result = await db.execute(
        select(Role).where(Role.scope == "project", Role.name == "owner")
    )
    owner_role = owner_role_result.scalar_one_or_none()
    if owner_role is None:
        owner_role = Role(
            name="owner",
            scope="project",
            description="Project owner with full access",
        )
        db.add(owner_role)
        await db.flush()

    project = Project(
        owner_id=user.id,
        organization_id=data.organization_id,
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        schedule_from=data.schedule_from,
        currency=data.currency,
        budget=data.budget,
        settings=data.settings or {},
        color=data.color,
    )
    db.add(project)

    # Keep owner_id for compatibility, but enforce owner-as-member invariant.
    await db.flush()
    db.add(
        ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role_id=owner_role.id,
        )
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
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def update_project(
    db: AsyncSession,
    project: Project,
    data: ProjectUpdate,
    activity_context: ActivityContext | None = None,
) -> Project:
    """Update a project with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    before = {field: getattr(project, field) for field in update_data}
    for field, value in update_data.items():
        setattr(project, field, value)

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(project, field) for field in update_data},
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
