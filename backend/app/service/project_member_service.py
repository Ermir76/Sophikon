"""
Project member and invitation business logic.
"""

import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InvalidOperationError,
    NotFoundError,
    PermissionDeniedError,
    ResourceConflictError,
)
from app.core.security import hash_token
from app.models.enums import AuditAction, NotificationType
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.repository import project_member_repo
from app.service import (
    activity_log_service,
    email_service,
    notification_service,
    realtime_service,
)
from app.service.activity_log_service import ActivityContext
from app.service.contracts.project_member import (
    ProjectInvitationAcceptInput,
    ProjectMemberInviteInput,
    ProjectMemberRolePatchInput,
    ProjectRoleName,
)

logger = logging.getLogger(__name__)

PROJECT_ROLE_NAMES: tuple[ProjectRoleName, ...] = (
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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _role_name(value: object) -> str:
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value)


def _coerce_project_role(value: object) -> ProjectRoleName:
    role_name = _role_name(value)
    if role_name not in PROJECT_ROLE_NAMES:
        raise InvalidOperationError("Unsupported project role")
    return cast(ProjectRoleName, role_name)


async def _get_project_role(db: AsyncSession, role_name: ProjectRoleName) -> Role:
    role = await project_member_repo.get_project_role(db, role_name=role_name)
    if role is None:
        role = await project_member_repo.create_project_role(
            db,
            role_name=role_name,
            description=PROJECT_ROLE_DESCRIPTIONS.get(role_name),
        )
    return role


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
    member = await project_member_repo.get_member_by_project_user(
        db,
        project_id=project.id,
        user_id=project.owner_id,
    )
    owner_role = await _get_project_role(db, "owner")

    if member is None:
        await project_member_repo.create_project_member(
            db,
            project_id=project.id,
            user_id=project.owner_id,
            role_id=owner_role.id,
        )
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
    rows, total = await project_member_repo.list_members_with_user_and_role(
        db,
        project_id=project.id,
        page=page,
        per_page=per_page,
    )
    members = [
        _serialize_member_row(member, role_name, email, full_name)
        for member, role_name, email, full_name in rows
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
    (
        rows,
        total,
    ) = await project_member_repo.list_pending_invitations_with_inviter_and_role(
        db,
        project_id=project.id,
        now=datetime.now(UTC),
        page=page,
        per_page=per_page,
    )
    items = [
        _serialize_invitation_row(inv, role_name, inviter_email, inviter_full_name)
        for inv, role_name, inviter_email, inviter_full_name in rows
    ]
    return items, total


async def invite_member(
    db: AsyncSession,
    project: Project,
    inviter: User,
    inviter_role_name: str,
    payload: ProjectMemberInviteInput,
    activity_context: ActivityContext | None = None,
) -> tuple[dict, str]:
    """Create a pending invitation and return (invitation_payload, raw_token)."""
    target_role = _coerce_project_role(payload["role"])
    if inviter_role_name == "manager" and target_role not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError("Managers can only invite member or viewer roles")

    role = await _get_project_role(db, target_role)
    normalized_email = _normalize_email(payload["email"])
    now = datetime.now(UTC)

    existing_user = await project_member_repo.get_user_by_email_case_insensitive(
        db,
        email=normalized_email,
    )
    if existing_user is not None:
        existing_member = await project_member_repo.get_member_by_project_user(
            db,
            project_id=project.id,
            user_id=existing_user.id,
        )
        if existing_member is not None:
            raise ResourceConflictError("User is already a member of this project")

    pending_invitation = await project_member_repo.get_pending_invitation_for_email(
        db,
        project_id=project.id,
        normalized_email=normalized_email,
        now=now,
    )
    if pending_invitation is not None:
        raise ResourceConflictError(
            "An active invitation already exists for this email"
        )

    raw_token = secrets.token_urlsafe(32)
    invitation = await project_member_repo.create_invitation(
        db,
        project_id=project.id,
        invited_by_id=inviter.id,
        role_id=role.id,
        email=normalized_email,
        token_hash=hash_token(raw_token),
        message=payload.get("message"),
        expires_at=now + timedelta(days=7),
    )

    should_create_notification = False
    if existing_user is not None and existing_user.id != inviter.id:
        org_member = await project_member_repo.get_organization_member(
            db,
            organization_id=project.organization_id,
            user_id=existing_user.id,
        )
        should_create_notification = org_member is not None

    if should_create_notification and existing_user is not None:
        inviter_name = inviter.full_name or inviter.email
        message = f"{inviter_name} invited you to {project.name} as {role.name}."
        if payload.get("message"):
            message = f"{message} Message: {payload['message']}"
        await notification_service.create_notification(
            db,
            user_id=existing_user.id,
            type=NotificationType.INVITATION_RECEIVED,
            title=f"Invited to {project.name}",
            message=message,
            entity_type="project_invitation",
            entity_id=invitation.id,
            actor_id=inviter.id,
        )

    entity_name = (
        existing_user.full_name or existing_user.email
        if existing_user is not None
        else normalized_email
    )
    await activity_log_service.log_activity(
        db,
        project_id=project.id,
        action=AuditAction.CREATED,
        entity_type="project_member",
        entity_id=invitation.id,
        entity_name=entity_name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project_member",
        action=AuditAction.CREATED,
        entity_id=invitation.id,
        entity_name=entity_name,
        context=activity_context,
        metadata={
            "subject_type": "invitation",
            "email": normalized_email,
            "role": role.name,
            "user_id": existing_user.id if existing_user is not None else None,
        },
    )
    await realtime_service.commit_and_publish(db)
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


async def _get_accept_invitation_row(
    db: AsyncSession,
    payload: ProjectInvitationAcceptInput,
) -> tuple[ProjectInvitation, UUID, UUID, bool, UUID, str] | None:
    token = payload.get("token")
    if token is not None:
        return await project_member_repo.get_invitation_with_project_and_role_by_token_hash(
            db,
            token_hash=hash_token(token),
        )

    invitation_id = payload.get("invitation_id")
    if invitation_id is None:
        return None

    invitation_uuid = (
        invitation_id if isinstance(invitation_id, UUID) else UUID(str(invitation_id))
    )
    return await project_member_repo.get_invitation_with_project_and_role_by_id(
        db,
        invitation_id=invitation_uuid,
    )


async def resend_invitation(
    db: AsyncSession,
    project: Project,
    invitation_id: UUID,
    actor_role_name: str,
    activity_context: ActivityContext | None = None,
) -> tuple[dict, str]:
    """Rotate invitation token and return refreshed invitation + new raw token."""
    row = await project_member_repo.get_invitation_with_role_and_inviter(
        db,
        project_id=project.id,
        invitation_id=invitation_id,
    )
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
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project_member",
        action=AuditAction.UPDATED,
        entity_id=invitation.id,
        entity_name=invitation.email,
        context=activity_context,
        metadata={
            "subject_type": "invitation",
            "email": invitation.email,
            "role": role_name,
        },
    )
    await realtime_service.commit_and_publish(db)
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
    activity_context: ActivityContext | None = None,
) -> None:
    """Revoke a pending invitation."""
    row = await project_member_repo.get_invitation_with_role_and_inviter(
        db,
        project_id=project.id,
        invitation_id=invitation_id,
    )
    if row is None:
        raise NotFoundError("Invitation not found")

    invitation, role_name, _, _ = row
    if invitation.accepted_at is not None:
        raise InvalidOperationError("Cannot revoke an accepted invitation")
    if invitation.is_revoked:
        return
    if actor_role_name == "manager" and role_name not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError(
            "Managers can only manage member/viewer invitations"
        )

    invitation.is_revoked = True
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project_member",
        action=AuditAction.DELETED,
        entity_id=invitation.id,
        entity_name=invitation.email,
        context=activity_context,
        metadata={
            "subject_type": "invitation",
            "email": invitation.email,
            "role": role_name,
        },
    )
    await realtime_service.commit_and_publish(db)


async def accept_invitation(
    db: AsyncSession,
    user: User,
    payload: ProjectInvitationAcceptInput,
    activity_context: ActivityContext | None = None,
) -> tuple[UUID, UUID]:
    """Accept a project invitation token."""
    row = await _get_accept_invitation_row(db, payload)
    if row is None:
        raise InvalidOperationError("Invalid or expired invitation")

    invitation, project_id, organization_id, project_is_deleted, role_id, role_name = (
        row
    )
    now = datetime.now(UTC)

    if invitation.is_revoked:
        raise InvalidOperationError("Invalid or expired invitation")
    if invitation.accepted_at is not None:
        raise InvalidOperationError("Invitation already accepted")
    if invitation.expires_at < now:
        raise InvalidOperationError("Invitation expired")
    if project_is_deleted:
        raise NotFoundError("Project not found")
    if _normalize_email(user.email) != _normalize_email(invitation.email):
        raise PermissionDeniedError("Invitation does not match the current user email")

    existing_member = await project_member_repo.get_member_by_project_user(
        db,
        project_id=project_id,
        user_id=user.id,
    )
    if existing_member is not None:
        raise ResourceConflictError("User is already a member of this project")

    org_member = await project_member_repo.get_organization_member(
        db,
        organization_id=organization_id,
        user_id=user.id,
    )
    if org_member is None:
        await project_member_repo.create_organization_member(
            db,
            organization_id=organization_id,
            user_id=user.id,
            role="member",
        )

    member = await project_member_repo.create_project_member(
        db,
        project_id=project_id,
        user_id=user.id,
        role_id=role_id,
    )
    invitation.accepted_at = now
    await notification_service.resolve_project_invitation_notifications(
        db,
        user_id=user.id,
        invitation_id=invitation.id,
    )
    await db.flush()
    realtime_service.queue_entity_event(
        db,
        project_id=project_id,
        entity_type="project_member",
        action=AuditAction.CREATED,
        entity_id=member.id,
        entity_name=user.full_name or user.email,
        context=activity_context,
        metadata={
            "subject_type": "member",
            "user_id": user.id,
            "role": role_name,
            "invitation_id": invitation.id,
        },
    )
    await realtime_service.commit_and_publish(db)
    await db.refresh(member)
    return project_id, member.id


async def change_role(
    db: AsyncSession,
    project: Project,
    member_id: UUID,
    patch: ProjectMemberRolePatchInput,
    activity_context: ActivityContext | None = None,
) -> dict:
    """Change an existing project member role."""
    row = await project_member_repo.get_member_with_role_and_user(
        db,
        project_id=project.id,
        member_id=member_id,
    )
    if row is None:
        raise NotFoundError("Member not found")

    member, current_role_name, email, full_name = row
    target_role_name = _coerce_project_role(patch["role"])
    target_role = await _get_project_role(db, target_role_name)

    if member.user_id == project.owner_id and target_role.name != "owner":
        raise InvalidOperationError("Cannot change the role of the project owner")

    if current_role_name == "owner" and target_role.name != "owner":
        owner_count = await project_member_repo.count_project_members_by_role(
            db,
            project_id=project.id,
            role_name="owner",
        )
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
        realtime_service.queue_entity_event(
            db,
            project_id=project.id,
            entity_type="project_member",
            action=AuditAction.UPDATED,
            entity_id=member.id,
            entity_name=full_name or email,
            context=activity_context,
            metadata={
                "subject_type": "member",
                "user_id": member.user_id,
                "role": target_role.name,
            },
        )
    await realtime_service.commit_and_publish(db)
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
    row = await project_member_repo.get_member_with_role_and_user(
        db,
        project_id=project.id,
        member_id=member_id,
    )
    if row is None:
        raise NotFoundError("Member not found")

    member, role_name, email, full_name = row

    if member.user_id == project.owner_id:
        raise InvalidOperationError("Cannot remove the project owner")
    if actor_role_name == "manager" and role_name not in MANAGER_MUTABLE_ROLES:
        raise PermissionDeniedError("Managers can only remove member/viewer roles")

    if role_name == "owner":
        owner_count = await project_member_repo.count_project_members_by_role(
            db,
            project_id=project.id,
            role_name="owner",
        )
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
    realtime_service.queue_entity_event(
        db,
        project_id=project.id,
        entity_type="project_member",
        action=AuditAction.DELETED,
        entity_id=member.id,
        entity_name=full_name or email,
        context=activity_context,
        metadata={
            "subject_type": "member",
            "user_id": member.user_id,
            "role": role_name,
        },
    )
    await db.delete(member)
    await realtime_service.commit_and_publish(db)


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
