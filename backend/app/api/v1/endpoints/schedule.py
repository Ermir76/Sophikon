"""
Schedule endpoints.

POST   /projects/{project_id}/schedule/calculate       - Recalculate schedule
GET    /projects/{project_id}/schedule/critical-path    - Get critical path
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectAccess, check_role, get_project_or_404
from app.core.database import get_db
from app.schema.schedule import (
    CriticalPathResponse,
    CriticalPathTask,
    ScheduleCalculateResponse,
)
from app.service import scheduling_service

router = APIRouter(prefix="/projects/{project_id}/schedule", tags=["schedule"])


@router.post("/calculate", response_model=ScheduleCalculateResponse)
async def calculate_schedule(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually trigger a full schedule recalculation for the project."""
    check_role(access, "owner", "manager", "member")
    result = await scheduling_service.calculate_schedule(db, access.project)
    await db.commit()
    return ScheduleCalculateResponse(
        project_finish_date=result.project_finish_date,
        critical_path_task_ids=result.critical_path_task_ids,
        tasks_updated=result.tasks_updated,
    )


@router.get("/critical-path", response_model=CriticalPathResponse)
async def get_critical_path(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return all tasks currently on the critical path."""
    tasks = await scheduling_service.get_critical_path_tasks(db, access.project)
    return CriticalPathResponse(
        critical_path=[CriticalPathTask.model_validate(t) for t in tasks],
    )
