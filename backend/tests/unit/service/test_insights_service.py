import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.service import insights_service, scheduling_service
from app.service.insights_service import _build_trend
from app.service.scheduling_service import _path_span_days


@dataclass
class _TaskStub:
    created_at: datetime
    updated_at: datetime
    finish_date: date
    percent_complete: float


@dataclass
class _ResourceStub:
    id: object
    project_id: uuid.UUID
    max_units: Decimal


@dataclass
class _AssignmentStub:
    resource_id: object
    start_date: date
    finish_date: date
    units: Decimal


def _point_by_day(points, day: date):
    return next(p for p in points if p["date"] == day)


def test_build_trend_keeps_late_completion_overdue_event():
    # Finish date in window, completed later -> should still count overdue event.
    task = _TaskStub(
        created_at=datetime(2026, 1, 1, 10, 0, 0),
        updated_at=datetime(2026, 1, 6, 9, 0, 0),  # completion day
        finish_date=date(2026, 1, 4),
        percent_complete=100.0,
    )

    trend = _build_trend([task], date(2026, 1, 1), date(2026, 1, 8))
    overdue_day = date(2026, 1, 5)  # day after finish date

    assert _point_by_day(trend, overdue_day)["overdue_tasks"] == 1
    assert _point_by_day(trend, date(2026, 1, 6))["completed_tasks"] == 1


def test_build_trend_does_not_mark_on_time_completion_as_overdue():
    # Completed on or before finish date -> no overdue event.
    task = _TaskStub(
        created_at=datetime(2026, 1, 1, 10, 0, 0),
        updated_at=datetime(2026, 1, 4, 9, 0, 0),
        finish_date=date(2026, 1, 4),
        percent_complete=100.0,
    )

    trend = _build_trend([task], date(2026, 1, 1), date(2026, 1, 8))
    overdue_day = date(2026, 1, 5)

    assert _point_by_day(trend, overdue_day)["overdue_tasks"] == 0


def test_path_span_days_counts_same_day_path_as_one_day():
    day = date(2026, 1, 5)

    assert _path_span_days(day, day) == 1


def test_resolve_window_uses_scoped_business_day_for_project(
    monkeypatch: pytest.MonkeyPatch,
):
    project = object()

    def fake_resolve_business_day(*, project=None, organization=None, user=None):
        assert project is not None
        assert organization is None
        assert user is None
        assert project is not None
        return date(2026, 1, 10)

    monkeypatch.setattr(
        insights_service, "resolve_business_day", fake_resolve_business_day
    )

    start_date, end_date = insights_service.resolve_window(
        "7d", None, None, project=project
    )

    assert start_date == date(2026, 1, 4)
    assert end_date == date(2026, 1, 10)


def test_resolve_window_uses_scoped_business_day_for_organization(
    monkeypatch: pytest.MonkeyPatch,
):
    organization = object()

    def fake_resolve_business_day(*, project=None, organization=None, user=None):
        assert project is None
        assert organization is not None
        assert user is None
        return date(2026, 2, 3)

    monkeypatch.setattr(
        insights_service, "resolve_business_day", fake_resolve_business_day
    )

    start_date, end_date = insights_service.resolve_window(
        "30d", None, None, organization=organization
    )

    assert start_date == date(2026, 1, 5)
    assert end_date == date(2026, 2, 3)


def test_compute_overallocation_counts_normalizes_uuid_like_resource_ids():
    project_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    counts = insights_service.compute_overallocation_counts(
        resources=[
            _ResourceStub(
                id=resource_id,
                project_id=project_id,
                max_units=Decimal("1.0"),
            )
        ],
        assignments=[
            _AssignmentStub(
                resource_id=str(resource_id),
                start_date=date(2026, 1, 6),
                finish_date=date(2026, 1, 7),
                units=Decimal("1.25"),
            )
        ],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
    )

    assert counts == {project_id: 1}


def test_compute_overallocation_counts_counts_each_resource_once_per_project():
    project_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    counts = insights_service.compute_overallocation_counts(
        resources=[
            _ResourceStub(
                id=resource_id,
                project_id=project_id,
                max_units=Decimal("1.0"),
            )
        ],
        assignments=[
            _AssignmentStub(
                resource_id=resource_id,
                start_date=date(2026, 1, 6),
                finish_date=date(2026, 1, 7),
                units=Decimal("1.10"),
            ),
            _AssignmentStub(
                resource_id=resource_id,
                start_date=date(2026, 1, 6),
                finish_date=date(2026, 1, 7),
                units=Decimal("0.15"),
            ),
        ],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 10),
    )

    assert counts == {project_id: 1}


async def _seed_dashboard_service_data(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> Project:
    today = date.today()

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Insights Service User",
        },
    )
    assert register_response.status_code == 201, register_response.text

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Service Dashboard Project",
            "organization_id": org_id,
            "start_date": str(today - timedelta(days=14)),
            "budget": 15000,
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_payloads = [
        {
            "name": "Completed task",
            "start_date": str(today - timedelta(days=9)),
            "duration": 480,
        },
        {
            "name": "Overdue critical task",
            "start_date": str(today - timedelta(days=5)),
            "duration": 960,
        },
        {
            "name": "Upcoming milestone",
            "start_date": str(today + timedelta(days=4)),
            "duration": 0,
            "is_milestone": True,
        },
        {
            "name": "Not started task",
            "start_date": str(today + timedelta(days=1)),
            "duration": 480,
        },
    ]

    for payload in task_payloads:
        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks", json=payload
        )
        assert response.status_code == 201, response.text

    project = (
        await session.execute(
            select(Project).where(Project.id == uuid.UUID(project_id))
        )
    ).scalar_one()
    tasks = list(
        (
            await session.execute(select(Task).where(Task.project_id == project.id))
        ).scalars()
    )
    tasks_by_name = {task.name: task for task in tasks}

    tasks_by_name["Completed task"].percent_complete = 100
    tasks_by_name["Completed task"].finish_date = today - timedelta(days=7)
    tasks_by_name["Completed task"].total_cost = 2400
    tasks_by_name["Completed task"].actual_cost = 2400
    tasks_by_name["Completed task"].remaining_cost = 0

    tasks_by_name["Overdue critical task"].percent_complete = 25
    tasks_by_name["Overdue critical task"].finish_date = today - timedelta(days=2)
    tasks_by_name["Overdue critical task"].is_critical = True
    tasks_by_name["Overdue critical task"].total_cost = 3000
    tasks_by_name["Overdue critical task"].actual_cost = 1200
    tasks_by_name["Overdue critical task"].remaining_cost = 1800

    tasks_by_name["Upcoming milestone"].finish_date = today + timedelta(days=5)

    tasks_by_name["Not started task"].finish_date = today + timedelta(days=3)
    tasks_by_name["Not started task"].total_cost = 1200
    tasks_by_name["Not started task"].remaining_cost = 1200

    await session.commit()

    resource_response = await client.post(
        f"/api/v1/projects/{project.id}/resources",
        json={"name": "Lead Engineer", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    assignment_response = await client.post(
        f"/api/v1/projects/{project.id}/tasks/{tasks_by_name['Overdue critical task'].id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.5,
            "start_date": str(today - timedelta(days=5)),
            "finish_date": str(today - timedelta(days=2)),
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    await session.refresh(project)
    return project


async def _seed_nested_dashboard_service_data(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> Project:
    today = date.today()

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Nested Insights User",
        },
    )
    assert register_response.status_code == 201, register_response.text

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Nested Dashboard Project",
            "organization_id": org_id,
            "start_date": str(today - timedelta(days=10)),
            "budget": 5000,
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    parent_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Parent summary",
            "start_date": str(today - timedelta(days=6)),
            "duration": 480,
        },
    )
    assert parent_response.status_code == 201, parent_response.text
    parent_id = parent_response.json()["id"]

    child_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Critical child",
            "parent_task_id": parent_id,
            "start_date": str(today - timedelta(days=4)),
            "duration": 960,
        },
    )
    assert child_response.status_code == 201, child_response.text

    project = (
        await session.execute(
            select(Project).where(Project.id == uuid.UUID(project_id))
        )
    ).scalar_one()
    tasks = list(
        (
            await session.execute(select(Task).where(Task.project_id == project.id))
        ).scalars()
    )
    tasks_by_name = {task.name: task for task in tasks}

    parent = tasks_by_name["Parent summary"]
    child = tasks_by_name["Critical child"]

    child.percent_complete = 50
    child.finish_date = today - timedelta(days=1)
    child.total_cost = 1000
    child.actual_cost = 400
    child.remaining_cost = 600
    child.is_critical = True

    # Mimic the rolled-up state that used to trigger double counting.
    parent.is_summary = True
    parent.percent_complete = 50
    parent.finish_date = child.finish_date
    parent.total_cost = child.total_cost
    parent.actual_cost = child.actual_cost
    parent.remaining_cost = child.remaining_cost
    parent.is_critical = True

    await session.commit()
    await session.refresh(project)
    return project


async def _seed_scheduled_critical_path_project(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> Project:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Critical Path User",
        },
    )
    assert register_response.status_code == 201, register_response.text

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Scheduled Critical Path Project",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    tasks = {}
    for payload in [
        {"name": "A", "start_date": "2024-01-01", "duration": 2100},
        {"name": "B", "start_date": "2024-01-01", "duration": 2100},
        {"name": "C", "start_date": "2024-01-01", "duration": 480},
    ]:
        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks", json=payload
        )
        assert response.status_code == 201, response.text
        task_data = response.json()
        tasks[payload["name"]] = task_data["id"]

    dependency_response = await client.post(
        f"/api/v1/projects/{project_id}/dependencies",
        json={
            "predecessor_id": tasks["A"],
            "successor_id": tasks["B"],
            "type": "FS",
        },
    )
    assert dependency_response.status_code == 201, dependency_response.text

    project = (
        await session.execute(
            select(Project).where(Project.id == uuid.UUID(project_id))
        )
    ).scalar_one()
    await scheduling_service.calculate_schedule(session, project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_get_project_dashboard_aggregates_summary_and_schedule(
    client: AsyncClient,
    session: AsyncSession,
):
    today = date.today()
    project = await _seed_dashboard_service_data(
        client,
        session,
        email="insights-service-summary@x.com",
        slug="org-insights-service-summary",
    )

    dashboard = await insights_service.get_project_dashboard(
        session,
        project,
        today - timedelta(days=29),
        today,
    )

    assert dashboard["summary"]["total_tasks"] == 4
    assert dashboard["summary"]["completed_tasks"] == 1
    assert dashboard["summary"]["in_progress_tasks"] == 1
    assert dashboard["summary"]["not_started_tasks"] == 2
    assert dashboard["summary"]["overdue_tasks"] == 1
    assert dashboard["summary"]["milestones"] == 1
    assert dashboard["summary"]["milestones_completed"] == 0
    assert dashboard["summary"]["percent_complete"] == 25.0
    assert dashboard["schedule"]["start_date"] == project.start_date
    assert dashboard["schedule"]["finish_date"] == today + timedelta(days=5)
    assert dashboard["schedule"]["duration_days"] == 19
    assert dashboard["schedule"]["days_elapsed"] == 14
    assert dashboard["schedule"]["days_remaining"] == 5


@pytest.mark.asyncio
async def test_get_project_dashboard_aggregates_costs_resources_and_activity(
    client: AsyncClient,
    session: AsyncSession,
):
    today = date.today()
    project = await _seed_dashboard_service_data(
        client,
        session,
        email="insights-service-costs@x.com",
        slug="org-insights-service-costs",
    )

    dashboard = await insights_service.get_project_dashboard(
        session,
        project,
        today - timedelta(days=29),
        today,
    )

    assert dashboard["resources"]["total_resources"] == 1
    assert dashboard["resources"]["overallocated_count"] == 1
    assert dashboard["cost"]["budget"] == 15000.0
    assert dashboard["cost"]["total_cost"] == 6600.0
    assert dashboard["cost"]["actual_cost"] == 3600.0
    assert dashboard["cost"]["remaining_cost"] == 3000.0
    assert dashboard["critical_path"]["task_count"] == 1
    assert dashboard["critical_path"]["total_duration_days"] == 2
    assert dashboard["upcoming_milestones"][0]["name"] == "Upcoming milestone"
    assert dashboard["overdue_tasks"][0]["name"] == "Overdue critical task"
    assert dashboard["overdue_tasks"][0]["days_overdue"] == 2
    assert dashboard["recent_activity"]


@pytest.mark.asyncio
async def test_get_project_dashboard_excludes_summary_rollups_from_leaf_metrics(
    client: AsyncClient,
    session: AsyncSession,
):
    today = date.today()
    project = await _seed_nested_dashboard_service_data(
        client,
        session,
        email="insights-service-nested@x.com",
        slug="org-insights-service-nested",
    )

    dashboard = await insights_service.get_project_dashboard(
        session,
        project,
        today - timedelta(days=29),
        today,
    )

    assert dashboard["summary"]["total_tasks"] == 1
    assert dashboard["summary"]["in_progress_tasks"] == 1
    assert dashboard["summary"]["overdue_tasks"] == 1
    assert dashboard["cost"]["total_cost"] == 1000.0
    assert dashboard["cost"]["actual_cost"] == 400.0
    assert dashboard["cost"]["remaining_cost"] == 600.0
    assert dashboard["critical_path"]["task_count"] == 1
    assert dashboard["critical_path"]["total_duration_days"] == 2
    assert len(dashboard["overdue_tasks"]) == 1
    assert dashboard["overdue_tasks"][0]["name"] == "Critical child"


@pytest.mark.asyncio
async def test_get_project_dashboard_reports_exact_critical_path_length(
    client: AsyncClient,
    session: AsyncSession,
):
    project = await _seed_scheduled_critical_path_project(
        client,
        session,
        email="insights-service-critical-path@x.com",
        slug="org-insights-service-critical-path",
    )

    dashboard = await insights_service.get_project_dashboard(
        session,
        project,
        date(2023, 12, 1),
        date(2024, 1, 31),
    )

    assert dashboard["critical_path"]["task_count"] == 2
    assert dashboard["critical_path"]["total_duration_days"] == 8
    assert dashboard["critical_path"]["path_length_days"] == 12
