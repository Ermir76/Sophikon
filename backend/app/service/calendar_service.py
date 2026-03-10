"""
Calendar business logic.

Handles listing, creating, updating, and deleting calendars and their exceptions.
Note: Calendars use hard delete.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException
from app.models.project import Project
from app.repository import calendar_repo
from app.service.contracts.calendar import (
    CalendarCreateInput,
    CalendarExceptionCreateInput,
    CalendarExceptionPatchInput,
    CalendarPatchInput,
)


async def list_calendars(
    db: AsyncSession,
    project: Project,
) -> list[Calendar]:
    """
    List calendars for a project.

    Returns project-specific calendars plus global base calendars.
    """
    return await calendar_repo.list_for_project(db, project_id=project.id)


async def create_calendar(
    db: AsyncSession,
    project: Project,
    payload: CalendarCreateInput,
) -> Calendar:
    """Create a new calendar in the project."""
    calendar = await calendar_repo.create(db, project_id=project.id, payload=payload)
    await db.commit()
    await db.refresh(calendar)
    return calendar


async def get_calendar_by_id(
    db: AsyncSession,
    calendar_id: UUID,
    project_id: UUID,
) -> Calendar | None:
    """
    Get a calendar by ID.

    Matches both project-specific and global calendars.
    """
    return await calendar_repo.get_by_id_for_project_or_global(
        db,
        calendar_id=calendar_id,
        project_id=project_id,
    )


async def update_calendar(
    db: AsyncSession,
    calendar: Calendar,
    patch: CalendarPatchInput,
) -> Calendar:
    """Update a calendar with partial data."""
    for field, value in patch.items():
        setattr(calendar, field, value)

    await db.commit()
    await db.refresh(calendar)
    return calendar


async def delete_calendar(
    db: AsyncSession,
    calendar: Calendar,
) -> None:
    """Hard delete a calendar."""
    await db.delete(calendar)
    await db.commit()


# ── Calendar Exceptions ──


async def list_exceptions(
    db: AsyncSession,
    calendar_id: UUID,
) -> list[CalendarException]:
    """List all exceptions for a calendar."""
    return await calendar_repo.list_exceptions(db, calendar_id=calendar_id)


async def create_exception(
    db: AsyncSession,
    calendar_id: UUID,
    payload: CalendarExceptionCreateInput,
) -> CalendarException:
    """Create a new calendar exception."""
    exception = await calendar_repo.create_exception(
        db,
        calendar_id=calendar_id,
        payload=payload,
    )
    await db.commit()
    await db.refresh(exception)
    return exception


async def get_exception_by_id(
    db: AsyncSession,
    exception_id: UUID,
    calendar_id: UUID,
) -> CalendarException | None:
    """Get a calendar exception by ID."""
    return await calendar_repo.get_exception_by_id(
        db,
        exception_id=exception_id,
        calendar_id=calendar_id,
    )


async def update_exception(
    db: AsyncSession,
    exception: CalendarException,
    patch: CalendarExceptionPatchInput,
) -> CalendarException:
    """Update a calendar exception with partial data."""
    for field, value in patch.items():
        setattr(exception, field, value)

    await db.commit()
    await db.refresh(exception)
    return exception


async def delete_exception(
    db: AsyncSession,
    exception: CalendarException,
) -> None:
    """Hard delete a calendar exception."""
    await db.delete(exception)
    await db.commit()
