import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.assignment import Assignment
from app.models.enums import RateTable, ResourceType, RoleScope, WorkContour
from app.models.organization import Organization
from app.models.project import Project
from app.models.resource import Resource
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.service import utilization_service


def _d(value: str) -> Decimal:
    return Decimal(value)


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
        email=f"utilization-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Utilization User {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()

    organization = Organization(
        name=f"Utilization Org {suffix}",
        slug=f"utilization-org-{suffix}-{uuid7()}",
    )
    session.add(organization)
    await session.flush()

    project = Project(
        owner_id=user.id,
        organization_id=organization.id,
        name=f"Utilization Project {suffix}",
        start_date=date(2026, 3, 1),
    )
    session.add(project)
    await session.flush()
    return project


async def _create_resource(
    session: AsyncSession,
    *,
    project: Project,
    name: str,
    max_units: str,
    is_active: bool = True,
) -> Resource:
    resource = Resource(
        project_id=project.id,
        name=name,
        type=ResourceType.WORK,
        max_units=Decimal(max_units),
        is_active=is_active,
    )
    session.add(resource)
    await session.flush()
    return resource


async def _create_task(
    session: AsyncSession,
    *,
    project: Project,
    name: str,
    order_index: int,
) -> Task:
    task = Task(
        project_id=project.id,
        wbs_code=str(order_index),
        outline_level=1,
        order_index=order_index,
        name=name,
        start_date=date(2026, 3, 1),
        finish_date=date(2026, 3, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    session.add(task)
    await session.flush()
    return task


async def _create_assignment(
    session: AsyncSession,
    *,
    task: Task,
    resource: Resource,
    units: str,
    start_date: date,
    finish_date: date,
) -> Assignment:
    assignment = Assignment(
        task_id=task.id,
        resource_id=resource.id,
        units=Decimal(units),
        start_date=start_date,
        finish_date=finish_date,
        work=0,
        remaining_work=0,
        work_contour=WorkContour.FLAT,
        rate_table=RateTable.A,
    )
    session.add(assignment)
    await session.flush()
    return assignment


def test_build_daily_allocations_handles_mixed_uuid_implementations() -> None:
    """
    Regression guard: assignment/resource UUID objects may come from different
    implementations (uuid.UUID vs uuid_utils.UUID) but must still match.
    """
    resource_uuid7 = uuid7()
    resource = cast(
        Resource,
        SimpleNamespace(
            id=resource_uuid7,
            name="Mixed UUID Resource",
            max_units=Decimal("1.00"),
        ),
    )
    assignment = cast(
        Assignment,
        SimpleNamespace(
            id=uuid.UUID(str(uuid7())),
            task_id=uuid.UUID(str(uuid7())),
            resource_id=uuid.UUID(str(resource_uuid7)),  # stdlib UUID
            units=Decimal("0.50"),
            start_date=date(2026, 3, 3),
            finish_date=date(2026, 3, 3),
            task=SimpleNamespace(name="Mixed UUID Task"),
        ),
    )

    daily = utilization_service._build_daily_allocations(
        [assignment],
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 3),
    )

    assert daily[0]["allocated_units"] == _d("0.50")
    assert daily[0]["is_over_allocated"] is False


@pytest.mark.asyncio
async def test_single_assignment_under_max_not_over_allocated(
    session: AsyncSession,
) -> None:
    """One 50% assignment on 100% resource is never over-allocated."""
    project = await _create_project(session, suffix="single-under")
    resource = await _create_resource(
        session, project=project, name="Dev Under", max_units="1.00"
    )
    task = await _create_task(
        session, project=project, name="Task Under", order_index=1
    )
    await _create_assignment(
        session,
        task=task,
        resource=resource,
        units="0.50",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 5),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 5),
    )

    assert result["peak_units"] == _d("0.50")
    assert result["average_utilization"] == _d("0.50")
    assert all(d["is_over_allocated"] is False for d in result["daily_allocations"])


@pytest.mark.asyncio
async def test_single_assignment_over_max_is_over_allocated(
    session: AsyncSession,
) -> None:
    """One 125% assignment on 100% resource is over-allocated for each covered day."""
    project = await _create_project(session, suffix="single-over")
    resource = await _create_resource(
        session, project=project, name="Dev Over", max_units="1.00"
    )
    task = await _create_task(session, project=project, name="Task Over", order_index=1)
    await _create_assignment(
        session,
        task=task,
        resource=resource,
        units="1.25",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 4),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 4),
    )

    assert result["peak_units"] == _d("1.25")
    assert all(d["is_over_allocated"] is True for d in result["daily_allocations"])


@pytest.mark.asyncio
async def test_multiple_assignments_same_day_sum_units(session: AsyncSession) -> None:
    """Two overlapping assignments sum units for the same day."""
    project = await _create_project(session, suffix="sum-same-day")
    resource = await _create_resource(
        session, project=project, name="Dev Sum", max_units="2.00"
    )
    task_a = await _create_task(session, project=project, name="Task A", order_index=1)
    task_b = await _create_task(session, project=project, name="Task B", order_index=2)
    await _create_assignment(
        session,
        task=task_a,
        resource=resource,
        units="0.75",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 3),
    )
    await _create_assignment(
        session,
        task=task_b,
        resource=resource,
        units="0.50",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 3),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 3),
    )
    day = result["daily_allocations"][0]

    assert day["allocated_units"] == _d("1.25")
    assert len(day["assignments"]) == 2


@pytest.mark.asyncio
async def test_no_assignments_in_range_returns_zero_allocations(
    session: AsyncSession,
) -> None:
    """No assignments in range returns zero allocation for every requested day."""
    project = await _create_project(session, suffix="empty-range")
    resource = await _create_resource(
        session, project=project, name="Dev Empty", max_units="1.00"
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 5),
    )

    assert result["peak_units"] == _d("0")
    assert result["average_utilization"] == _d("0")
    assert [d["allocated_units"] for d in result["daily_allocations"]] == [
        _d("0"),
        _d("0"),
        _d("0"),
    ]


@pytest.mark.asyncio
async def test_resource_with_zero_max_units_always_over_allocated(
    session: AsyncSession,
) -> None:
    """Any non-zero assignment over a zero-capacity resource is over-allocation."""
    project = await _create_project(session, suffix="zero-max")
    resource = await _create_resource(
        session, project=project, name="Dev Zero", max_units="0.00"
    )
    task = await _create_task(session, project=project, name="Task Zero", order_index=1)
    await _create_assignment(
        session,
        task=task,
        resource=resource,
        units="0.10",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 3),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 3),
    )

    day = result["daily_allocations"][0]
    assert day["allocated_units"] == _d("0.10")
    assert day["max_units"] == _d("0.00")
    assert day["is_over_allocated"] is True


@pytest.mark.asyncio
async def test_assignment_partially_overlaps_range_clamped(
    session: AsyncSession,
) -> None:
    """Assignment outside bounds is clamped to requested date window."""
    project = await _create_project(session, suffix="clamped-overlap")
    resource = await _create_resource(
        session, project=project, name="Dev Clamp", max_units="1.00"
    )
    task = await _create_task(
        session, project=project, name="Task Clamp", order_index=1
    )
    await _create_assignment(
        session,
        task=task,
        resource=resource,
        units="0.60",
        start_date=date(2026, 3, 1),
        finish_date=date(2026, 3, 10),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 4),
        end_date=date(2026, 3, 6),
    )

    assert len(result["daily_allocations"]) == 3
    assert all(d["allocated_units"] == _d("0.60") for d in result["daily_allocations"])


@pytest.mark.asyncio
async def test_peak_units_is_maximum_across_all_days(session: AsyncSession) -> None:
    """Peak utilization equals the maximum single-day allocation in range."""
    project = await _create_project(session, suffix="peak-max")
    resource = await _create_resource(
        session, project=project, name="Dev Peak", max_units="2.00"
    )
    task_a = await _create_task(session, project=project, name="Task A", order_index=1)
    task_b = await _create_task(session, project=project, name="Task B", order_index=2)
    await _create_assignment(
        session,
        task=task_a,
        resource=resource,
        units="0.50",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 5),
    )
    await _create_assignment(
        session,
        task=task_b,
        resource=resource,
        units="1.00",
        start_date=date(2026, 3, 4),
        finish_date=date(2026, 3, 4),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 5),
    )

    assert result["peak_units"] == _d("1.50")


@pytest.mark.asyncio
async def test_average_utilization_excludes_unallocated_days(
    session: AsyncSession,
) -> None:
    """Average uses only allocated days, not full requested day count."""
    project = await _create_project(session, suffix="avg-excludes-empty")
    resource = await _create_resource(
        session, project=project, name="Dev Avg", max_units="1.00"
    )
    task = await _create_task(session, project=project, name="Task Avg", order_index=1)
    await _create_assignment(
        session,
        task=task,
        resource=resource,
        units="0.80",
        start_date=date(2026, 3, 4),
        finish_date=date(2026, 3, 4),
    )

    result = await utilization_service.get_resource_utilization(
        session,
        project,
        resource,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 5),
    )

    # Only one allocated day (03-04) contributes to average.
    assert result["average_utilization"] == _d("0.80")


@pytest.mark.asyncio
async def test_project_summary_aggregates_all_resources(session: AsyncSession) -> None:
    """Project summary returns one utilization entry per active resource."""
    project = await _create_project(session, suffix="project-summary")
    res_a = await _create_resource(
        session, project=project, name="Dev A", max_units="1.00"
    )
    res_b = await _create_resource(
        session, project=project, name="Dev B", max_units="1.00"
    )
    await _create_resource(
        session, project=project, name="Dev Inactive", max_units="1.00", is_active=False
    )
    task_a = await _create_task(session, project=project, name="Task A", order_index=1)
    task_b = await _create_task(session, project=project, name="Task B", order_index=2)
    await _create_assignment(
        session,
        task=task_a,
        resource=res_a,
        units="0.40",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 3),
    )
    await _create_assignment(
        session,
        task=task_b,
        resource=res_b,
        units="0.60",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 3),
    )

    summary = await utilization_service.get_project_utilization_summary(
        session,
        project,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 3),
    )

    assert len(summary["resources"]) == 2
    names = {item["resource_name"] for item in summary["resources"]}
    assert names == {"Dev A", "Dev B"}


@pytest.mark.asyncio
async def test_detect_over_allocations_returns_only_exceeding_days(
    session: AsyncSession,
) -> None:
    """Only days exceeding max_units are returned in over-allocation report."""
    project = await _create_project(session, suffix="detect-over")
    resource = await _create_resource(
        session, project=project, name="Dev Overalloc", max_units="1.00"
    )
    task_a = await _create_task(session, project=project, name="Task A", order_index=1)
    task_b = await _create_task(session, project=project, name="Task B", order_index=2)
    await _create_assignment(
        session,
        task=task_a,
        resource=resource,
        units="0.75",
        start_date=date(2026, 3, 3),
        finish_date=date(2026, 3, 5),
    )
    await _create_assignment(
        session,
        task=task_b,
        resource=resource,
        units="0.75",
        start_date=date(2026, 3, 4),
        finish_date=date(2026, 3, 4),
    )

    report = await utilization_service.detect_over_allocations(
        session,
        project,
        start_date=date(2026, 3, 3),
        end_date=date(2026, 3, 5),
    )

    assert report["total_count"] == 1
    item = report["items"][0]
    assert item["date"] == date(2026, 3, 4)
    assert item["allocated_units"] == _d("1.50")
    assert item["max_units"] == _d("1.00")
    assert item["exceeds_by"] == _d("0.50")
