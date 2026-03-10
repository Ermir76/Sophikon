"""
Pydantic schemas for Project endpoints.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus, ScheduleFrom, TaskType
from app.models.project import Project
from app.schema._patch import ModelPatchSchema

# Request Schemas


class ProjectSettingsPatch(BaseModel):
    """Patchable project settings payload (bounded known keys only)."""

    model_config = {"extra": "forbid"}

    hours_per_day: int | None = Field(default=None, ge=1, le=24)
    hours_per_week: int | None = Field(default=None, ge=1, le=168)
    days_per_month: int | None = Field(default=None, ge=1, le=31)
    first_day_of_week: int | None = Field(default=None, ge=0, le=6)
    default_task_type: TaskType | None = Field(default=None)
    new_tasks_effort_driven: bool | None = Field(default=None)
    auto_calculate: bool | None = Field(default=None)


class ProjectCreate(BaseModel):
    """Create a new project."""

    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    start_date: date
    schedule_from: ScheduleFrom = ScheduleFrom.START
    currency: str = Field(default="USD", min_length=3, max_length=3)
    budget: Decimal | None = None
    settings: ProjectSettingsPatch | None = None
    color: str | None = Field(default=None, max_length=32)


class ProjectUpdate(ModelPatchSchema):
    """
    Update an existing project (all fields optional).

    NOT NULL fields are optional to omit, but explicit null is rejected.
    Nullable fields keep `| None` to allow explicit null.
    """

    __sa_model__ = Project

    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_date: date | None = Field(default=None)
    status: ProjectStatus | None = Field(default=None)
    schedule_from: ScheduleFrom | None = Field(default=None)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    settings: ProjectSettingsPatch | None = Field(default=None)

    description: str | None = Field(default=None, max_length=4000)
    finish_date: date | None = None
    status_date: date | None = None
    default_calendar_id: uuid.UUID | None = None
    budget: Decimal | None = None
    color: str | None = Field(default=None, max_length=32)


# Response Schemas


class ProjectListItem(BaseModel):
    """Project summary for list view."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date
    finish_date: date | None
    color: str | None
    created_at: datetime
    updated_at: datetime


class ProjectDetail(BaseModel):
    """Full project details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_id: uuid.UUID
    organization_id: uuid.UUID
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
    color: str | None
    created_at: datetime
    updated_at: datetime
