"""
Project activity log endpoints.

GET /projects/{project_id}/activity - List project activity entries
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.project import ProjectAccess, get_project_or_404
from app.core.database import get_db
from app.models.enums import AuditAction
from app.schema.activity_log import ActivityEntityType, ActivityLogItem
from app.schema.common import PaginatedResponse
from app.service import activity_log_service

router = APIRouter(prefix="/projects/{project_id}/activity", tags=["activity"])


@router.get("", response_model=PaginatedResponse[ActivityLogItem])
async def list_project_activity(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
    user_id: Annotated[UUID | None, Query()] = None,
    entity_type: Annotated[ActivityEntityType | None, Query()] = None,
    action: Annotated[AuditAction | None, Query()] = None,
):
    """List paginated project activity entries."""
    items, total = await activity_log_service.list_activity(
        db,
        project_id=access.project.id,
        page=page,
        per_page=per_page,
        user_id=user_id,
        entity_type=entity_type,
        action=action,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )
