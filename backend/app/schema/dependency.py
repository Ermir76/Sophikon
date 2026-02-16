"""
Pydantic schemas for Dependency endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import DependencyType, LagFormat

# ── Request Schemas ──


class DependencyCreate(BaseModel):
    """Create a new dependency between tasks."""

    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    type: DependencyType = DependencyType.FS
    lag: int = Field(default=0, description="Lag in minutes (negative for lead)")
    lag_format: LagFormat = LagFormat.DURATION

    @model_validator(mode="after")
    def validate_no_self_reference(self):
        if self.predecessor_id == self.successor_id:
            raise ValueError("A task cannot depend on itself")
        return self


class DependencyUpdate(BaseModel):
    """
    Update an existing dependency (all fields optional).

    All fields are NOT NULL, so reject explicit nulls.
    """

    type: DependencyType = None
    lag: int = None
    lag_format: LagFormat = None
    is_disabled: bool = None


# ── Response Schemas ──


class DependencyResponse(BaseModel):
    """Dependency response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    predecessor_id: uuid.UUID
    successor_id: uuid.UUID
    type: DependencyType
    lag: int
    lag_format: LagFormat
    is_disabled: bool
    created_at: datetime
