"""
Project member and invitation business logic.
"""

import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InvalidOperationError,
    NotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from app.core.security import hash_token
from app.models.enums import AuditAction
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.schema.project_member import (
    ProjectInvitationAccept,
    ProjectMemberInvite,
    ProjectMemberRole,
    ProjectMemberRoleUpdate,
)
from app.service import activity_log_service, email_service
from app.service.activity_log_service import ActivityContext

logger = logging.getLogger(__name__)

PROJECT_ROLE_NAMES: tuple[ProjectMemberRole, ...] = (
    "owner",
    "manager",
    "member",
    "viewer",
)
MANAGER_MUTABLE_ROLES = frozenset({"member", "viewer"})
PROJECT_ROLE_DESCRIPTIONS = {
    "owner": "Project owner with full access",
    "manager": "Project manager",
    "member": "Project member",
    "viewer": "Project viewer",
}


async def _get_project_role(db: AsyncSession, role_name: ProjectMemberRole) -> Role:
    result = await db.execute(
        select(Role).where(Role.scope == "project", Role.name == role_name)
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(
            name=role_name,
            scope="project",
            description=PROJECT_ROLE_DESCRIPTIONS.get(role_name),
        )
        db.add(role)
        await db.flush()
    return role


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _serialize_member_row(
    member: ProjectMember,
    role_name: str,
    email: str | None,
    full_name: str | None,
) -> dict:
    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": role_name,
        "joined_at": member.joined_at,
        "updated_at": member.updated_at,
        "user_email": email,
        "user_full_name": full_name,
    }


def _serialize_invitation_row(
    invitation: ProjectInvitation,
    role_name: str,
    inviter_email: str | None,
    inviter_full_name: str | None,
) -> dict:
    return {
        "id": invitation.id,
        "project_id": invitation.project_id,
        "invited_by_id": invitation.invited_by_id,
        "role": role_name,
        "email": invitation.email,
        "message": invitation.message,
        "expires_at": invitation.expires_at,
        "accepted_at": invitation.accepted_at,
        "is_revoked": invitation.is_revoked,
        "created_at": invitation.created_at,
        "invited_by_email": inviter_email,
        "invited_by_full_name": inviter_full_name,
    }


async def ensure_owner_membership(
    db: AsyncSession,
    project: Project,
) -> None:
    """Ensure the project owner has an owner membership row."""
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == project.owner_id,
        )
    )
    member = existing.scalar_one_or_none()
    owner_role = await _get_project_role(db, "owner")

    if member is None:
        db.add(
            ProjectMember(
                project_id=project.id,
                user_id=project.owner_id,
                role_id=owner_role.id,
            )
        )
        await db.flush()
        return

    if member.role_id != owner_role.id:
        member.role_id = owner_role.id
        await db.flush()


async def list_members(
    db: AsyncSession,
    project: Project,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """List project members with user and role metadata."""
    await ensure_owner_membership(db, project)

    base_query = (
        select(ProjectMember, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectMember.role_id)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project.id)
    )

    count_query = select(func.count()).select_from(
        select(ProjectMember.id)
        .where(ProjectMember.project_id == project.id)
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        base_query.order_by(ProjectMember.joined_at.asc())
        .offset(offset)
        .limit(per_page)
    )

    members = [
        _serialize_member_row(member, role_name, email, full_name)
        for member, role_name, email, full_name in result.all()
    ]
    return members, total


async def list_pending_invitations(
    db: AsyncSession,
    project: Project,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """List pending invitations for a project."""
    now = datetime.now(UTC)
    pending_filter = (
        ProjectInvitation.project_id == project.id,
        ProjectInvitation.is_revoked.is_(False),
        ProjectInvitation.accepted_at.is_(None),
        ProjectInvitation.expires_at >= now,
    )

    base_query = (
        select(ProjectInvitation, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .join(User, User.id == ProjectInvitation.invited_by_id)
        .where(*pending_filter)
    )
    count_query = select(func.count()).select_from(
        select(ProjectInvitation.id).where(*pending_filter).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        base_query.order_by(ProjectInvitation.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    items = [
        _serialize_invitation_row(inv, role_name, inviter_email, inviter_full_name)
        for inv, role_name, inviter_email, inviter_full_name in result.all()
    ]
    return items, total


async def invite_member(
    db: AsyncSession,
    project: Project,
    inviter: User,
    inviter_role_name: str,
    data: ProjectMemberInvite,
    activity_context: ActivityContext | None = None,
) -> tuple[dict, str]:
    """Create a pending invitation and return (invitation_payload, raw_token)."""
    target_role = data.role
    if inviter_role_name == "manager" and target_role not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError("Managers can only invite member or viewer roles")

    role = await _get_project_role(db, target_role)
    normalized_email = _normalize_email(data.email)
    now = datetime.now(UTC)

    # Existing direct membership check
    existing_user_result = await db.execute(
        select(User).where(func.lower(User.email) == normalized_email)
    )
    existing_user = existing_user_result.scalar_one_or_none()
    if existing_user is not None:
        existing_member_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == existing_user.id,
            )
        )
        if existing_member_result.scalar_one_or_none() is not None:
            raise ResourceConflictError("User is already a member of this project")

    # Existing active invitation check
    pending_invitation_result = await db.execute(
        select(ProjectInvitation).where(
            ProjectInvitation.project_id == project.id,
            func.lower(ProjectInvitation.email) == normalized_email,
            ProjectInvitation.is_revoked.is_(False),
            ProjectInvitation.accepted_at.is_(None),
            ProjectInvitation.expires_at >= now,
        )
    )
    if pending_invitation_result.scalar_one_or_none() is not None:
        raise ResourceConflictError(
            "An active invitation already exists for this email"
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = ProjectInvitation(
        project_id=project.id,
        invited_by_id=inviter.id,
        role_id=role.id,
        email=normalized_email,
        token_hash=hash_token(raw_token),
        message=data.message,
        expires_at=now + timedelta(days=7),
        is_revoked=False,
    )
    db.add(invitation)
    await db.flush()
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="project_member",
        entity_id=invitation.id,
        entity_name=existing_user.full_name or existing_user.email
        if existing_user is not None
        else normalized_email,
        context=activity_context,
    )
    await db.commit()
    await db.refresh(invitation)

    return (
        _serialize_invitation_row(
            invitation,
            role.name,
            inviter.email,
            inviter.full_name,
        ),
        raw_token,
    )


async def resend_invitation(
    db: AsyncSession,
    project: Project,
    invitation_id: UUID,
    actor_role_name: str,
) -> tuple[dict, str]:
    """Rotate invitation token and return refreshed invitation + new raw token."""
    result = await db.execute(
        select(ProjectInvitation, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .join(User, User.id == ProjectInvitation.invited_by_id)
        .where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project.id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Invitation not found")

    invitation, role_name, inviter_email, inviter_full_name = row
    if invitation.is_revoked:
        raise InvalidOperationError("Cannot resend a revoked invitation")
    if invitation.accepted_at is not None:
        raise InvalidOperationError("Cannot resend an accepted invitation")
    if actor_role_name == "manager" and role_name not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError(
            "Managers can only manage member/viewer invitations"
        )

    raw_token = secrets.token_urlsafe(32)
    invitation.token_hash = hash_token(raw_token)
    invitation.expires_at = datetime.now(UTC) + timedelta(days=7)
    await db.commit()
    await db.refresh(invitation)

    return (
        _serialize_invitation_row(
            invitation,
            role_name,
            inviter_email,
            inviter_full_name,
        ),
        raw_token,
    )


async def revoke_invitation(
    db: AsyncSession,
    project: Project,
    invitation_id: UUID,
    actor_role_name: str,
) -> None:
    """Revoke a pending invitation."""
    result = await db.execute(
        select(ProjectInvitation, Role.name)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project.id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Invitation not found")

    invitation, role_name = row
    if invitation.accepted_at is not None:
        raise InvalidOperationError("Cannot revoke an accepted invitation")
    if invitation.is_revoked:
        return

    if actor_role_name == "manager" and role_name not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError(
            "Managers can only manage member/viewer invitations"
        )

    invitation.is_revoked = True
    await db.commit()


async def accept_invitation(
    db: AsyncSession,
    user: User,
    data: ProjectInvitationAccept,
) -> tuple[UUID, UUID]:
    """Accept a project invitation token."""
    result = await db.execute(
        select(ProjectInvitation, Project, Role)
        .join(Project, Project.id == ProjectInvitation.project_id)
        .join(Role, Role.id == ProjectInvitation.role_id)
        .where(ProjectInvitation.token_hash == hash_token(data.token))
    )
    row = result.one_or_none()
    if row is None:
        raise InvalidOperationError("Invalid or expired invitation token")

    invitation, project, role = row
    now = datetime.now(UTC)

    if invitation.is_revoked:
        raise InvalidOperationError("Invalid or expired invitation token")
    if invitation.accepted_at is not None:
        raise InvalidOperationError("Invitation already accepted")
    if invitation.expires_at < now:
        raise InvalidOperationError("Invitation expired")
    if project.is_deleted:
        raise NotFoundError("Project not found")
    if _normalize_email(user.email) != _normalize_email(invitation.email):
        raise PermissionDeniedError("Invitation does not match the current user email")

    existing_member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    )
    if existing_member_result.scalar_one_or_none() is not None:
        raise ResourceConflictError("User is already a member of this project")

    # Ensure organization membership exists.
    org_member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == project.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if org_member_result.scalar_one_or_none() is None:
        db.add(
            OrganizationMember(
                organization_id=project.organization_id,
                user_id=user.id,
                role="member",
            )
        )

    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role_id=role.id,
    )
    db.add(member)
    invitation.accepted_at = now
    await db.commit()
    await db.refresh(member)
    return project.id, member.id


async def change_role(
    db: AsyncSession,
    project: Project,
    member_id: UUID,
    data: ProjectMemberRoleUpdate,
    activity_context: ActivityContext | None = None,
) -> dict:
    """Change an existing project member role."""
    result = await db.execute(
        select(ProjectMember, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectMember.role_id)
        .join(User, User.id == ProjectMember.user_id)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project.id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Member not found")

    member, current_role_name, email, full_name = row
    target_role = await _get_project_role(db, data.role)

    if member.user_id == project.owner_id and target_role.name != "owner":
        raise InvalidOperationError("Cannot change the role of the project owner")

    if current_role_name == "owner" and target_role.name != "owner":
        owner_count_result = await db.execute(
            select(func.count())
            .select_from(ProjectMember)
            .join(Role, Role.id == ProjectMember.role_id)
            .where(
                ProjectMember.project_id == project.id,
                Role.name == "owner",
            )
        )
        owner_count = owner_count_result.scalar() or 0
        if owner_count <= 1:
            raise InvalidOperationError("Cannot demote the last owner")

    member.role_id = target_role.id
    changes = activity_log_service.build_change_set(
        {"role": current_role_name},
        {"role": target_role.name},
    )
    if changes is not None:
        await activity_log_service.log_activity(
            db,
            project_id=project.id,
            action=AuditAction.UPDATED,
            entity_type="project_member",
            entity_id=member.id,
            entity_name=full_name or email,
            changes=changes,
            context=activity_context,
        )
    await db.commit()
    await db.refresh(member)

    return _serialize_member_row(member, target_role.name, email, full_name)


async def remove_member(
    db: AsyncSession,
    project: Project,
    member_id: UUID,
    actor_role_name: str,
    activity_context: ActivityContext | None = None,
) -> None:
    """Remove a project member."""
    result = await db.execute(
        select(ProjectMember, Role.name, User.email, User.full_name)
        .join(Role, Role.id == ProjectMember.role_id)
        .join(User, User.id == ProjectMember.user_id)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project.id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Member not found")

    member, role_name, email, full_name = row

    if member.user_id == project.owner_id:
        raise InvalidOperationError("Cannot remove the project owner")
    if actor_role_name == "manager" and role_name not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError("Managers can only remove member/viewer roles")

    if role_name == "owner":
        owner_count_result = await db.execute(
            select(func.count())
            .select_from(ProjectMember)
            .join(Role, Role.id == ProjectMember.role_id)
            .where(
                ProjectMember.project_id == project.id,
                Role.name == "owner",
            )
        )
        owner_count = owner_count_result.scalar() or 0
        if owner_count <= 1:
            raise InvalidOperationError("Cannot remove the last owner")

    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.DELETED,
        entity_type="project_member",
        entity_id=member.id,
        entity_name=full_name or email,
        context=activity_context,
    )
    await db.delete(member)
    await db.commit()


async def send_project_invitation_email_with_retry(
    recipient_email: str,
    inviter_name: str,
    project_name: str,
    role_name: str,
    raw_token: str,
    max_attempts: int = 3,
) -> None:
    """Best-effort async invitation email with bounded retries."""
    accept_url = f"{settings.FRONTEND_URL}/project-invitations/accept?token={raw_token}"
    for attempt in range(1, max_attempts + 1):
        try:
            await email_service.send_project_invitation_email(
                email=recipient_email,
                inviter_name=inviter_name,
                project_name=project_name,
                role_name=role_name,
                accept_url=accept_url,
            )
            return
        except Exception:
            logger.warning(
                "Project invitation email attempt %s/%s failed",
                attempt,
                max_attempts,
                exc_info=True,
            )
            if attempt < max_attempts:
                await asyncio.sleep(2 ** (attempt - 1))

    logger.error("Project invitation email permanently failed for %s", recipient_email)
