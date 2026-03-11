import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException
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


def _working_day() -> dict:
    return {"start": "09:00", "end": "17:00", "breaks": []}


MON_THU_WORK_WEEK: list[dict | None] = [
    None,  # Sunday
    _working_day(),  # Monday
    _working_day(),  # Tuesday
    _working_day(),  # Wednesday
    _working_day(),  # Thursday
    None,  # Friday
    None,  # Saturday
]


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
    constraint_type: ConstraintType = ConstraintType.ASAP,
    constraint_date: date | None = None,
    parent_task_id: uuid.UUID | None = None,
    is_summary: bool = False,
    outline_level: int = 1,
) -> Task:
    task = Task(
        project_id=project.id,
        wbs_code=str(order_index),
        outline_level=outline_level,
        order_index=order_index,
        name=name,
        start_date=start_date,
        finish_date=start_date,
        duration=duration,
        constraint_type=constraint_type,
        constraint_date=constraint_date,
        parent_task_id=parent_task_id,
        is_summary=is_summary,
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
    lag: int = 0,
) -> None:
    dep = Dependency(
        project_id=project.id,
        predecessor_id=predecessor.id,
        successor_id=successor.id,
        type=dep_type,
        lag=lag,
    )
    session.add(dep)
    await session.flush()


async def _attach_project_calendar(
    session: AsyncSession,
    *,
    project: Project,
    work_week: list[dict | None],
) -> Calendar:
    calendar = Calendar(
        project_id=project.id,
        name=f"Scheduling Calendar {uuid7()}",
        work_week=work_week,
    )
    session.add(calendar)
    await session.flush()
    project.default_calendar_id = calendar.id
    await session.flush()
    return calendar


async def _add_calendar_exception(
    session: AsyncSession,
    *,
    calendar: Calendar,
    start_date: date,
    end_date: date | None = None,
    is_working: bool = False,
) -> CalendarException:
    exception = CalendarException(
        calendar_id=calendar.id,
        name=f"Scheduling Exception {uuid7()}",
        start_date=start_date,
        end_date=end_date or start_date,
        is_working=is_working,
    )
    session.add(exception)
    await session.flush()
    return exception


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


def _build_pred_data(*, es: date, ef: date) -> _TaskScheduleData:
    predecessor = Task(
        project_id=_uuid(),
        wbs_code="1",
        outline_level=1,
        order_index=1,
        name="Predecessor",
        start_date=es,
        finish_date=ef,
        duration=480,
    )
    return _TaskScheduleData(task=predecessor, es=es, ef=ef)


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


@pytest.mark.asyncio
async def test_single_task_no_deps_starts_at_project_start(
    session: AsyncSession,
) -> None:
    """Forward pass: one isolated task starts at project start."""
    project = await _create_project(
        session,
        suffix="forward-single-task",
        start_date=date(2024, 1, 1),
    )
    task = await _create_task(
        session,
        project=project,
        name="Solo",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task)
    await session.refresh(project)

    assert task.start_date == date(2024, 1, 1)
    assert task.finish_date == date(2024, 1, 2)
    assert task.total_slack == 0
    assert project.finish_date == date(2024, 1, 2)


@pytest.mark.asyncio
async def test_fs_chain_two_tasks(session: AsyncSession) -> None:
    """Forward pass: FS chain computes successor ES from predecessor EF."""
    project = await _create_project(
        session,
        suffix="forward-fs-two-tasks",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=1440,  # 3 working days (3 * 480min)
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
        dep_type=DependencyType.FS,
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)

    assert task_a.finish_date == date(2024, 1, 2)
    assert task_b.start_date == date(2024, 1, 3)
    assert task_b.finish_date == date(2024, 1, 5)


@pytest.mark.asyncio
async def test_ss_dependency_same_start(session: AsyncSession) -> None:
    """Forward pass: SS dependency aligns successor start with predecessor start."""
    project = await _create_project(
        session,
        suffix="forward-ss",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
        dep_type=DependencyType.SS,
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)

    assert task_a.start_date == date(2024, 1, 1)
    assert task_b.start_date == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_ff_dependency_derives_start_from_finish() -> None:
    """Forward pass helper: FF derives successor start from predecessor finish."""
    pred_data = _build_pred_data(es=date(2024, 1, 3), ef=date(2024, 1, 4))
    dep = Dependency(
        project_id=_uuid(),
        predecessor_id=_uuid(),
        successor_id=_uuid(),
        type=DependencyType.FF,
        lag=0,
    )

    driven = _compute_dep_driven_date(
        dep,
        pred_data,
        960,  # 2 working days (2 * 480min)
        DEFAULT_WORK_WEEK,
        [],
    )

    assert driven == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_sf_dependency_reverses_logic() -> None:
    """Forward pass helper: SF maps predecessor start to successor finish."""
    pred_data = _build_pred_data(es=date(2024, 1, 3), ef=date(2024, 1, 3))
    dep = Dependency(
        project_id=_uuid(),
        predecessor_id=_uuid(),
        successor_id=_uuid(),
        type=DependencyType.SF,
        lag=0,
    )

    driven = _compute_dep_driven_date(
        dep,
        pred_data,
        960,  # 2 working days (2 * 480min)
        DEFAULT_WORK_WEEK,
        [],
    )

    assert driven == date(2024, 1, 2)


@pytest.mark.asyncio
async def test_fs_with_positive_lag() -> None:
    """Forward pass helper: FS lag adds working-day offset to successor start."""
    pred_data = _build_pred_data(es=date(2024, 1, 1), ef=date(2024, 1, 1))
    dep = Dependency(
        project_id=_uuid(),
        predecessor_id=_uuid(),
        successor_id=_uuid(),
        type=DependencyType.FS,
        lag=960,  # +2 working days of lag (2 * 480min)
    )

    driven = _compute_dep_driven_date(
        dep,
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )

    assert driven == date(2024, 1, 4)


@pytest.mark.asyncio
async def test_fs_with_zero_lag() -> None:
    """Forward pass helper: FS with zero lag starts successor next day."""
    pred_data = _build_pred_data(es=date(2024, 1, 1), ef=date(2024, 1, 1))
    dep = Dependency(
        project_id=_uuid(),
        predecessor_id=_uuid(),
        successor_id=_uuid(),
        type=DependencyType.FS,
        lag=0,
    )

    driven = _compute_dep_driven_date(
        dep,
        pred_data,
        480,
        DEFAULT_WORK_WEEK,
        [],
    )

    assert driven == date(2024, 1, 2)


@pytest.mark.asyncio
async def test_multiple_predecessors_takes_latest(session: AsyncSession) -> None:
    """Forward pass: successor ES takes max among predecessor-driven dates."""
    project = await _create_project(
        session,
        suffix="forward-multi-preds",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
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
        session, project=project, predecessor=task_a, successor=task_c
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    await calculate_schedule(session, project)
    await session.refresh(task_c)

    assert task_c.start_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_disconnected_tasks_start_at_project_start(session: AsyncSession) -> None:
    """Forward pass: disconnected tasks start at project start."""
    project = await _create_project(
        session,
        suffix="forward-disconnected",
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
        duration=960,  # 2 working days (2 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)

    assert task_a.start_date == date(2024, 1, 1)
    assert task_b.start_date == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_es_lands_on_non_working_day_shifts_forward(
    session: AsyncSession,
) -> None:
    """Forward pass: project start on weekend shifts task ES to next working day."""
    project = await _create_project(
        session,
        suffix="forward-weekend-start",
        start_date=date(2024, 1, 6),  # Saturday
    )
    task = await _create_task(
        session,
        project=project,
        name="Weekend Shift",
        order_index=1,
        start_date=date(2024, 1, 6),
        duration=480,  # 1 working day (8h * 60min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task)

    assert task.start_date == date(2024, 1, 8)  # Monday
    assert task.finish_date == date(2024, 1, 8)


@pytest.mark.asyncio
async def test_terminal_task_lf_equals_project_finish(session: AsyncSession) -> None:
    """Backward pass: terminal task finish aligns with computed project finish."""
    project = await _create_project(
        session,
        suffix="backward-terminal",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    task_c = await _create_task(
        session,
        project=project,
        name="C",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    await calculate_schedule(session, project)
    await session.refresh(task_c)
    await session.refresh(project)

    assert task_c.finish_date == project.finish_date
    assert project.finish_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_backward_pass_propagates_lf(session: AsyncSession) -> None:
    """Backward pass: predecessor slack follows successor LS propagation."""
    project = await _create_project(
        session,
        suffix="backward-propagation",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    _ = await _create_task(
        session,
        project=project,
        name="Independent Long",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=1440,  # 3 working days (3 * 480min)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)

    assert task_b.total_slack == 480
    assert task_a.total_slack == 480
    assert task_a.free_slack == 0


@pytest.mark.asyncio
async def test_multiple_successors_takes_earliest(session: AsyncSession) -> None:
    """Backward pass: predecessor LF is constrained by earliest successor LS."""
    project = await _create_project(
        session,
        suffix="backward-earliest-successor",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session, project=project, name="A", order_index=1, start_date=date(2024, 1, 1)
    )
    task_b = await _create_task(
        session, project=project, name="B", order_index=2, start_date=date(2024, 1, 1)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
    )
    task_d = await _create_task(
        session, project=project, name="D", order_index=4, start_date=date(2024, 1, 1)
    )
    _ = await _create_task(
        session,
        project=project,
        name="Independent Long",
        order_index=5,
        start_date=date(2024, 1, 1),
        duration=1920,  # 4 working days (4 * 480min)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_c
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_d
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)
    await session.refresh(task_c)

    assert task_a.total_slack == 480
    assert task_b.total_slack == 480
    assert task_c.total_slack == 960


@pytest.mark.asyncio
async def test_critical_task_has_zero_total_slack(session: AsyncSession) -> None:
    """Slack: single-chain tasks are critical with zero total slack."""
    project = await _create_project(
        session,
        suffix="slack-critical-zero",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session, project=project, name="A", order_index=1, start_date=date(2024, 1, 1)
    )
    task_b = await _create_task(
        session, project=project, name="B", order_index=2, start_date=date(2024, 1, 1)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)
    await session.refresh(task_c)

    assert task_a.total_slack == 0
    assert task_b.total_slack == 0
    assert task_c.total_slack == 0


@pytest.mark.asyncio
async def test_non_critical_task_has_positive_total_slack(
    session: AsyncSession,
) -> None:
    """Slack: shorter parallel path receives positive total slack."""
    project = await _create_project(
        session,
        suffix="slack-positive",
        start_date=date(2024, 1, 1),
    )
    long_a = await _create_task(
        session,
        project=project,
        name="Long A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    long_b = await _create_task(
        session,
        project=project,
        name="Long B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    short_c = await _create_task(
        session,
        project=project,
        name="Short C",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    await _create_dependency(
        session, project=project, predecessor=long_a, successor=long_b
    )

    await calculate_schedule(session, project)
    await session.refresh(short_c)

    assert short_c.total_slack == 1440
    assert short_c.is_critical is False


@pytest.mark.asyncio
async def test_free_slack_equals_gap_to_earliest_successor(
    session: AsyncSession,
) -> None:
    """Slack: free slack equals gap from task EF to earliest successor ES."""
    project = await _create_project(
        session,
        suffix="slack-free-gap",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session, project=project, name="A", order_index=1, start_date=date(2024, 1, 1)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_c
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_c
    )

    await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)
    await session.refresh(task_c)

    assert task_c.start_date == date(2024, 1, 3)
    assert task_a.free_slack == 480
    assert task_a.total_slack == 480
    assert task_b.free_slack == 0
    assert task_b.total_slack == 0


@pytest.mark.asyncio
async def test_free_slack_equals_total_slack_for_terminal_tasks(
    session: AsyncSession,
) -> None:
    """Slack: terminal tasks use total slack as free slack."""
    project = await _create_project(
        session,
        suffix="slack-terminal",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="Long A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,
    )
    task_b = await _create_task(
        session,
        project=project,
        name="Long B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,
    )
    terminal_c = await _create_task(
        session,
        project=project,
        name="Terminal",
        order_index=3,
        start_date=date(2024, 1, 1),
        duration=480,
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )

    await calculate_schedule(session, project)
    await session.refresh(terminal_c)

    assert terminal_c.total_slack == 1440
    assert terminal_c.free_slack == terminal_c.total_slack


@pytest.mark.asyncio
async def test_asap_is_default_no_effect() -> None:
    """Constraint: ASAP leaves early start unchanged."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.ASAP,
        constraint_date=None,
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 4),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 4)


@pytest.mark.asyncio
async def test_alap_shifts_to_late_dates(session: AsyncSession) -> None:
    """Constraint: ALAP task shifts to late schedule dates."""
    project = await _create_project(
        session,
        suffix="constraint-alap",
        start_date=date(2024, 1, 1),
    )
    task_alap = await _create_task(
        session,
        project=project,
        name="ALAP Task",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
        constraint_type=ConstraintType.ALAP,
    )
    task_anchor = await _create_task(
        session,
        project=project,
        name="Anchor",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=1440,  # 3 working days (3 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task_alap)
    await session.refresh(task_anchor)

    assert task_anchor.start_date == date(2024, 1, 1)
    assert task_anchor.finish_date == date(2024, 1, 3)
    assert task_alap.start_date == date(2024, 1, 3)
    assert task_alap.finish_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_mso_forces_exact_start_date() -> None:
    """Constraint: MSO forces exact start date."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.MSO,
        constraint_date=date(2024, 1, 10),
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 1),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 10)


@pytest.mark.asyncio
async def test_mfo_derives_start_from_finish_date() -> None:
    """Constraint: MFO derives start from fixed finish date."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.MFO,
        constraint_date=date(2024, 1, 10),
        duration_minutes=960,  # 2 working days (2 * 480min)
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 1),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 9)


@pytest.mark.asyncio
async def test_snet_takes_later_of_dep_and_constraint() -> None:
    """Constraint: SNET takes later date between dependency-driven ES and constraint."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.SNET,
        constraint_date=date(2024, 1, 5),
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 3),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 5)


@pytest.mark.asyncio
async def test_snet_ignored_when_dep_is_later() -> None:
    """Constraint: SNET does not move ES backward when dependency is already later."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.SNET,
        constraint_date=date(2024, 1, 5),
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 8),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 8)


@pytest.mark.asyncio
async def test_snlt_caps_late_start() -> None:
    """Constraint: SNLT caps backward LF to configured limit."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.SNLT,
        constraint_date=date(2024, 1, 10),
    )

    constrained = _apply_backward_constraints(task, date(2024, 1, 12))

    assert constrained == date(2024, 1, 10)


@pytest.mark.asyncio
async def test_fnet_pushes_start_if_finish_too_early() -> None:
    """Constraint: FNET pushes start forward when computed finish is too early."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.FNET,
        constraint_date=date(2024, 1, 5),
        duration_minutes=960,  # 2 working days (2 * 480min)
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 1),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 4)


@pytest.mark.asyncio
async def test_fnet_no_effect_when_finish_already_late_enough() -> None:
    """Constraint: FNET keeps ES when EF already satisfies lower finish bound."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.FNET,
        constraint_date=date(2024, 1, 5),
        duration_minutes=960,  # 2 working days (2 * 480min)
    )

    constrained = _apply_forward_constraints(
        task,
        date(2024, 1, 4),
        DEFAULT_WORK_WEEK,
        [],
    )

    assert constrained == date(2024, 1, 4)


@pytest.mark.asyncio
async def test_fnlt_caps_late_finish() -> None:
    """Constraint: FNLT caps backward LF to configured latest finish."""
    task = _build_constraint_task(
        constraint_type=ConstraintType.FNLT,
        constraint_date=date(2024, 1, 8),
    )

    constrained = _apply_backward_constraints(task, date(2024, 1, 12))

    assert constrained == date(2024, 1, 8)


@pytest.mark.asyncio
async def test_single_chain_all_tasks_are_critical(session: AsyncSession) -> None:
    """Critical path: all tasks in a single dependency chain are critical."""
    project = await _create_project(
        session,
        suffix="cp-single-chain",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session, project=project, name="A", order_index=1, start_date=date(2024, 1, 1)
    )
    task_b = await _create_task(
        session, project=project, name="B", order_index=2, start_date=date(2024, 1, 1)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
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

    assert {str(task_id) for task_id in result.critical_path_task_ids} == {
        str(task_a.id),
        str(task_b.id),
        str(task_c.id),
    }
    assert task_a.is_critical is True
    assert task_b.is_critical is True
    assert task_c.is_critical is True


@pytest.mark.asyncio
async def test_parallel_paths_longest_is_critical(session: AsyncSession) -> None:
    """Critical path: longest parallel path determines critical tasks."""
    project = await _create_project(
        session,
        suffix="cp-parallel",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
    )
    task_d = await _create_task(
        session, project=project, name="D", order_index=4, start_date=date(2024, 1, 1)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_c, successor=task_d
    )

    result = await calculate_schedule(session, project)
    await session.refresh(task_a)
    await session.refresh(task_b)
    await session.refresh(task_c)
    await session.refresh(task_d)

    assert {str(task_id) for task_id in result.critical_path_task_ids} == {
        str(task_a.id),
        str(task_b.id),
    }
    assert task_c.is_critical is False
    assert task_d.is_critical is False


@pytest.mark.asyncio
async def test_diamond_pattern_identifies_driving_path(
    session: AsyncSession,
) -> None:
    """Critical path details: diamond graph returns the driving branch."""
    project = await _create_project(
        session,
        suffix="cp-diamond",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session, project=project, name="A", order_index=1, start_date=date(2024, 1, 1)
    )
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    task_c = await _create_task(
        session, project=project, name="C", order_index=3, start_date=date(2024, 1, 1)
    )
    task_d = await _create_task(
        session, project=project, name="D", order_index=4, start_date=date(2024, 1, 1)
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_b
    )
    await _create_dependency(
        session, project=project, predecessor=task_a, successor=task_c
    )
    await _create_dependency(
        session, project=project, predecessor=task_b, successor=task_d
    )
    await _create_dependency(
        session, project=project, predecessor=task_c, successor=task_d
    )

    result = await calculate_schedule(session, project)
    details = await get_critical_path_details(session, project)
    await session.refresh(task_c)

    assert {str(task_id) for task_id in result.critical_path_task_ids} == {
        str(task_a.id),
        str(task_b.id),
        str(task_d.id),
    }
    assert [str(task_id) for task_id in details.task_ids] == [
        str(task_a.id),
        str(task_b.id),
        str(task_d.id),
    ]
    assert details.path_length_days == 4
    assert task_c.is_critical is False


@pytest.mark.asyncio
async def test_empty_project_returns_empty_critical_path(
    session: AsyncSession,
) -> None:
    """Critical path details: empty project returns no path."""
    project = await _create_project(
        session,
        suffix="cp-empty",
        start_date=date(2024, 1, 1),
    )

    details = await get_critical_path_details(session, project)

    assert details.task_ids == []
    assert details.path_length_days == 0


@pytest.mark.asyncio
async def test_single_task_is_critical(session: AsyncSession) -> None:
    """Critical path: single task project marks the task critical."""
    project = await _create_project(
        session,
        suffix="cp-single-task",
        start_date=date(2024, 1, 1),
    )
    task = await _create_task(
        session,
        project=project,
        name="Solo",
        order_index=1,
        start_date=date(2024, 1, 1),
    )

    result = await calculate_schedule(session, project)
    await session.refresh(task)

    assert [str(task_id) for task_id in result.critical_path_task_ids] == [str(task.id)]
    assert task.total_slack == 0
    assert task.is_critical is True


@pytest.mark.asyncio
async def test_fs_with_negative_lag_produces_lead_time() -> None:
    """Forward pass helper: negative lag (lead) moves successor start earlier."""
    pred_data = _build_pred_data(es=date(2024, 1, 1), ef=date(2024, 1, 2))
    dep = Dependency(
        project_id=_uuid(),
        predecessor_id=_uuid(),
        successor_id=_uuid(),
        type=DependencyType.FS,
        lag=-480,  # -1 working day lead (1 * 480min)
    )

    driven = _compute_dep_driven_date(
        dep,
        pred_data,
        480,  # 1 working day (8h * 60min)
        DEFAULT_WORK_WEEK,
        [],
    )

    assert driven == date(2024, 1, 2)


@pytest.mark.asyncio
async def test_mixed_dependency_types_on_same_successor(session: AsyncSession) -> None:
    """Forward pass: mixed predecessor relation types still pick latest driven ES."""
    project = await _create_project(
        session,
        suffix="forward-mixed-dep-types",
        start_date=date(2024, 1, 1),
    )
    task_a = await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
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
        session,
        project=project,
        predecessor=task_a,
        successor=task_c,
        dep_type=DependencyType.FS,
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=task_b,
        successor=task_c,
        dep_type=DependencyType.SS,
    )

    await calculate_schedule(session, project)
    await session.refresh(task_c)

    assert task_c.start_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_summary_task_excluded_from_cpm_calculation(
    session: AsyncSession,
) -> None:
    """Summary tasks are rolled up, but leaf task update count stays leaf-only."""
    project = await _create_project(
        session,
        suffix="summary-excluded-from-cpm",
        start_date=date(2024, 1, 1),
    )
    summary = await _create_task(
        session,
        project=project,
        name="Summary",
        order_index=1,
        start_date=date(2024, 1, 10),
        duration=480,
        is_summary=True,
    )
    child = await _create_task(
        session,
        project=project,
        name="Child",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        parent_task_id=summary.id,
    )
    independent = await _create_task(
        session,
        project=project,
        name="Independent",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
    )

    result = await calculate_schedule(session, project)
    await session.refresh(summary)
    await session.refresh(child)
    await session.refresh(independent)

    assert result.tasks_updated == 2
    assert summary.start_date == child.start_date
    assert summary.finish_date == child.finish_date


@pytest.mark.asyncio
async def test_summary_inherits_min_start_max_finish_from_children(
    session: AsyncSession,
) -> None:
    """Summary rollup: parent dates are min/max over direct children."""
    project = await _create_project(
        session,
        suffix="summary-min-max",
        start_date=date(2024, 1, 1),
    )
    summary = await _create_task(
        session,
        project=project,
        name="Parent Summary",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
    )
    child_a = await _create_task(
        session,
        project=project,
        name="Child A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        parent_task_id=summary.id,
    )
    child_b = await _create_task(
        session,
        project=project,
        name="Child B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
        parent_task_id=summary.id,
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=child_a,
        successor=child_b,
    )

    await calculate_schedule(session, project)
    await session.refresh(summary)
    await session.refresh(child_a)
    await session.refresh(child_b)

    assert child_a.start_date == date(2024, 1, 1)
    assert child_b.finish_date == date(2024, 1, 3)
    assert summary.start_date == date(2024, 1, 1)
    assert summary.finish_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_nested_summaries_propagate_bottom_up(session: AsyncSession) -> None:
    """Nested summary rollups propagate from leaf children to grandparent."""
    project = await _create_project(
        session,
        suffix="summary-nested-propagation",
        start_date=date(2024, 1, 1),
    )
    grandparent = await _create_task(
        session,
        project=project,
        name="Grandparent Summary",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
        outline_level=1,
    )
    parent = await _create_task(
        session,
        project=project,
        name="Parent Summary",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
        parent_task_id=grandparent.id,
        is_summary=True,
        outline_level=2,
    )
    leaf_a = await _create_task(
        session,
        project=project,
        name="Leaf A",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        parent_task_id=parent.id,
        outline_level=3,
    )
    leaf_b = await _create_task(
        session,
        project=project,
        name="Leaf B",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
        parent_task_id=parent.id,
        outline_level=3,
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=leaf_a,
        successor=leaf_b,
    )

    await calculate_schedule(session, project)
    await session.refresh(parent)
    await session.refresh(grandparent)

    assert parent.start_date == date(2024, 1, 1)
    assert parent.finish_date == date(2024, 1, 3)
    assert grandparent.start_date == date(2024, 1, 1)
    assert grandparent.finish_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_summary_is_critical_if_any_child_is_critical(
    session: AsyncSession,
) -> None:
    """Summary critical flag is true when any child is on critical path."""
    project = await _create_project(
        session,
        suffix="summary-critical-flag",
        start_date=date(2024, 1, 1),
    )
    summary = await _create_task(
        session,
        project=project,
        name="Summary",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
    )
    child_critical = await _create_task(
        session,
        project=project,
        name="Child Critical",
        order_index=1,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
        parent_task_id=summary.id,
    )
    child_noncritical = await _create_task(
        session,
        project=project,
        name="Child Noncritical",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        parent_task_id=summary.id,
    )
    external_terminal = await _create_task(
        session,
        project=project,
        name="External Terminal",
        order_index=2,
        start_date=date(2024, 1, 1),
        duration=960,  # 2 working days (2 * 480min)
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=child_critical,
        successor=external_terminal,
    )

    await calculate_schedule(session, project)
    await session.refresh(child_critical)
    await session.refresh(child_noncritical)
    await session.refresh(summary)

    assert child_critical.is_critical is True
    assert child_noncritical.is_critical is False
    assert summary.is_critical is True
    assert summary.total_slack == 0


@pytest.mark.asyncio
async def test_schedule_skips_weekends(session: AsyncSession) -> None:
    """Calendar-aware: 2-day task starting Friday finishes Monday (weekend skipped)."""
    project = await _create_project(
        session,
        suffix="calendar-weekend-skip",
        start_date=date(2024, 1, 5),  # Friday
    )
    task = await _create_task(
        session,
        project=project,
        name="Weekend Span",
        order_index=1,
        start_date=date(2024, 1, 5),
        duration=960,  # 2 working days (2 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task)

    assert task.start_date == date(2024, 1, 5)
    assert task.finish_date == date(2024, 1, 8)


@pytest.mark.asyncio
async def test_schedule_skips_holiday_exception(session: AsyncSession) -> None:
    """Calendar-aware: holiday exception pushes finish beyond otherwise-working day."""
    project = await _create_project(
        session,
        suffix="calendar-holiday-exception",
        start_date=date(2024, 1, 5),  # Friday
    )
    calendar = await _attach_project_calendar(
        session,
        project=project,
        work_week=DEFAULT_WORK_WEEK,
    )
    await _add_calendar_exception(
        session,
        calendar=calendar,
        start_date=date(2024, 1, 8),  # Monday holiday
        is_working=False,
    )
    task = await _create_task(
        session,
        project=project,
        name="Holiday Span",
        order_index=1,
        start_date=date(2024, 1, 5),
        duration=960,  # 2 working days (2 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task)

    assert task.start_date == date(2024, 1, 5)
    assert task.finish_date == date(2024, 1, 9)


@pytest.mark.asyncio
async def test_schedule_with_custom_work_week(session: AsyncSession) -> None:
    """Calendar-aware: custom Mon-Thu calendar treats Friday as non-working."""
    project = await _create_project(
        session,
        suffix="calendar-custom-work-week",
        start_date=date(2024, 1, 4),  # Thursday
    )
    await _attach_project_calendar(
        session,
        project=project,
        work_week=MON_THU_WORK_WEEK,
    )
    task = await _create_task(
        session,
        project=project,
        name="Mon-Thu Task",
        order_index=1,
        start_date=date(2024, 1, 4),
        duration=960,  # 2 working days (2 * 480min)
    )

    await calculate_schedule(session, project)
    await session.refresh(task)

    assert task.start_date == date(2024, 1, 4)
    assert task.finish_date == date(2024, 1, 8)
