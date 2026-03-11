"""
Integration flow tests for calendar-driven scheduling behavior.

Focus: changing calendar working/non-working days and verifying that
manual schedule recalculation updates task dates deterministically.
"""

import pytest
from httpx import AsyncClient


def _custom_four_day_work_week() -> list[dict | None]:
    """Sunday-first week where Friday+Saturday are non-working."""
    return [
        None,  # Sunday
        {"start": "09:00", "end": "17:00", "breaks": []},  # Monday
        {"start": "09:00", "end": "17:00", "breaks": []},  # Tuesday
        {"start": "09:00", "end": "17:00", "breaks": []},  # Wednesday
        {"start": "09:00", "end": "17:00", "breaks": []},  # Thursday
        None,  # Friday
        None,  # Saturday
    ]


async def _setup_project(client: AsyncClient, suffix: str) -> str:
    """Register user, create org/project, return project_id."""
    slug_suffix = suffix.lower().replace("_", "-")

    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"calendar_flow_{slug_suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Calendar Flow {suffix}",
        },
    )
    assert register_resp.status_code == 201, register_resp.text

    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org Calendar {suffix}", "slug": f"org-calendar-{slug_suffix}"},
    )
    assert org_resp.status_code == 201, org_resp.text
    org_id = org_resp.json()["id"]

    project_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Project Calendar {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
            "settings": {"auto_calculate": False},
        },
    )
    assert project_resp.status_code == 201, project_resp.text
    return project_resp.json()["id"]


async def _create_calendar(
    client: AsyncClient,
    project_id: str,
    *,
    name: str,
    work_week: list[dict | None] | None = None,
) -> str:
    payload: dict[str, object] = {"name": name, "is_base": False}
    if work_week is not None:
        payload["work_week"] = work_week

    resp = await client.post(f"/api/v1/projects/{project_id}/calendars", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _set_default_calendar(
    client: AsyncClient,
    project_id: str,
    calendar_id: str,
) -> None:
    resp = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"default_calendar_id": calendar_id},
    )
    assert resp.status_code == 200, resp.text


async def _create_task(
    client: AsyncClient,
    project_id: str,
    *,
    name: str,
    start_date: str,
    duration: int,
) -> str:
    # Use SNET to preserve a deterministic earliest-start anchor
    # while still allowing calendar exceptions to move non-working starts.
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": name,
            "start_date": start_date,
            "duration": duration,
            "constraint_type": "SNET",
            "constraint_date": start_date,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_holiday(
    client: AsyncClient,
    project_id: str,
    calendar_id: str,
    *,
    name: str,
    day: str,
) -> str:
    resp = await client.post(
        f"/api/v1/projects/{project_id}/calendars/{calendar_id}/exceptions",
        json={
            "name": name,
            "start_date": day,
            "end_date": day,
            "is_working": False,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _calculate_schedule(client: AsyncClient, project_id: str) -> None:
    resp = await client.post(f"/api/v1/projects/{project_id}/schedule/calculate")
    assert resp.status_code == 200, resp.text


async def _get_task(client: AsyncClient, project_id: str, task_id: str) -> dict:
    resp = await client.get(f"/api/v1/projects/{project_id}/tasks/{task_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_add_holiday_exception_reschedules_affected_tasks(client: AsyncClient):
    """
    Add a holiday on a task's anchored start day and verify the task shifts.

    Baseline: task starts/finishes on 2024-01-01.
    After holiday on 2024-01-01: task starts/finishes on 2024-01-02.
    """
    project_id = await _setup_project(client, "add_holiday")
    calendar_id = await _create_calendar(client, project_id, name="Standard")
    await _set_default_calendar(client, project_id, calendar_id)

    task_id = await _create_task(
        client,
        project_id,
        name="Holiday Sensitive Task",
        start_date="2024-01-01",
        duration=480,  # 1 working day (8h * 60min)
    )

    await _calculate_schedule(client, project_id)
    baseline = await _get_task(client, project_id, task_id)
    assert baseline["start_date"] == "2024-01-01"
    assert baseline["finish_date"] == "2024-01-01"

    await _create_holiday(
        client,
        project_id,
        calendar_id,
        name="New Year Holiday",
        day="2024-01-01",
    )
    await _calculate_schedule(client, project_id)

    shifted = await _get_task(client, project_id, task_id)
    assert shifted["start_date"] == "2024-01-02"
    assert shifted["finish_date"] == "2024-01-02"


@pytest.mark.asyncio
async def test_change_project_calendar_reschedules_all_tasks(client: AsyncClient):
    """
    Switch project calendar from 5-day to 4-day week and verify finish shift.

    Task anchored to Thu 2024-01-04, duration=960 (2 working days):
    - 5-day week finish: Fri 2024-01-05
    - 4-day week (Fri off) finish: Mon 2024-01-08
    """
    project_id = await _setup_project(client, "change_calendar")
    five_day_calendar_id = await _create_calendar(client, project_id, name="5-day")
    await _set_default_calendar(client, project_id, five_day_calendar_id)

    task_id = await _create_task(
        client,
        project_id,
        name="Calendar Switch Task",
        start_date="2024-01-04",  # Thursday
        duration=960,  # 2 working days
    )

    await _calculate_schedule(client, project_id)
    before = await _get_task(client, project_id, task_id)
    assert before["start_date"] == "2024-01-04"
    assert before["finish_date"] == "2024-01-05"

    four_day_calendar_id = await _create_calendar(
        client,
        project_id,
        name="4-day",
        work_week=_custom_four_day_work_week(),
    )
    await _set_default_calendar(client, project_id, four_day_calendar_id)
    await _calculate_schedule(client, project_id)

    after = await _get_task(client, project_id, task_id)
    assert after["start_date"] == "2024-01-04"
    assert after["finish_date"] == "2024-01-08"


@pytest.mark.asyncio
async def test_calendar_exception_on_task_finish_date_extends_task(
    client: AsyncClient,
):
    """
    Make the baseline finish day a holiday and verify finish extends.

    Task anchored to Thu 2024-01-04, duration=960 (2 working days):
    - baseline finish: Fri 2024-01-05
    - with holiday on Fri 2024-01-05: finish extends to Mon 2024-01-08
    """
    project_id = await _setup_project(client, "finish_exception")
    calendar_id = await _create_calendar(client, project_id, name="Standard")
    await _set_default_calendar(client, project_id, calendar_id)

    task_id = await _create_task(
        client,
        project_id,
        name="Finish Date Exception Task",
        start_date="2024-01-04",  # Thursday
        duration=960,  # 2 working days
    )

    await _calculate_schedule(client, project_id)
    baseline = await _get_task(client, project_id, task_id)
    assert baseline["start_date"] == "2024-01-04"
    assert baseline["finish_date"] == "2024-01-05"

    await _create_holiday(
        client,
        project_id,
        calendar_id,
        name="Friday Closure",
        day="2024-01-05",
    )
    await _calculate_schedule(client, project_id)

    extended = await _get_task(client, project_id, task_id)
    assert extended["start_date"] == "2024-01-04"
    assert extended["finish_date"] == "2024-01-08"
