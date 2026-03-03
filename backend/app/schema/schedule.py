"""
Pydantic schemas for Schedule endpoints.
"""

import uuid
from datetime import date

from pydantic import BaseModel

# ── Response Schemas ──


class CriticalPathTask(BaseModel):
    """A single task on the critical path."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    wbs_code: str
    start_date: date
    finish_date: date
    duration: int
    total_slack: int
    free_slack: int


class ScheduleCalculateResponse(BaseModel):
    """Response from schedule calculation."""

    project_finish_date: date | None
    critical_path_task_ids: list[uuid.UUID]
    tasks_updated: int


class CriticalPathResponse(BaseModel):
    """Response for the critical path query."""

    critical_path: list[CriticalPathTask]
