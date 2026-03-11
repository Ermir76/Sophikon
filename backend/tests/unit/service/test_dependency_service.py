from datetime import date
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.exceptions import InvalidOperationError, ResourceConflictError
from app.models.dependency import Dependency
from app.models.enums import DependencyType, LagFormat, RoleScope
from app.models.organization import Organization
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.service import dependency_service


def _as_uuid(value: UUID | str) -> UUID:
    return UUID(str(value))


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
    session: AsyncSession,
    *,
    suffix: str,
    auto_calculate: bool = True,
) -> Project:
    role = await _ensure_system_user_role(session)

    user = User(
        email=f"dependency-service-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Dependency Service User {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()

    organization = Organization(
        name=f"Dependency Service Org {suffix}",
        slug=f"dependency-service-org-{suffix}-{uuid7()}",
    )
    session.add(organization)
    await session.flush()

    project = Project(
        owner_id=user.id,
        organization_id=organization.id,
        name=f"Dependency Service Project {suffix}",
        start_date=date(2026, 3, 1),
        settings={
            "hours_per_day": 8,
            "days_per_month": 20,
            "default_task_type": "FIXED_UNITS",
            "auto_calculate": auto_calculate,
        },
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
    is_deleted: bool = False,
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
        is_deleted=is_deleted,
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
    lag_format: LagFormat = LagFormat.DURATION,
) -> Dependency:
    return await dependency_service.create_dependency(
        session,
        project,
        {
            "predecessor_id": _as_uuid(predecessor.id),
            "successor_id": _as_uuid(successor.id),
            "type": dep_type,
            "lag": lag,
            "lag_format": lag_format,
        },
    )


@pytest.mark.asyncio
async def test_create_dependency_success_fs(session: AsyncSession) -> None:
    """Create succeeds for a valid Finish-to-Start dependency."""
    project = await _create_project(session, suffix="create-fs")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)

    dep = await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
        dep_type=DependencyType.FS,
    )

    assert _as_uuid(dep.project_id) == _as_uuid(project.id)
    assert _as_uuid(dep.predecessor_id) == _as_uuid(task_a.id)
    assert _as_uuid(dep.successor_id) == _as_uuid(task_b.id)
    assert dep.type == DependencyType.FS


@pytest.mark.parametrize(
    "dep_type",
    [DependencyType.SS, DependencyType.FF, DependencyType.SF],
)
@pytest.mark.asyncio
async def test_create_dependency_success_ss_ff_sf(
    session: AsyncSession,
    dep_type: DependencyType,
) -> None:
    """Create succeeds for SS/FF/SF dependency variants."""
    project = await _create_project(session, suffix=f"create-{dep_type.value.lower()}")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)

    dep = await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
        dep_type=dep_type,
    )

    assert dep.type == dep_type


@pytest.mark.asyncio
async def test_circular_direct_a_to_b_to_a_rejected(session: AsyncSession) -> None:
    """Cycle A->B then B->A is rejected."""
    project = await _create_project(session, suffix="cycle-direct")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)
    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )

    with pytest.raises(InvalidOperationError, match="circular"):
        await _create_dependency(
            session,
            project=project,
            predecessor=task_b,
            successor=task_a,
        )


@pytest.mark.asyncio
async def test_circular_transitive_a_to_b_to_c_to_a_rejected(
    session: AsyncSession,
) -> None:
    """Transitive cycle A->B->C then C->A is rejected."""
    project = await _create_project(session, suffix="cycle-transitive")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)
    task_c = await _create_task(session, project=project, name="C", order_index=3)

    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )
    await _create_dependency(
        session,
        project=project,
        predecessor=task_b,
        successor=task_c,
    )

    with pytest.raises(InvalidOperationError, match="circular"):
        await _create_dependency(
            session,
            project=project,
            predecessor=task_c,
            successor=task_a,
        )


@pytest.mark.asyncio
async def test_self_reference_rejected(session: AsyncSession) -> None:
    """A task cannot depend on itself."""
    project = await _create_project(session, suffix="self-ref")
    task_a = await _create_task(session, project=project, name="A", order_index=1)

    with pytest.raises(InvalidOperationError, match="cannot depend on itself"):
        await _create_dependency(
            session,
            project=project,
            predecessor=task_a,
            successor=task_a,
        )


@pytest.mark.asyncio
async def test_duplicate_dependency_rejected(session: AsyncSession) -> None:
    """Duplicate predecessor/successor pair is rejected as conflict."""
    project = await _create_project(session, suffix="duplicate")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)

    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )

    with pytest.raises(ResourceConflictError, match="already exists"):
        await _create_dependency(
            session,
            project=project,
            predecessor=task_a,
            successor=task_b,
        )


@pytest.mark.asyncio
async def test_cross_project_dependency_rejected(session: AsyncSession) -> None:
    """Dependency endpoints enforce both tasks belong to same project."""
    project_a = await _create_project(session, suffix="cross-a")
    project_b = await _create_project(session, suffix="cross-b")

    task_a1 = await _create_task(session, project=project_a, name="A1", order_index=1)
    task_b1 = await _create_task(session, project=project_b, name="B1", order_index=1)

    with pytest.raises(InvalidOperationError, match="task not found in this project"):
        await _create_dependency(
            session,
            project=project_a,
            predecessor=task_a1,
            successor=task_b1,
        )


@pytest.mark.asyncio
async def test_dependency_on_deleted_task_rejected(session: AsyncSession) -> None:
    """Soft-deleted tasks cannot participate in new dependencies."""
    project = await _create_project(session, suffix="deleted-task")
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        is_deleted=True,
    )

    with pytest.raises(InvalidOperationError, match="task not found in this project"):
        await _create_dependency(
            session,
            project=project,
            predecessor=task_a,
            successor=task_b,
        )


@pytest.mark.asyncio
async def test_create_triggers_schedule_recalculation(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create triggers schedule recalculation when project auto-calculate is enabled."""
    project = await _create_project(
        session, suffix="create-recalc", auto_calculate=True
    )
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)

    schedule_mock = AsyncMock()
    monkeypatch.setattr(
        "app.service.dependency_service.scheduling_service.calculate_schedule",
        schedule_mock,
    )

    await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )

    schedule_mock.assert_awaited_once_with(session, project)


@pytest.mark.asyncio
async def test_delete_triggers_schedule_recalculation(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delete triggers schedule recalculation when project auto-calculate is enabled."""
    project = await _create_project(
        session, suffix="delete-recalc", auto_calculate=False
    )
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)
    dep = await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )

    project.settings["auto_calculate"] = True

    schedule_mock = AsyncMock()
    monkeypatch.setattr(
        "app.service.dependency_service.scheduling_service.calculate_schedule",
        schedule_mock,
    )

    await dependency_service.delete_dependency(session, dep, project=project)

    schedule_mock.assert_awaited_once_with(session, project)


@pytest.mark.asyncio
async def test_update_lag_triggers_schedule_recalculation(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Updating lag triggers schedule recalculation when project is provided."""
    project = await _create_project(
        session, suffix="update-recalc", auto_calculate=False
    )
    task_a = await _create_task(session, project=project, name="A", order_index=1)
    task_b = await _create_task(session, project=project, name="B", order_index=2)
    dep = await _create_dependency(
        session,
        project=project,
        predecessor=task_a,
        successor=task_b,
    )

    project.settings["auto_calculate"] = True

    schedule_mock = AsyncMock()
    monkeypatch.setattr(
        "app.service.dependency_service.scheduling_service.calculate_schedule",
        schedule_mock,
    )

    updated = await dependency_service.update_dependency(
        session,
        dep,
        {"lag": 120},
        project=project,
    )

    schedule_mock.assert_awaited_once_with(session, project)
    assert updated.lag == 120
