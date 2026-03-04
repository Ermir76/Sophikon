"""
Pydantic schemas for Calendar endpoints.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Request Schemas ──


class CalendarCreate(BaseModel):
    """Create a new calendar."""

    name: str = Field(min_length=1, max_length=100)
    is_base: bool = False
    work_week: list | None = None
    base_calendar_id: uuid.UUID | None = None


class CalendarUpdate(BaseModel):
    """
    Update an existing calendar (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    """

    # NOT NULL fields — optional but reject explicit null
    name: str = Field(default=None, min_length=1, max_length=100)
    is_base: bool = None
    work_week: list = None

    # Nullable fields — can be explicitly set to null
    base_calendar_id: uuid.UUID | None = None


class CalendarExceptionCreate(BaseModel):
    """Create a calendar exception (holiday or special working day)."""

    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    is_working: bool = False
    work_times: dict | None = None
    recurrence: dict | None = None


class CalendarExceptionUpdate(BaseModel):
    """
    Update an existing calendar exception (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    """

    # NOT NULL fields — optional but reject explicit null
    name: str = Field(default=None, min_length=1, max_length=100)
    start_date: date = None
    end_date: date = None
    is_working: bool = None

    # Nullable fields — can be explicitly set to null
    work_times: dict | None = None
    recurrence: dict | None = None


# ── Response Schemas ──


class CalendarExceptionResponse(BaseModel):
    """Calendar exception response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    calendar_id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    is_working: bool
    work_times: dict | None
    recurrence: dict | None
    created_at: datetime


class CalendarResponse(BaseModel):
    """Calendar response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID | None
    base_calendar_id: uuid.UUID | None
    name: str
    is_base: bool
    work_week: list
    created_at: datetime
    updated_at: datetime
