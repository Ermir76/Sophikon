import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.dependency import Dependency
from app.models.enums import ConstraintType, DependencyType, RoleScope
from app.models.organization import Organization
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.service.calendar_utils import DEFAULT_WORK_WEEK
from app.service.scheduling_service import (
    _apply_backward_constraints,
    _apply_forward_constraints,
    _compute_dep_driven_date,
    _TaskScheduleData,
    _topological_sort,
    calculate_schedule,
    get_critical_path_details,
)


def _uuid() -> uuid.UUID:
    return uuid.UUID(bytes=uuid7().bytes)


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


async def _create_project(
    session: AsyncSession, *, suffix: str, start_date: date
) -> Project:
    role = await _ensure_system_user_role(session)
    user = User(
        email=f"scheduling-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Scheduling User {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()

    organization = Organization(
        name=f"Scheduling Org {suffix}",
        slug=f"scheduling-org-{suffix}-{uuid7()}",
    )
    session.add(organization)
    await session.flush()

    project = Project(
        owner_id=user.id,
        organization_id=organization.id,
        name=f"Scheduling Project {suffix}",
        start_date=start_date,
    )
    session.add(project)
    await session.flush()
    return project


async def _create_task(
    session: AsyncSession,
    *,
    project: Project,
    name: str,
    order_index: int,
    start_date: date,
    duration: int = 480,
) -> Task:
    task = Task(
        project_id=project.id,
        wbs_code=str(order_index),
        outline_level=1,
        order_index=order_index,
        name=name,
        start_date=start_date,
        finish_date=start_date,
        duration=duration,
    )
    session.add(task)
    await session.flush()
    return task


async def _create_dependency(
    session: AsyncSession,
    *,
    project: Project,
    predecessor: Task,
    successor: Task,
    dep_type: DependencyType = DependencyType.FS,
) -> None:
    dep = Dependency(
        project_id=project.id,
        predecessor_id=predecessor.id,
        successor_id=successor.id,
        type=dep_type,
        lag=0,
    )
    session.add(dep)
    await session.flush()


def _build_constraint_task(
    *,
    constraint_type: ConstraintType,
    constraint_date: date | None,
    duration_minutes: int = 480,
) -> Task:
    return Task(
        project_id=_uuid(),
        wbs_code="1",
        outline_level=1,
        order_index=1,
        name="Constraint Task",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=duration_minutes,
        constraint_type=constraint_type,
        constraint_date=constraint_date,
    )


@pytest.mark.asyncio
async def test_topological_sort_orders_dependencies_and_keeps_disconnected_nodes() -> (
    None
):
    task_a = _uuid()
    task_b = _uuid()
    task_c = _uuid()

    ordered = _topological_sort(
        [task_a, task_c, task_b],
        {task_a: [task_b]},
        {task_b: [task_a]},
    )

    assert set(ordered) == {task_a, task_b, task_c}
    assert ordered.index(task_a) < ordered.index(task_b)


@pytest.mark.asyncio
async def test_compute_dep_driven_date_supports_fs_ss_ff_and_sf() -> None:
    predecessor = Task(
        project_id=_uuid(),
        wbs_code="1",
        outline_level=1,
        order_index=1,
        name="Predecessor",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 2),
        duration=480,
    )
    pred_data = _TaskScheduleData(
        task=predecessor,
        es=date(2024, 1, 1),
        ef=date(2024, 1, 2),
    )

    fs_driven = _compute_dep_driven_date(
        Dependency(
            project_id=_uuid(),
            predecessor_id=_uuid(),
            successor_id=_uuid(),
            type=DependencyType.FS,
            lag=0,
        ),
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )
    ss_driven = _compute_dep_driven_date(
        Dependency(
            project_id=_uuid(),
            predecessor_id=_uuid(),
            successor_id=_uuid(),
            type=DependencyType.SS,
            lag=0,
        ),
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )
    ff_driven = _compute_dep_driven_date(
        Dependency(
            project_id=_uuid(),
            predecessor_id=_uuid(),
            successor_id=_uuid(),
            type=DependencyType.FF,
            lag=0,
        ),
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )
    sf_driven = _compute_dep_driven_date(
        Dependency(
            project_id=_uuid(),
            predecessor_id=_uuid(),
            successor_id=_uuid(),
            type=DependencyType.SF,
            lag=0,
        ),
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )

    assert fs_driven == date(2024, 1, 3)
    assert ss_driven == date(2024, 1, 1)
    assert ff_driven == date(2024, 1, 2)
    assert sf_driven == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_apply_forward_constraints_handles_mso_snet_and_fnet() -> None:
    mso_task = _build_constraint_task(
        constraint_type=ConstraintType.MSO,
        constraint_date=date(2024, 1, 10),
    )
    snet_task = _build_constraint_task(
        constraint_type=ConstraintType.SNET,
        constraint_date=date(2024, 1, 5),
    )
    fnet_task = _build_constraint_task(
        constraint_type=ConstraintType.FNET,
        constraint_date=date(2024, 1, 3),
    )

    mso_start = _apply_forward_constraints(
        mso_task,
        date(2024, 1, 1),
        DEFAULT_WORK_WEEK,
        [],
    )
    snet_start = _apply_forward_constraints(
        snet_task,
        date(2024, 1, 3),
        DEFAULT_WORK_WEEK,
        [],
    )
    fnet_start = _apply_forward_constraints(
        fnet_task,
        date(2024, 1, 1),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert mso_start == date(2024, 1, 10)
    assert snet_start == date(2024, 1, 5)
    assert fnet_start == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_apply_backward_constraints_handles_fnlt_snlt_and_mfo() -> None:
    fnlt_task = _build_constraint_task(
        constraint_type=ConstraintType.FNLT,
        constraint_date=date(2024, 1, 10),
    )
    snlt_task = _build_constraint_task(
        constraint_type=ConstraintType.SNLT,
        constraint_date=date(2024, 1, 10),
    )
    mfo_task = _build_constraint_task(
        constraint_type=ConstraintType.MFO,
        constraint_date=date(2024, 1, 11),
    )

    fnlt_lf = _apply_backward_constraints(fnlt_task, date(2024, 1, 12))
    snlt_lf = _apply_backward_constraints(snlt_task, date(2024, 1, 12))
    mfo_lf = _apply_backward_constraints(mfo_task, date(2024, 1, 15))

    assert fnlt_lf == date(2024, 1, 10)
    assert snlt_lf == date(2024, 1, 10)
    assert mfo_lf == date(2024, 1, 11)


@pytest.mark.asyncio
async def test_calculate_schedule_empty_project_returns_start_date(
    session: AsyncSession,
) -> None:
    project = await _create_project(
        session,
        suffix="empty",
        start_date=date(2024, 1, 1),
    )

    result = await calculate_schedule(session, project)
    await session.refresh(project)

    assert result.tasks_updated == 0
    assert result.critical_path_task_ids == []
    assert result.project_finish_date == date(2024, 1, 1)
    assert project.finish_date == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_calculate_schedule_sets_fs_chain_dates_and_critical_flags(
    session: AsyncSession,
) -> None:
    project = await _create_project(
        session,
        suffix="chain",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    task_c = await _create_task(
        session,
        project=project,
        name="C",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    result = await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)
    await session.refresh(task_c)
    await session.refresh(project)

    assert result.tasks_updated == 3
    assert set(result.critical_path_task_ids) == {task_a.id, task_b.id, task_c.id}
    assert project.finish_date == date(2024, 1, 3)

    assert task_a.start_date == date(2024, 1, 1)
    assert task_a.finish_date == date(2024, 1, 1)
    assert task_a.total_slack == 0
    assert task_a.is_critical is True

    assert task_b.start_date == date(2024, 1, 2)
    assert task_b.finish_date == date(2024, 1, 2)
    assert task_b.total_slack == 0
    assert task_b.is_critical is True

    assert task_c.start_date == date(2024, 1, 3)
    assert task_c.finish_date == date(2024, 1, 3)
    assert task_c.total_slack == 0
    assert task_c.is_critical is True


@pytest.mark.asyncio
async def test_get_critical_path_details_returns_ordered_chain_and_span(
    session: AsyncSession,
) -> None:
    project = await _create_project(
        session,
        suffix="critical-path-details",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    task_c = await _create_task(
        session,
        project=project,
        name="C",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    await calculate_schedule(session, project)
    details = await get_critical_path_details(session, project)

    assert [str(task_id) for task_id in details.task_ids] == [
        str(task_a.id),
        str(task_b.id),
        str(task_c.id),
    ]
    assert details.path_length_days == 3
