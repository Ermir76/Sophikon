"""
Pydantic schemas for Organization endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request Schemas ──


class OrganizationCreate(BaseModel):
    """Create a new organization."""

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(
        min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )


class OrganizationUpdate(BaseModel):
    """
    Update an existing organization (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    """

    name: str = Field(default=None, min_length=1, max_length=255)
    slug: str = Field(
        default=None,
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    settings: dict = None


# ── Response Schemas ──


class OrganizationListItem(BaseModel):
    """Organization summary for list view."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    is_personal: bool
    created_at: datetime
    updated_at: datetime


class OrganizationDetail(BaseModel):
    """Full organization details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    is_personal: bool
    settings: dict
    created_at: datetime
    updated_at: datetime
