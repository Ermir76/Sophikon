"""
Pydantic schemas for Calendar endpoints.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException
from app.schema._patch import ModelPatchSchema

# Request Schemas


TIME_OF_DAY_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
MAX_WORK_WEEK_DAYS = 7
MAX_BREAKS_PER_DAY = 8


class WorkBreak(BaseModel):
    """Single break interval in HH:MM format."""

    start: str = Field(pattern=TIME_OF_DAY_PATTERN)
    end: str = Field(pattern=TIME_OF_DAY_PATTERN)


class WorkDay(BaseModel):
    """Working day definition with optional breaks."""

    start: str = Field(pattern=TIME_OF_DAY_PATTERN)
    end: str = Field(pattern=TIME_OF_DAY_PATTERN)
    breaks: list[WorkBreak] = Field(default_factory=list, max_length=MAX_BREAKS_PER_DAY)


class RecurrenceRule(BaseModel):
    """Structured recurrence rule for calendar exceptions."""

    type: str = Field(min_length=1, max_length=32)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    weekday: int | None = Field(default=None, ge=0, le=6)
    interval: int | None = Field(default=None, ge=1, le=365)


class CalendarCreate(BaseModel):
    """Create a new calendar."""

    name: str = Field(min_length=1, max_length=100)
    is_base: bool = False
    work_week: list[WorkDay | None] | None = Field(
        default=None,
        min_length=MAX_WORK_WEEK_DAYS,
        max_length=MAX_WORK_WEEK_DAYS,
    )
    base_calendar_id: uuid.UUID | None = None


class CalendarUpdate(ModelPatchSchema):
    """
    Update an existing calendar (all fields optional).

    NOT NULL fields are optional to omit, but explicit null is rejected.
    """

    __sa_model__ = Calendar

    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_base: bool | None = Field(default=None)
    work_week: list[WorkDay | None] | None = Field(
        default=None,
        min_length=MAX_WORK_WEEK_DAYS,
        max_length=MAX_WORK_WEEK_DAYS,
    )
    base_calendar_id: uuid.UUID | None = Field(default=None)


class CalendarExceptionCreate(BaseModel):
    """Create a calendar exception (holiday or special working day)."""

    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    is_working: bool = False
    work_times: WorkDay | None = None
    recurrence: RecurrenceRule | None = None


class CalendarExceptionUpdate(ModelPatchSchema):
    """
    Update an existing calendar exception (all fields optional).

    NOT NULL fields are optional to omit, but explicit null is rejected.
    """

    __sa_model__ = CalendarException

    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    is_working: bool | None = Field(default=None)
    work_times: WorkDay | None = Field(default=None)
    recurrence: RecurrenceRule | None = Field(default=None)


# Response Schemas


class CalendarExceptionResponse(BaseModel):
    """Calendar exception response."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    calendar_id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    is_working: bool
    work_times: WorkDay | None
    recurrence: RecurrenceRule | None
    created_at: datetime


class CalendarResponse(BaseModel):
    """Calendar response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID | None
    base_calendar_id: uuid.UUID | None
    name: str
    is_base: bool
    work_week: list[WorkDay | None]
    created_at: datetime
    updated_at: datetime
