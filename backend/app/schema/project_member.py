"""
Pydantic schemas for Project Member and Project Invitation endpoints.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

ProjectMemberRole = Literal["owner", "manager", "member", "viewer"]


class ProjectMemberInvite(BaseModel):
    """Invite a user to a project by email."""

    email: EmailStr
    role: ProjectMemberRole = "member"
    message: str | None = Field(default=None, max_length=2000)


class ProjectMemberRoleUpdate(BaseModel):
    """Change a project member role."""

    role: ProjectMemberRole


class ProjectInvitationAccept(BaseModel):
    """Accept a project invitation token."""

    token: str | None = Field(default=None, min_length=1, max_length=512)
    invitation_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_lookup_key(self) -> "ProjectInvitationAccept":
        if (self.token is None) == (self.invitation_id is None):
            raise ValueError("Provide exactly one of token or invitation_id")
        return self


class ProjectMemberListItem(BaseModel):
    """Project member summary for list view."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectMemberRole
    joined_at: datetime
    updated_at: datetime
    user_email: str | None = None
    user_full_name: str | None = None


class ProjectInvitationListItem(BaseModel):
    """Pending invitation summary."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    invited_by_id: uuid.UUID
    role: ProjectMemberRole
    email: str
    message: str | None
    expires_at: datetime
    accepted_at: datetime | None
    is_revoked: bool
    created_at: datetime
    invited_by_email: str | None = None
    invited_by_full_name: str | None = None


class ProjectInvitationCreateResponse(BaseModel):
    """Response payload after creating a project invitation."""

    invitation: ProjectInvitationListItem


class ProjectInvitationAcceptResponse(BaseModel):
    """Response payload after accepting an invitation."""

    project_id: uuid.UUID
    member_id: uuid.UUID
