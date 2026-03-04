"""
Calendar business logic.

Handles listing, creating, updating, and deleting calendars and their exceptions.
Note: Calendars use hard delete.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException
from app.models.project import Project
from app.schema.calendar import (
    CalendarCreate,
    CalendarExceptionCreate,
    CalendarExceptionUpdate,
    CalendarUpdate,
)


async def list_calendars(
    db: AsyncSession,
    project: Project,
) -> list[Calendar]:
    """
    List calendars for a project.

    Returns project-specific calendars plus global base calendars.
    """
    result = await db.execute(
        select(Calendar)
        .where((Calendar.project_id == project.id) | (Calendar.project_id.is_(None)))
        .order_by(Calendar.is_base.desc(), Calendar.name.asc())
    )
    return list(result.scalars().all())


async def create_calendar(
    db: AsyncSession,
    project: Project,
    data: CalendarCreate,
) -> Calendar:
    """Create a new calendar in the project."""
    calendar = Calendar(
        project_id=project.id,
        name=data.name,
        is_base=data.is_base,
        base_calendar_id=data.base_calendar_id,
    )

    # Apply custom work week if provided
    if data.work_week is not None:
        calendar.work_week = data.work_week

    db.add(calendar)
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
    result = await db.execute(
        select(Calendar).where(
            Calendar.id == calendar_id,
            (Calendar.project_id == project_id) | (Calendar.project_id.is_(None)),
        )
    )
    return result.scalar_one_or_none()


async def update_calendar(
    db: AsyncSession,
    calendar: Calendar,
    data: CalendarUpdate,
) -> Calendar:
    """Update a calendar with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
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
    result = await db.execute(
        select(CalendarException)
        .where(CalendarException.calendar_id == calendar_id)
        .order_by(CalendarException.start_date.asc())
    )
    return list(result.scalars().all())


async def create_exception(
    db: AsyncSession,
    calendar_id: UUID,
    data: CalendarExceptionCreate,
) -> CalendarException:
    """Create a new calendar exception."""
    exception = CalendarException(
        calendar_id=calendar_id,
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
        is_working=data.is_working,
        work_times=data.work_times,
        recurrence=data.recurrence,
    )
    db.add(exception)
    await db.commit()
    await db.refresh(exception)
    return exception


async def get_exception_by_id(
    db: AsyncSession,
    exception_id: UUID,
    calendar_id: UUID,
) -> CalendarException | None:
    """Get a calendar exception by ID."""
    result = await db.execute(
        select(CalendarException).where(
            CalendarException.id == exception_id,
            CalendarException.calendar_id == calendar_id,
        )
    )
    return result.scalar_one_or_none()


async def update_exception(
    db: AsyncSession,
    exception: CalendarException,
    data: CalendarExceptionUpdate,
) -> CalendarException:
    """Update a calendar exception with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
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
