"""
Pydantic schemas for Project endpoints.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, ScheduleFrom


# ── Request Schemas ──


class ProjectCreate(BaseModel):
    """Create a new project."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    schedule_from: ScheduleFrom = ScheduleFrom.START
    currency: str = Field(default="USD", min_length=3, max_length=3)
    budget: Decimal | None = None
    settings: dict | None = None


class ProjectUpdate(BaseModel):
    """
    Update an existing project (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    Nullable fields keep `| None` to allow explicit null.
    """

    # NOT NULL fields — optional but reject explicit null
    name: str = Field(default=None, min_length=1, max_length=255)
    start_date: date = None
    status: ProjectStatus = None
    schedule_from: ScheduleFrom = None
    currency: str = Field(default=None, min_length=3, max_length=3)
    settings: dict = None

    # Nullable fields — can be explicitly set to null
    description: str | None = None
    finish_date: date | None = None
    status_date: date | None = None
    default_calendar_id: uuid.UUID | None = None
    budget: Decimal | None = None


# ── Response Schemas ──


class ProjectListItem(BaseModel):
    """Project summary for list view."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date
    finish_date: date | None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(BaseModel):
    """Full project details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    start_date: date
    finish_date: date | None
    status_date: date | None
    schedule_from: ScheduleFrom
    default_calendar_id: uuid.UUID | None
    status: ProjectStatus
    budget: Decimal | None
    currency: str
    settings: dict
    created_at: datetime
    updated_at: datetime
