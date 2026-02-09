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
    """Update an existing resource (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: ResourceType | None = None
    initials: str | None = Field(default=None, max_length=10)
    email: EmailStr | None = None
    material_label: str | None = Field(default=None, max_length=50)
    max_units: Decimal | None = Field(default=None, ge=0)
    group_name: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    is_generic: bool | None = None
    is_active: bool | None = None
    standard_rate: Decimal | None = None
    overtime_rate: Decimal | None = None
    cost_per_use: Decimal | None = None
    accrue_at: CostAccrual | None = None


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
