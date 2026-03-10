"""
Calendar CRUD endpoints.

GET    /projects/{project_id}/calendars                                          - List project calendars
POST   /projects/{project_id}/calendars                                          - Create a new calendar
GET    /projects/{project_id}/calendars/{calendar_id}                            - Get calendar details
PATCH  /projects/{project_id}/calendars/{calendar_id}                            - Update calendar
DELETE /projects/{project_id}/calendars/{calendar_id}                            - Delete calendar (hard)
GET    /projects/{project_id}/calendars/{calendar_id}/exceptions                 - List exceptions
POST   /projects/{project_id}/calendars/{calendar_id}/exceptions                 - Create exception
PATCH  /projects/{project_id}/calendars/{calendar_id}/exceptions/{exception_id}  - Update exception
DELETE /projects/{project_id}/calendars/{calendar_id}/exceptions/{exception_id}  - Delete exception
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.project import ProjectAccess, check_role, get_project_or_404
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schema.calendar import (
    CalendarCreate,
    CalendarExceptionCreate,
    CalendarExceptionResponse,
    CalendarExceptionUpdate,
    CalendarResponse,
    CalendarUpdate,
)
from app.service import calendar_service

router = APIRouter(prefix="/projects/{project_id}/calendars", tags=["calendars"])


# ── Calendar Endpoints ──


@router.get("", response_model=list[CalendarResponse])
async def list_calendars(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all calendars for the project (includes global base calendars)."""
    calendars = await calendar_service.list_calendars(db, access.project)
    return [CalendarResponse.model_validate(c) for c in calendars]


@router.post(
    "",
    response_model=CalendarResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_calendar(
    body: CalendarCreate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new calendar in the project."""
    check_role(access, "owner", "manager")
    calendar = await calendar_service.create_calendar(
        db,
        access.project,
        body.model_dump(mode="python"),
    )
    return CalendarResponse.model_validate(calendar)


@router.get("/{calendar_id}", response_model=CalendarResponse)
async def get_calendar(
    calendar_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get calendar details."""
    calendar = await calendar_service.get_calendar_by_id(
        db, calendar_id, access.project.id
    )
    if not calendar:
        raise NotFoundError("Calendar not found")
    return CalendarResponse.model_validate(calendar)


@router.patch("/{calendar_id}", response_model=CalendarResponse)
async def update_calendar(
    calendar_id: UUID,
    body: CalendarUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a calendar."""
    check_role(access, "owner", "manager")
    calendar = await calendar_service.get_calendar_by_id(
        db, calendar_id, access.project.id
    )
    if not calendar:
        raise NotFoundError("Calendar not found")

    calendar = await calendar_service.update_calendar(
        db,
        calendar,
        body.model_dump(mode="python", exclude_unset=True),
    )
    return CalendarResponse.model_validate(calendar)


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a calendar (hard delete)."""
    check_role(access, "owner", "manager")
    calendar = await calendar_service.get_calendar_by_id(
        db, calendar_id, access.project.id
    )
    if not calendar:
        raise NotFoundError("Calendar not found")

    await calendar_service.delete_calendar(db, calendar)


# ── Calendar Exception Endpoints ──


@router.get(
    "/{calendar_id}/exceptions",
    response_model=list[CalendarExceptionResponse],
)
async def list_exceptions(
    calendar_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all exceptions for a calendar."""
    calendar = await calendar_service.get_calendar_by_id(
        db, calendar_id, access.project.id
    )
    if not calendar:
        raise NotFoundError("Calendar not found")

    exceptions = await calendar_service.list_exceptions(db, calendar_id)
    return [CalendarExceptionResponse.model_validate(e) for e in exceptions]


@router.post(
    "/{calendar_id}/exceptions",
    response_model=CalendarExceptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_exception(
    calendar_id: UUID,
    body: CalendarExceptionCreate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new calendar exception."""
    check_role(access, "owner", "manager")
    calendar = await calendar_service.get_calendar_by_id(
        db, calendar_id, access.project.id
    )
    if not calendar:
        raise NotFoundError("Calendar not found")

    exception = await calendar_service.create_exception(
        db,
        calendar_id,
        body.model_dump(mode="python"),
    )
    return CalendarExceptionResponse.model_validate(exception)


@router.patch(
    "/{calendar_id}/exceptions/{exception_id}",
    response_model=CalendarExceptionResponse,
)
async def update_exception(
    calendar_id: UUID,
    exception_id: UUID,
    body: CalendarExceptionUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a calendar exception."""
    check_role(access, "owner", "manager")
    exception = await calendar_service.get_exception_by_id(
        db, exception_id, calendar_id
    )
    if not exception:
        raise NotFoundError("Calendar exception not found")

    exception = await calendar_service.update_exception(
        db,
        exception,
        body.model_dump(mode="python", exclude_unset=True),
    )
    return CalendarExceptionResponse.model_validate(exception)


@router.delete(
    "/{calendar_id}/exceptions/{exception_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_exception(
    calendar_id: UUID,
    exception_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a calendar exception."""
    check_role(access, "owner", "manager")
    exception = await calendar_service.get_exception_by_id(
        db, exception_id, calendar_id
    )
    if not exception:
        raise NotFoundError("Calendar exception not found")

    await calendar_service.delete_exception(db, exception)
