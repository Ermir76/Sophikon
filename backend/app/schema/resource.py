"""
Pydantic schemas for Resource endpoints.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import CostAccrual, ResourceType

# ── Request Schemas ──


class ResourceCreate(BaseModel):
    """Create a new resource."""

    name: str = Field(min_length=1, max_length=255)
    type: ResourceType = ResourceType.WORK
    initials: str | None = Field(default=None, max_length=10)
    email: EmailStr | None = None
    material_label: str | None = Field(default=None, max_length=50)
    max_units: Decimal = Field(default=Decimal("1.0"), ge=0)
    group_name: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    is_generic: bool = False
    standard_rate: Decimal = Decimal("0")
    overtime_rate: Decimal = Decimal("0")
    cost_per_use: Decimal = Decimal("0")
    accrue_at: CostAccrual = CostAccrual.PRORATED


class ResourceUpdate(BaseModel):
    """
    Update an existing resource (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    """

    # NOT NULL fields — optional but reject explicit null
    name: str = Field(default=None, min_length=1, max_length=255)
    type: ResourceType = None
    max_units: Decimal = Field(default=None, ge=0)
    is_generic: bool = None
    is_active: bool = None
    standard_rate: Decimal = None
    overtime_rate: Decimal = None
    cost_per_use: Decimal = None
    accrue_at: CostAccrual = None

    # Nullable fields — can be explicitly set to null
    initials: str | None = Field(default=None, max_length=10)
    email: EmailStr | None = None
    material_label: str | None = Field(default=None, max_length=50)
    group_name: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=50)


# ── Response Schemas ──


class ResourceResponse(BaseModel):
    """Resource response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    initials: str | None
    email: str | None
    type: ResourceType
    material_label: str | None
    max_units: Decimal
    group_name: str | None
    code: str | None
    is_generic: bool
    is_active: bool
    standard_rate: Decimal
    overtime_rate: Decimal
    cost_per_use: Decimal
    accrue_at: CostAccrual
    user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
