"""
Pydantic schemas for Organization endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.organization import Organization
from app.schema._patch import ModelPatchSchema

# Request Schemas


class OrganizationCreate(BaseModel):
    """Create a new organization."""

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(
        min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )


class OrganizationUpdate(ModelPatchSchema):
    """
    Update an existing organization (all fields optional).

    NOT NULL fields are optional to omit, but explicit null is rejected.
    """

    __sa_model__ = Organization

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    settings: dict | None = Field(default=None)


# Response Schemas


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
