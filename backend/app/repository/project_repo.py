"""
Project repository helpers.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.role import Role


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_projects_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int,
    per_page: int,
    status: str | None,
    search: str | None,
    organization_id: UUID | None,
) -> tuple[list[Project], int]:
    if organization_id:
        base_query = select(Project).where(
            Project.is_deleted.is_(False),
            Project.organization_id == organization_id,
        )
    else:
        base_query = (
            select(Project)
            .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
            .where(
                Project.is_deleted.is_(False),
                or_(
                    Project.owner_id == user_id,
                    ProjectMember.user_id == user_id,
                ),
            )
            .distinct()
        )

    if status:
        base_query = base_query.where(Project.status == status)

    if search:
        escaped_search = _escape_like(search)
        base_query = base_query.where(
            Project.name.ilike(f"%{escaped_search}%", escape="\\")
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    paginated_query = (
        base_query.order_by(Project.updated_at.desc()).offset(offset).limit(per_page)
    )
    result = await db.execute(paginated_query)
    return list(result.scalars().all()), total


async def get_project_owner_role(db: AsyncSession) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.scope == "project", Role.name == "owner")
    )
    return result.scalar_one_or_none()


async def create_project_owner_role(db: AsyncSession) -> Role:
    role = Role(
        name="owner",
        scope="project",
        description="Project owner with full access",
    )
    db.add(role)
    await db.flush()
    return role


async def create_project(
    db: AsyncSession,
    *,
    owner_id: UUID,
    payload: dict[str, Any],
) -> Project:
    project = Project(
        owner_id=owner_id,
        organization_id=payload["organization_id"],
        name=payload["name"],
        description=payload.get("description"),
        start_date=payload["start_date"],
        schedule_from=payload.get("schedule_from"),
        currency=payload.get("currency"),
        budget=payload.get("budget"),
        settings=payload.get("settings") or {},
        color=payload.get("color"),
    )
    db.add(project)
    await db.flush()
    return project


async def add_project_member(
    db: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    role_id: UUID,
) -> None:
    db.add(
        ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_id=role_id,
        )
    )
    await db.flush()


async def get_project_by_id(
    db: AsyncSession,
    *,
    project_id: UUID,
    include_deleted: bool = False,
) -> Project | None:
    query = select(Project).where(Project.id == project_id)
    if not include_deleted:
        query = query.where(Project.is_deleted.is_(False))
    result = await db.execute(query)
    return result.scalar_one_or_none()
