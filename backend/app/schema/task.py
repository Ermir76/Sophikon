"""
Pydantic schemas for Task endpoints.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ConstraintType, TaskType

# ── Request Schemas ──


class TaskCreate(BaseModel):
    """Create a new task."""

    name: str = Field(min_length=1, max_length=500)
    parent_task_id: uuid.UUID | None = None
    notes: str | None = None
    start_date: date
    duration: int = Field(default=480, ge=0, description="Duration in minutes")
    is_milestone: bool = False
    task_type: TaskType = TaskType.FIXED_UNITS
    effort_driven: bool = True
    constraint_type: ConstraintType = ConstraintType.ASAP
    constraint_date: date | None = None
    deadline: date | None = None
    priority: int = Field(default=500, ge=0, le=1000)
    fixed_cost: Decimal = Decimal("0")
    color: str | None = None


class TaskUpdate(BaseModel):
    """
    Update an existing task (all fields optional).

    NOT NULL fields use `= None` (optional) but NOT `| None` (rejects explicit null).
    """

    # NOT NULL fields — optional but reject explicit null
    name: str = Field(default=None, min_length=1, max_length=500)
    start_date: date = None
    finish_date: date = None
    duration: int = Field(default=None, ge=0)
    is_milestone: bool = None
    task_type: TaskType = None
    effort_driven: bool = None
    constraint_type: ConstraintType = None
    priority: int = Field(default=None, ge=0, le=1000)
    percent_complete: Decimal = Field(default=None, ge=0, le=100)
    fixed_cost: Decimal = None

    # Nullable fields — can be explicitly set to null
    parent_task_id: uuid.UUID | None = None
    notes: str | None = None
    constraint_date: date | None = None
    deadline: date | None = None
    color: str | None = None


class TaskReorder(BaseModel):
    """Payload for reordering tasks via drag-and-drop."""

    after_task_id: uuid.UUID | None = None
    before_task_id: uuid.UUID | None = None
    new_parent_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_position_anchor(self) -> "TaskReorder":
        if self.after_task_id and self.before_task_id:
            raise ValueError("Cannot provide both after_task_id and before_task_id")
        return self


# ── Bulk Schemas ──


class TaskBulkCreate(BaseModel):
    """Payload for bulk creating tasks."""

    tasks: list[TaskCreate] = Field(min_length=1, max_length=100)


class TaskBulkUpdateItem(BaseModel):
    """A single task update in a bulk operation."""

    id: uuid.UUID
    data: TaskUpdate


class TaskBulkUpdate(BaseModel):
    """Payload for bulk updating tasks."""

    tasks: list[TaskBulkUpdateItem] = Field(min_length=1, max_length=100)


class TaskBulkDelete(BaseModel):
    """Payload for bulk deleting tasks."""

    task_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


# ── Response Schemas ──


class TaskResponse(BaseModel):
    """Task response with all details."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    parent_task_id: uuid.UUID | None
    wbs_code: str
    outline_level: int
    order_index: int
    sort_order: int
    name: str
    notes: str | None
    is_milestone: bool
    is_summary: bool
    is_critical: bool
    duration: int
    actual_duration: int
    remaining_duration: int
    work: int
    start_date: date
    finish_date: date
    actual_start: date | None
    actual_finish: date | None
    percent_complete: Decimal
    percent_work_complete: Decimal
    task_type: TaskType
    effort_driven: bool
    constraint_type: ConstraintType
    constraint_date: date | None
    deadline: date | None
    priority: int
    total_slack: int
    free_slack: int
    fixed_cost: Decimal
    total_cost: Decimal
    actual_cost: Decimal
    color: str | None
    created_at: datetime
    updated_at: datetime


class BulkOperationError(BaseModel):
    """Error details for a single item in a bulk operation."""

    index: int
    task_id: uuid.UUID | None = None
    message: str


class TaskBulkCreateResponse(BaseModel):
    """Response payload for bulk creating tasks."""

    tasks: list[TaskResponse]
    errors: list[BulkOperationError]


class BulkOperationResponse(BaseModel):
    """Response payload for bulk update and delete operations."""

    succeeded: int
    failed: int
    errors: list[BulkOperationError]
