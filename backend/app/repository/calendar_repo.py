"""
Calendar repository helpers.
"""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException


def _default_work_week() -> list[dict | None]:
    # Default Mon-Fri 09:00-17:00 (8h/day), no implicit lunch break.
    return [
        None,
        {"start": "09:00", "end": "17:00", "breaks": []},
        {"start": "09:00", "end": "17:00", "breaks": []},
        {"start": "09:00", "end": "17:00", "breaks": []},
        {"start": "09:00", "end": "17:00", "breaks": []},
        {"start": "09:00", "end": "17:00", "breaks": []},
        None,
    ]


async def list_for_project(
    db: AsyncSession,
    *,
    project_id: UUID,
) -> list[Calendar]:
    result = await db.execute(
        select(Calendar)
        .where((Calendar.project_id == project_id) | (Calendar.project_id.is_(None)))
        .order_by(Calendar.is_base.desc(), Calendar.name.asc())
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    project_id: UUID,
    payload: Mapping[str, Any],
) -> Calendar:
    work_week = (
        payload["work_week"]
        if payload["work_week"] is not None
        else _default_work_week()
    )
    calendar = Calendar(
        project_id=project_id,
        name=payload["name"],
        is_base=payload["is_base"],
        base_calendar_id=payload["base_calendar_id"],
        work_week=work_week,
    )
    db.add(calendar)
    await db.flush()
    return calendar


async def get_by_id_for_project_or_global(
    db: AsyncSession,
    *,
    calendar_id: UUID,
    project_id: UUID,
) -> Calendar | None:
    result = await db.execute(
        select(Calendar).where(
            Calendar.id == calendar_id,
            (Calendar.project_id == project_id) | (Calendar.project_id.is_(None)),
        )
    )
    return result.scalar_one_or_none()


async def list_exceptions(
    db: AsyncSession,
    *,
    calendar_id: UUID,
) -> list[CalendarException]:
    result = await db.execute(
        select(CalendarException)
        .where(CalendarException.calendar_id == calendar_id)
        .order_by(CalendarException.start_date.asc())
    )
    return list(result.scalars().all())


async def create_exception(
    db: AsyncSession,
    *,
    calendar_id: UUID,
    payload: Mapping[str, Any],
) -> CalendarException:
    exception = CalendarException(
        calendar_id=calendar_id,
        name=payload["name"],
        start_date=payload["start_date"],
        end_date=payload["end_date"],
        is_working=payload["is_working"],
        work_times=payload["work_times"],
        recurrence=payload["recurrence"],
    )
    db.add(exception)
    await db.flush()
    return exception


async def get_exception_by_id(
    db: AsyncSession,
    *,
    exception_id: UUID,
    calendar_id: UUID,
) -> CalendarException | None:
    result = await db.execute(
        select(CalendarException).where(
            CalendarException.id == exception_id,
            CalendarException.calendar_id == calendar_id,
        )
    )
    return result.scalar_one_or_none()
