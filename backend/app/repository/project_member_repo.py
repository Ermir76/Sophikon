"""
Project membership and invitation repository helpers.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_member import OrganizationMember
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User


async def get_project_role(
    db: AsyncSession,
    *,
    role_name: str,
) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.scope == "project", Role.name == role_name)
    )
    return result.scalar_one_or_none()


async def create_project_role(
    db: AsyncSession,
    *,
    role_name: str,
    description: str | None,
) -> Role:
    role = Role(
        name=role_name,
        scope="project",
        description=description,
    )
    db.add(role)
    await db.flush()
    return role


async def get_member_by_project_user(
    db: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_project_member(
    db: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    role_id: UUID,
) -> ProjectMember:
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role_id=role_id,
    )
    db.add(member)
    await db.flush()
    return member


async def list_members_with_user_and_role(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int,
    per_page: int,
) -> tuple[list[tuple[ProjectMember, str, str | None, str | None]], int]:
    count_result = await db.execute(
        select(func.count())
        .select_from(ProjectMember)
        .where(ProjectMember.project_id == project_id)
    )
    total = int(count_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        select(ProjectMember, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectMember.role_id)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at.asc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.all()), total


async def list_pending_invitations_with_inviter_and_role(
    db: AsyncSession,
    *,
    project_id: UUID,
    now: datetime,
    page: int,
    per_page: int,
) -> tuple[list[tuple[ProjectInvitation, str, str | None, str | None]], int]:
    pending_filter = (
        ProjectInvitation.project_id == project_id,
        ProjectInvitation.is_revoked.is_(False),
        ProjectInvitation.accepted_at.is_(None),
        ProjectInvitation.expires_at >= now,
    )

    count_result = await db.execute(
        select(func.count()).select_from(ProjectInvitation).where(*pending_filter)
    )
    total = int(count_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        select(ProjectInvitation, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .join(User, User.id == ProjectInvitation.invited_by_id)
        .where(*pending_filter)
        .order_by(ProjectInvitation.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.all()), total


async def get_user_by_email_case_insensitive(
    db: AsyncSession,
    *,
    email: str,
) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    return result.scalar_one_or_none()


async def get_pending_invitation_for_email(
    db: AsyncSession,
    *,
    project_id: UUID,
    normalized_email: str,
    now: datetime,
) -> ProjectInvitation | None:
    result = await db.execute(
        select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            func.lower(ProjectInvitation.email) == normalized_email,
            ProjectInvitation.is_revoked.is_(False),
            ProjectInvitation.accepted_at.is_(None),
            ProjectInvitation.expires_at >= now,
        )
    )
    return result.scalar_one_or_none()


async def create_invitation(
    db: AsyncSession,
    *,
    project_id: UUID,
    invited_by_id: UUID,
    role_id: UUID,
    email: str,
    token_hash: str,
    message: str | None,
    expires_at: datetime,
) -> ProjectInvitation:
    invitation = ProjectInvitation(
        project_id=project_id,
        invited_by_id=invited_by_id,
        role_id=role_id,
        email=email,
        token_hash=token_hash,
        message=message,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(invitation)
    await db.flush()
    return invitation


async def get_invitation_with_role_and_inviter(
    db: AsyncSession,
    *,
    project_id: UUID,
    invitation_id: UUID,
) -> tuple[ProjectInvitation, str, str | None, str | None] | None:
    result = await db.execute(
        select(ProjectInvitation, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .join(User, User.id == ProjectInvitation.invited_by_id)
        .where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    invitation, role_name, inviter_email, inviter_full_name = row
    return invitation, role_name, inviter_email, inviter_full_name


async def get_invitation_with_project_and_role_by_token_hash(
    db: AsyncSession,
    *,
    token_hash: str,
) -> tuple[ProjectInvitation, UUID, UUID, bool, UUID, str] | None:
    from app.models.project import Project

    result = await db.execute(
        select(
            ProjectInvitation,
            Project.id,
            Project.organization_id,
            Project.is_deleted,
            Role.id,
            Role.name,
        )
        .join(Project, Project.id == ProjectInvitation.project_id)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .where(ProjectInvitation.token_hash == token_hash)
    )
    row = result.one_or_none()
    if row is None:
        return None
    invitation, project_id, organization_id, project_is_deleted, role_id, role_name = (
        row
    )
    return (
        invitation,
        project_id,
        organization_id,
        project_is_deleted,
        role_id,
        role_name,
    )


async def get_organization_member(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> OrganizationMember | None:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_organization_member(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID,
    role: str,
) -> OrganizationMember:
    member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    await db.flush()
    return member


async def get_member_with_role_and_user(
    db: AsyncSession,
    *,
    project_id: UUID,
    member_id: UUID,
) -> tuple[ProjectMember, str, str | None, str | None] | None:
    result = await db.execute(
        select(ProjectMember, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectMember.role_id)
        .join(User, User.id == ProjectMember.user_id)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    member, role_name, email, full_name = row
    return member, role_name, email, full_name


async def count_project_members_by_role(
    db: AsyncSession,
    *,
    project_id: UUID,
    role_name: str,
) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(ProjectMember)
        .join(Role, Role.id == ProjectMember.role_id)
        .where(
            ProjectMember.project_id == project_id,
            Role.name == role_name,
        )
    )
    return int(result.scalar() or 0)
