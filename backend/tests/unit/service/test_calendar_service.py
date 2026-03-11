from datetime import date
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.calendar import Calendar
from app.models.enums import RoleScope
from app.models.organization import Organization
from app.models.project import Project
from app.models.role import Role
from app.models.user import User
from app.service import calendar_service


def _work_day(
    *,
    start: str = "09:00",
    end: str = "17:00",
    breaks: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {"start": start, "end": end, "breaks": breaks or []}


def _default_work_week() -> list[dict[str, Any] | None]:
    return [
        None,  # Sunday
        _work_day(),  # Monday
        _work_day(),  # Tuesday
        _work_day(),  # Wednesday
        _work_day(),  # Thursday
        _work_day(),  # Friday
        None,  # Saturday
    ]


def _custom_work_week() -> list[dict[str, Any] | None]:
    return [
        None,  # Sunday
        _work_day(start="08:00", end="12:00"),  # Monday half-day
        _work_day(start="10:00", end="18:00"),  # Tuesday shifted day
        _work_day(),  # Wednesday standard
        _work_day(),  # Thursday standard
        None,  # Friday off
        None,  # Saturday off
    ]


async def _ensure_system_user_role(session: AsyncSession) -> Role:
    result = await session.execute(
        select(Role).where(Role.name == "user", Role.scope == RoleScope.SYSTEM)
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name="user", scope=RoleScope.SYSTEM, is_system=True)
        session.add(role)
        await session.flush()
    return role


async def _create_project(session: AsyncSession, *, suffix: str) -> Project:
    role = await _ensure_system_user_role(session)

    user = User(
        email=f"calendar-service-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Calendar Service User {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()

    organization = Organization(
        name=f"Calendar Service Org {suffix}",
        slug=f"calendar-service-org-{suffix}-{uuid7()}",
    )
    session.add(organization)
    await session.flush()

    project = Project(
        owner_id=user.id,
        organization_id=organization.id,
        name=f"Calendar Service Project {suffix}",
        start_date=date(2026, 3, 1),
    )
    session.add(project)
    await session.flush()
    return project


@pytest.mark.asyncio
async def test_create_calendar_with_default_work_week(session: AsyncSession) -> None:
    """Creating without work_week applies the 7-day default pattern."""
    project = await _create_project(session, suffix="default-week")

    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Default Week",
            "is_base": False,
            "work_week": None,
            "base_calendar_id": None,
        },
    )

    assert str(calendar.project_id) == str(project.id)
    assert calendar.work_week == _default_work_week()


@pytest.mark.asyncio
async def test_create_calendar_with_custom_work_week(session: AsyncSession) -> None:
    """Creating with explicit work_week preserves the provided schedule exactly."""
    project = await _create_project(session, suffix="custom-week")
    custom_week = _custom_work_week()

    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Custom Week",
            "is_base": False,
            "work_week": custom_week,
            "base_calendar_id": None,
        },
    )

    assert calendar.work_week == custom_week


@pytest.mark.asyncio
async def test_create_calendar_with_base_reference(session: AsyncSession) -> None:
    """Child calendar stores base_calendar_id for inheritance-by-reference."""
    project = await _create_project(session, suffix="base-reference")
    base = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Base Calendar",
            "is_base": True,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    child = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Child Calendar",
            "is_base": False,
            "work_week": _custom_work_week(),
            "base_calendar_id": base.id,
        },
    )

    assert str(child.base_calendar_id) == str(base.id)
    assert child.work_week == _custom_work_week()


@pytest.mark.asyncio
async def test_calendar_inheritance_reference_only_no_runtime_merge(
    session: AsyncSession,
) -> None:
    """
    Pass-now behavior: inheritance is relation-only at runtime.

    TODO: if/when effective merged work-week APIs are added, replace this with
    assertions for composed base+child schedule semantics.
    """
    project = await _create_project(session, suffix="inheritance-reference-only")
    base_week = _default_work_week()
    child_week = _custom_work_week()

    base = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Merge Base",
            "is_base": True,
            "work_week": base_week,
            "base_calendar_id": None,
        },
    )
    child = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Merge Child",
            "is_base": False,
            "work_week": child_week,
            "base_calendar_id": base.id,
        },
    )

    assert str(child.base_calendar_id) == str(base.id)
    assert child.work_week == child_week
    assert child.work_week != base_week


@pytest.mark.asyncio
async def test_get_calendar_by_id_returns_global_for_project(
    session: AsyncSession,
) -> None:
    """Project lookups can resolve global (project_id=NULL) calendars."""
    project = await _create_project(session, suffix="global-lookup")
    global_calendar = Calendar(
        project_id=None,
        name=f"Global Base {uuid7()}",
        is_base=True,
        base_calendar_id=None,
        work_week=_default_work_week(),
    )
    session.add(global_calendar)
    await session.commit()

    found = await calendar_service.get_calendar_by_id(
        session, global_calendar.id, project.id
    )

    assert found is not None
    assert str(found.id) == str(global_calendar.id)


@pytest.mark.asyncio
async def test_list_calendars_includes_project_and_global(
    session: AsyncSession,
) -> None:
    """Listing returns both project calendars and global base calendars."""
    project = await _create_project(session, suffix="list-global-and-project")
    global_name = f"Global Base {uuid7()}"
    project_name = f"Project Calendar {uuid7()}"

    global_calendar = Calendar(
        project_id=None,
        name=global_name,
        is_base=True,
        base_calendar_id=None,
        work_week=_default_work_week(),
    )
    session.add(global_calendar)
    await session.flush()

    project_calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": project_name,
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    calendars = await calendar_service.list_calendars(session, project)
    by_name = [c for c in calendars if c.name in {global_name, project_name}]

    assert [c.name for c in by_name] == [global_name, project_name]
    assert {str(c.id) for c in by_name} == {
        str(global_calendar.id),
        str(project_calendar.id),
    }


@pytest.mark.asyncio
async def test_create_exception_marks_holiday_as_non_working(
    session: AsyncSession,
) -> None:
    """Non-working exception persists holiday semantics."""
    project = await _create_project(session, suffix="holiday-exception")
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Holiday Calendar",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    exception = await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "Christmas Eve",
            "start_date": date(2026, 12, 24),
            "end_date": date(2026, 12, 24),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )

    assert exception.is_working is False
    assert exception.work_times is None
    assert exception.start_date == date(2026, 12, 24)
    assert exception.end_date == date(2026, 12, 24)


@pytest.mark.asyncio
async def test_create_exception_marks_special_day_as_working(
    session: AsyncSession,
) -> None:
    """Working exception persists custom work_times and recurrence payload."""
    project = await _create_project(session, suffix="special-working-day")
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Special Day Calendar",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )
    work_times = _work_day(start="10:00", end="14:00")

    exception = await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "Year-End Working Window",
            "start_date": date(2026, 12, 31),
            "end_date": date(2026, 12, 31),
            "is_working": True,
            "work_times": work_times,
            "recurrence": {"type": "yearly", "month": 12, "day": 31},
        },
    )

    assert exception.is_working is True
    assert exception.work_times == work_times
    assert exception.recurrence == {"type": "yearly", "month": 12, "day": 31}


@pytest.mark.asyncio
async def test_list_exceptions_returns_sorted_for_one_calendar(
    session: AsyncSession,
) -> None:
    """Exception listing is ordered by start_date and scoped to one calendar."""
    project = await _create_project(session, suffix="list-exceptions-order")
    calendar_a = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Calendar A",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )
    calendar_b = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Calendar B",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    await calendar_service.create_exception(
        session,
        calendar_a.id,
        {
            "name": "Late",
            "start_date": date(2026, 12, 25),
            "end_date": date(2026, 12, 25),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )
    await calendar_service.create_exception(
        session,
        calendar_a.id,
        {
            "name": "Early",
            "start_date": date(2026, 12, 10),
            "end_date": date(2026, 12, 10),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )
    await calendar_service.create_exception(
        session,
        calendar_b.id,
        {
            "name": "Other Calendar Exception",
            "start_date": date(2026, 12, 1),
            "end_date": date(2026, 12, 1),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )

    exceptions = await calendar_service.list_exceptions(session, calendar_a.id)

    assert [e.name for e in exceptions] == ["Early", "Late"]
    assert all(str(e.calendar_id) == str(calendar_a.id) for e in exceptions)


@pytest.mark.asyncio
async def test_create_exception_allows_overlapping_ranges_current_behavior(
    session: AsyncSession,
) -> None:
    """
    Pass-now behavior: overlapping exceptions are currently accepted.

    TODO: if overlap policy becomes strict, replace this with rejection
    assertions and expected error semantics.
    """
    project = await _create_project(session, suffix="overlap-policy")
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Overlap Calendar",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    first = await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "First Range",
            "start_date": date(2026, 12, 20),
            "end_date": date(2026, 12, 22),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )
    second = await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "Overlapping Range",
            "start_date": date(2026, 12, 21),
            "end_date": date(2026, 12, 23),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )

    assert first.id != second.id
    exceptions = await calendar_service.list_exceptions(session, calendar.id)
    assert [e.name for e in exceptions] == ["First Range", "Overlapping Range"]


@pytest.mark.asyncio
async def test_list_exceptions_returns_full_calendar_scope_no_date_filter(
    session: AsyncSession,
) -> None:
    """
    Pass-now behavior: list_exceptions is calendar-scoped only (no date filtering).

    TODO: if a date-range filter surface is introduced, add a separate filtered
    listing test and keep this as unfiltered baseline behavior.
    """
    project = await _create_project(session, suffix="exception-scope")
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Exception Scope Calendar",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )

    await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "Far Past",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 1, 1),
            "is_working": False,
            "work_times": None,
            "recurrence": None,
        },
    )
    await calendar_service.create_exception(
        session,
        calendar.id,
        {
            "name": "Far Future",
            "start_date": date(2030, 1, 1),
            "end_date": date(2030, 1, 1),
            "is_working": True,
            "work_times": _work_day(start="12:00", end="14:00"),
            "recurrence": None,
        },
    )

    listed = await calendar_service.list_exceptions(session, calendar.id)
    assert [e.name for e in listed] == ["Far Past", "Far Future"]


@pytest.mark.asyncio
async def test_update_calendar_patch_updates_only_requested_fields(
    session: AsyncSession,
) -> None:
    """Partial patch updates target field and preserves untouched work_week."""
    project = await _create_project(session, suffix="update-partial")
    original_week = _custom_work_week()
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Calendar Before Patch",
            "is_base": False,
            "work_week": original_week,
            "base_calendar_id": None,
        },
    )

    updated = await calendar_service.update_calendar(
        session, calendar, {"name": "Calendar After Patch"}
    )

    assert updated.name == "Calendar After Patch"
    assert updated.work_week == original_week


@pytest.mark.asyncio
async def test_delete_base_calendar_sets_child_base_calendar_id_to_none(
    session: AsyncSession,
) -> None:
    """Deleting a base calendar nulls child.base_calendar_id via FK on-delete."""
    project = await _create_project(session, suffix="delete-base")
    base = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Base To Delete",
            "is_base": True,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )
    child = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Derived Child",
            "is_base": False,
            "work_week": _custom_work_week(),
            "base_calendar_id": base.id,
        },
    )

    await calendar_service.delete_calendar(session, base)
    refreshed_child = await calendar_service.get_calendar_by_id(
        session, child.id, project.id
    )

    assert refreshed_child is not None
    assert refreshed_child.base_calendar_id is None


@pytest.mark.asyncio
async def test_delete_project_default_calendar_sets_project_reference_to_none(
    session: AsyncSession,
) -> None:
    """Deleting a referenced calendar nulls project.default_calendar_id."""
    project = await _create_project(session, suffix="delete-default-reference")
    calendar = await calendar_service.create_calendar(
        session,
        project,
        {
            "name": "Project Default",
            "is_base": False,
            "work_week": _default_work_week(),
            "base_calendar_id": None,
        },
    )
    project.default_calendar_id = calendar.id
    await session.commit()

    await calendar_service.delete_calendar(session, calendar)
    await session.refresh(project)

    assert project.default_calendar_id is None
