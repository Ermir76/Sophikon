"""
Pydantic schemas for Assignment endpoints.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import RateTable, WorkContour


# ── Request Schemas ──


class AssignmentCreate(BaseModel):
    """Create a new assignment."""

    resource_id: uuid.UUID
    units: Decimal = Field(default=Decimal("1.0"), ge=0, description="1.0 = 100%")
    start_date: date
    finish_date: date
    work: int = Field(default=0, ge=0, description="Work in minutes")
    work_contour: WorkContour = WorkContour.FLAT
    rate_table: RateTable = RateTable.A


class AssignmentUpdate(BaseModel):
    """Update an existing assignment (all fields optional)."""

    units: Decimal | None = Field(default=None, ge=0)
    start_date: date | None = None
    finish_date: date | None = None
    work: int | None = Field(default=None, ge=0)
    actual_work: int | None = Field(default=None, ge=0)
    remaining_work: int | None = Field(default=None, ge=0)
    work_contour: WorkContour | None = None
    rate_table: RateTable | None = None
    percent_work_complete: Decimal | None = Field(default=None, ge=0, le=100)
    is_confirmed: bool | None = None


# ── Response Schemas ──


class AssignmentResponse(BaseModel):
    """Assignment response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    task_id: uuid.UUID
    resource_id: uuid.UUID
    units: Decimal
    work: int
    actual_work: int
    remaining_work: int
    start_date: date
    finish_date: date
    actual_start: date | None
    actual_finish: date | None
    work_contour: WorkContour
    cost: Decimal
    actual_cost: Decimal
    remaining_cost: Decimal
    rate_table: RateTable
    percent_work_complete: Decimal
    is_confirmed: bool
    created_at: datetime
