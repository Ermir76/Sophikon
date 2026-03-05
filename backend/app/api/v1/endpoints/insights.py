"""
Insights endpoints for dashboard and project overview.
"""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    OrgAccess,
    ProjectAccess,
    get_org_access_or_404,
    get_project_or_404,
)
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.schema.insights import (
    DashboardInsightsResponse,
    ProjectOverviewInsightsResponse,
)
from app.service import insights_service

router = APIRouter(tags=["insights"])

WindowPreset = Literal["7d", "30d", "90d", "custom"]


def _resolve_window_or_422(
    window_preset: WindowPreset,
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    try:
        return insights_service.resolve_window(window_preset, start_date, end_date)
    except ValueError as exc:
        raise ValidationError(str(exc))


@router.get(
    "/organizations/{org_id}/insights/dashboard",
    response_model=DashboardInsightsResponse,
)
async def get_dashboard_insights(
    org_id: UUID,
    access: Annotated[OrgAccess, Depends(get_org_access_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_preset: Annotated[WindowPreset, Query()] = "30d",
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
):
    """
    Return dashboard control-center insights for an organization.
    """
    window_start, window_end = _resolve_window_or_422(
        window_preset, start_date, end_date
    )
    return await insights_service.get_org_dashboard_insights(
        db, access.organization, window_start, window_end
    )


@router.get(
    "/projects/{project_id}/insights/overview",
    response_model=ProjectOverviewInsightsResponse,
)
async def get_project_overview_insights(
    project_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_preset: Annotated[WindowPreset, Query()] = "30d",
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
):
    """
    Return project overview control-center insights for a project.
    """
    window_start, window_end = _resolve_window_or_422(
        window_preset, start_date, end_date
    )
    return await insights_service.get_project_overview_insights(
        db, access.project, window_start, window_end
    )
