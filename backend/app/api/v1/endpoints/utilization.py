"""
Resource Utilization & Over-Allocation endpoints.

GET /projects/{project_id}/utilization                          - All resources summary
GET /projects/{project_id}/utilization/{resource_id}            - Single resource utilization
GET /projects/{project_id}/utilization/over-allocations         - Over-allocation list
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.project import ProjectAccess, get_project_or_404
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schema.utilization import (
    OverAllocationResponse,
    ProjectUtilizationSummary,
    ResourceUtilizationResponse,
)
from app.service import resource_service, utilization_service

router = APIRouter(prefix="/projects/{project_id}/utilization", tags=["utilization"])


@router.get("", response_model=ProjectUtilizationSummary)
async def get_project_utilization(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
):
    """Get utilization summary for all active resources in the project."""
    payload = await utilization_service.get_project_utilization_summary(
        db, access.project, start_date, end_date
    )
    return ProjectUtilizationSummary.model_validate(payload)


@router.get("/over-allocations", response_model=OverAllocationResponse)
async def get_over_allocations(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
):
    """Detect over-allocated resources in the project date range."""
    payload = await utilization_service.detect_over_allocations(
        db, access.project, start_date, end_date
    )
    return OverAllocationResponse.model_validate(payload)


@router.get("/{resource_id}", response_model=ResourceUtilizationResponse)
async def get_resource_utilization(
    resource_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
):
    """Get time-phased utilization for a single resource."""
    resource = await resource_service.get_resource_by_id(
        db, resource_id, access.project.id
    )
    if not resource:
        raise NotFoundError("Resource not found")

    payload = await utilization_service.get_resource_utilization(
        db, access.project, resource, start_date, end_date
    )
    return ResourceUtilizationResponse.model_validate(payload)
