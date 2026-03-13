"""
Service contracts for task bulk use-cases.
"""

from datetime import date
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.models.enums import ConstraintType, TaskType


class TaskCreateInput(TypedDict):
    name: str
    parent_task_id: UUID | None
    notes: str | None
    start_date: date
    duration: int
    is_milestone: bool
    task_type: TaskType
    effort_driven: bool
    constraint_type: ConstraintType
    constraint_date: date | None
    deadline: date | None
    priority: int
    fixed_cost: Decimal
    calendar_id: UUID | None
    color: str | None


class TaskBulkUpdatePatchInput(TypedDict, total=False):
    parent_task_id: UUID | None
    name: str
    notes: str | None
    start_date: date
    finish_date: date
    duration: int
    is_milestone: bool
    task_type: TaskType
    effort_driven: bool
    constraint_type: ConstraintType
    constraint_date: date | None
    deadline: date | None
    priority: int
    percent_complete: Decimal
    fixed_cost: Decimal
    calendar_id: UUID | None
    color: str | None


class TaskBulkUpdateInputItem(TypedDict):
    id: UUID
    data: TaskBulkUpdatePatchInput
