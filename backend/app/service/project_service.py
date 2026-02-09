"""
Project business logic.

Handles listing, creating, updating, and soft-deleting projects.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schema.project import ProjectCreate, ProjectUpdate


async def list_projects(
    db: AsyncSession,
    user: User,
    *,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[Project], int]:
    """
    List projects the user owns or is a member of.

    Returns (projects, total_count).
    """
    # Base query: projects user owns OR is a member of
    base_query = (
        select(Project)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .where(
            Project.is_deleted == False,  # TODO:Check this later
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
        base_query = base_query.where(Project.name.ilike(f"%{search}%"))

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
) -> Project:
    """Create a new project owned by the user."""
    project = Project(
        owner_id=user.id,
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        schedule_from=data.schedule_from,
        currency=data.currency,
        budget=data.budget,
        settings=data.settings or {},
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_id(
    db: AsyncSession,
    project_id: UUID,
) -> Project | None:
    """Get a project by ID (excludes deleted)."""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.is_deleted == False
        )  # TODO:Check this later
    )
    return result.scalar_one_or_none()


async def update_project(
    db: AsyncSession,
    project: Project,
    data: ProjectUpdate,
) -> Project:
    """Update a project with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


async def soft_delete_project(
    db: AsyncSession,
    project: Project,
) -> None:
    """Soft delete a project."""
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    await db.commit()
