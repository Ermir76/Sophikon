"""
Pydantic schemas for Organization Member endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import OrgRole


# ── Request Schemas ──


class OrgMemberInvite(BaseModel):
    """Invite a user to an organization."""

    email: str = Field(min_length=1, max_length=255)
    role: OrgRole = OrgRole.MEMBER


class OrgMemberRoleUpdate(BaseModel):
    """Change a member's role."""

    role: OrgRole


# ── Response Schemas ──


class OrgMemberListItem(BaseModel):
    """Organization member summary for list view."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    updated_at: datetime
    # Flattened user info
    user_email: str | None = None
    user_full_name: str | None = None
