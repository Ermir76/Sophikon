"""
Insights endpoints for organization-level dashboards.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.organization import (
    OrgAccess,
    get_org_access_or_404,
)
from app.api.v1.endpoints._insights_window import resolve_window_or_422
from app.core.database import get_db
from app.schema.insights import (
    DashboardInsightsResponse,
    InsightsWindowPreset,
)
from app.service import insights_service

router = APIRouter(tags=["insights"])


@router.get(
    "/organizations/{org_id}/insights/dashboard",
    response_model=DashboardInsightsResponse,
)
async def get_dashboard_insights(
    access: Annotated[OrgAccess, Depends(get_org_access_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_preset: Annotated[InsightsWindowPreset, Query()] = "30d",
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
):
    """
    Return dashboard control-center insights for an organization.
    """
    window_start, window_end = resolve_window_or_422(
        window_preset,
        start_date,
        end_date,
        organization=access.organization,
    )
    payload = await insights_service.get_org_dashboard_insights(
        db, access.organization, window_start, window_end
    )
    return DashboardInsightsResponse.model_validate(payload)
