"""
Project member and invitation endpoints.

GET    /projects/{project_id}/members                                - List members
POST   /projects/{project_id}/members/invite                         - Create invitation
GET    /projects/{project_id}/members/invitations                    - List pending invitations
POST   /projects/{project_id}/members/invitations/{invitation_id}/resend - Resend invitation
DELETE /projects/{project_id}/members/invitations/{invitation_id}    - Revoke invitation
POST   /projects/members/invitations/accept                          - Accept invitation
PATCH  /projects/{project_id}/members/{member_id}                    - Change member role
DELETE /projects/{project_id}/members/{member_id}                    - Remove member
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectAccess,
    check_role,
    get_current_active_user,
    get_project_or_404,
)
from app.core.database import get_db
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.project_member import (
    ProjectInvitationAccept,
    ProjectInvitationAcceptResponse,
    ProjectInvitationCreateResponse,
    ProjectInvitationListItem,
    ProjectMemberInvite,
    ProjectMemberListItem,
    ProjectMemberRoleUpdate,
)
from app.service import activity_log_service, project_member_service

router = APIRouter(
    prefix="/projects",
    tags=["project-members"],
)


@router.get(
    "/{project_id}/members",
    response_model=PaginatedResponse[ProjectMemberListItem],
)
async def list_project_members(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List active members for a project."""
    members, total = await project_member_service.list_members(
        db,
        access.project,
        page=page,
        per_page=per_page,
    )
    return PaginatedResponse(
        items=[ProjectMemberListItem(**member) for member in members],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/{project_id}/members/invite",
    response_model=ProjectInvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_project_member(
    body: ProjectMemberInvite,
    background_tasks: BackgroundTasks,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Invite a user by email.

    Owner can invite any role. Manager can invite only member/viewer.
    """
    check_role(access, "owner", "manager")

    invitation_payload, raw_token = await project_member_service.invite_member(
        db,
        access.project,
        user,
        access.role_name,
        body,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    invitation = ProjectInvitationListItem(**invitation_payload)

    background_tasks.add_task(
        project_member_service.send_project_invitation_email_with_retry,
        recipient_email=invitation.email,
        inviter_name=user.full_name or user.email,
        project_name=access.project.name,
        role_name=invitation.role,
        raw_token=raw_token,
    )

    return ProjectInvitationCreateResponse(invitation=invitation)


@router.get(
    "/{project_id}/members/invitations",
    response_model=PaginatedResponse[ProjectInvitationListItem],
)
async def list_project_invitations(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List pending project invitations."""
    check_role(access, "owner", "manager")

    invitations, total = await project_member_service.list_pending_invitations(
        db,
        access.project,
        page=page,
        per_page=per_page,
    )
    return PaginatedResponse(
        items=[ProjectInvitationListItem(**invitation) for invitation in invitations],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/{project_id}/members/invitations/{invitation_id}/resend",
    response_model=ProjectInvitationCreateResponse,
)
async def resend_project_invitation(
    invitation_id: UUID,
    background_tasks: BackgroundTasks,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Resend a pending invitation.

    Owner can resend any invitation. Manager can resend member/viewer invitations.
    """
    check_role(access, "owner", "manager")

    invitation_payload, raw_token = await project_member_service.resend_invitation(
        db,
        access.project,
        invitation_id,
        access.role_name,
    )
    invitation = ProjectInvitationListItem(**invitation_payload)

    background_tasks.add_task(
        project_member_service.send_project_invitation_email_with_retry,
        recipient_email=invitation.email,
        inviter_name=user.full_name or user.email,
        project_name=access.project.name,
        role_name=invitation.role,
        raw_token=raw_token,
    )

    return ProjectInvitationCreateResponse(invitation=invitation)


@router.delete(
    "/{project_id}/members/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_project_invitation(
    invitation_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Revoke a pending invitation.

    Owner can revoke any invitation. Manager can revoke member/viewer invitations.
    """
    check_role(access, "owner", "manager")
    await project_member_service.revoke_invitation(
        db,
        access.project,
        invitation_id,
        access.role_name,
    )


@router.post(
    "/members/invitations/accept",
    response_model=ProjectInvitationAcceptResponse,
)
async def accept_project_invitation(
    body: ProjectInvitationAccept,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    """Accept an invitation token for the authenticated user."""
    project_id, member_id = await project_member_service.accept_invitation(
        db,
        user,
        body,
    )
    return ProjectInvitationAcceptResponse(project_id=project_id, member_id=member_id)


@router.patch(
    "/{project_id}/members/{member_id}",
    response_model=ProjectMemberListItem,
)
async def update_project_member_role(
    member_id: UUID,
    body: ProjectMemberRoleUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Change a member role. Owner only."""
    check_role(access, "owner")
    member = await project_member_service.change_role(
        db,
        access.project,
        member_id,
        body,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return ProjectMemberListItem(**member)


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_member(
    member_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Remove a member from the project.

    Owner can remove any non-protected member. Manager can remove member/viewer.
    """
    check_role(access, "owner", "manager")
    await project_member_service.remove_member(
        db,
        access.project,
        member_id,
        access.role_name,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
