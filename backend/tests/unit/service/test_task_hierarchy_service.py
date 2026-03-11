import uuid
from datetime import date
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.exceptions import InvalidOperationError
from app.models.enums import RoleScope
from app.models.organization import Organization
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task
from app.models.user import User
from app.service import task_hierarchy_service


def _uuid() -> uuid.UUID:
    # Temporary test-level normalization: keep PK/FK values on stdlib UUID
    # to avoid mixed uuid_utils.UUID vs uuid.UUID behavior inside flush/reorder flows.
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


async def _create_project(session: AsyncSession, *, suffix: str) -> Project:
    role = await _ensure_system_user_role(session)
    user = User(
        email=f"hierarchy-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Hierarchy User {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()

    organization = Organization(
        name=f"Hierarchy Org {suffix}",
        slug=f"hierarchy-org-{suffix}-{uuid7()}",
    )
    session.add(organization)
    await session.flush()

    project = Project(
        owner_id=user.id,
        organization_id=organization.id,
        name=f"Hierarchy Project {suffix}",
        start_date=date(2026, 3, 1),
        settings={"auto_calculate": False},
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
    parent_task_id: UUID | None = None,
    outline_level: int = 1,
    wbs_code: str | None = None,
) -> Task:
    task = Task(
        id=_uuid(),
        project_id=project.id,
        parent_task_id=parent_task_id,
        wbs_code=wbs_code or str(order_index),
        outline_level=outline_level,
        order_index=order_index,
        name=name,
        start_date=date(2026, 3, 1),
        finish_date=date(2026, 3, 1),
        duration=480,  # 1 working day (8h * 60min)
    )
    session.add(task)
    await session.flush()
    return task


async def _get_task(session: AsyncSession, task_id: UUID) -> Task:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    assert task is not None
    return task


async def _list_active_tasks(session: AsyncSession, project: Project) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(Task.project_id == project.id, Task.is_deleted == False)  # noqa: E712
        .order_by(Task.sort_order.asc(), Task.order_index.asc())
    )
    return list(result.scalars().all())


def _task_by_name(tasks: list[Task], name: str) -> Task:
    for task in tasks:
        if task.name == name:
            return task
    raise AssertionError(f"Task '{name}' not found")


@pytest.mark.asyncio
async def test_indent_moves_task_under_previous_sibling(session: AsyncSession) -> None:
    """Indent moves the task under its immediate previous sibling."""
    project = await _create_project(session, suffix="indent-parent")
    t1 = await _create_task(session, project=project, name="T1", order_index=1)
    t2 = await _create_task(session, project=project, name="T2", order_index=2)

    updated = await task_hierarchy_service.indent_task(session, project, t2)

    assert str(updated.parent_task_id) == str(t1.id)


@pytest.mark.asyncio
async def test_indent_updates_wbs_codes(session: AsyncSession) -> None:
    """Indent triggers WBS regeneration for affected siblings."""
    project = await _create_project(session, suffix="indent-wbs")
    await _create_task(session, project=project, name="T1", order_index=1)
    t2 = await _create_task(session, project=project, name="T2", order_index=2)
    await _create_task(session, project=project, name="T3", order_index=3)

    await task_hierarchy_service.indent_task(session, project, t2)
    tasks = await _list_active_tasks(session, project)

    assert _task_by_name(tasks, "T1").wbs_code == "1"
    assert _task_by_name(tasks, "T2").wbs_code == "1.1"
    assert _task_by_name(tasks, "T3").wbs_code == "2"


@pytest.mark.asyncio
async def test_indent_updates_outline_level(session: AsyncSession) -> None:
    """Indented task gets one deeper outline level."""
    project = await _create_project(session, suffix="indent-outline")
    await _create_task(session, project=project, name="Parent", order_index=1)
    child = await _create_task(session, project=project, name="Child", order_index=2)

    await task_hierarchy_service.indent_task(session, project, child)
    refreshed = await _get_task(session, child.id)

    assert refreshed.outline_level == 2


@pytest.mark.asyncio
async def test_indent_marks_new_parent_as_summary(session: AsyncSession) -> None:
    """Indent marks the new parent as summary when it gains a child."""
    project = await _create_project(session, suffix="indent-summary")
    parent = await _create_task(session, project=project, name="Parent", order_index=1)
    child = await _create_task(session, project=project, name="Child", order_index=2)

    await task_hierarchy_service.indent_task(session, project, child)
    refreshed_parent = await _get_task(session, parent.id)

    assert refreshed_parent.is_summary is True


@pytest.mark.asyncio
async def test_indent_first_task_rejected(session: AsyncSession) -> None:
    """Indenting the first sibling is rejected (no previous sibling)."""
    project = await _create_project(session, suffix="indent-first-reject")
    first = await _create_task(session, project=project, name="First", order_index=1)

    with pytest.raises(InvalidOperationError):
        await task_hierarchy_service.indent_task(session, project, first)


@pytest.mark.asyncio
async def test_indent_preserves_child_subtree(session: AsyncSession) -> None:
    """Indent keeps existing descendants attached to the moved task."""
    project = await _create_project(session, suffix="indent-subtree")
    t1 = await _create_task(session, project=project, name="T1", order_index=1)
    t2 = await _create_task(session, project=project, name="T2", order_index=2)
    child = await _create_task(
        session,
        project=project,
        name="T2-Child",
        order_index=1,
        parent_task_id=t2.id,
        outline_level=2,
        wbs_code="2.1",
    )

    await task_hierarchy_service.indent_task(session, project, t2)
    refreshed_child = await _get_task(session, child.id)
    refreshed_t2 = await _get_task(session, t2.id)

    assert str(refreshed_t2.parent_task_id) == str(t1.id)
    assert str(refreshed_child.parent_task_id) == str(refreshed_t2.id)


@pytest.mark.asyncio
async def test_outdent_moves_task_up_one_level(session: AsyncSession) -> None:
    """Outdent moves task from child level to its grandparent level."""
    project = await _create_project(session, suffix="outdent-up-level")
    parent = await _create_task(session, project=project, name="Parent", order_index=1)
    child = await _create_task(
        session,
        project=project,
        name="Child",
        order_index=1,
        parent_task_id=parent.id,
        outline_level=2,
        wbs_code="1.1",
    )

    updated = await task_hierarchy_service.outdent_task(session, project, child)

    assert updated.parent_task_id is None


@pytest.mark.asyncio
async def test_outdent_reparents_subsequent_siblings_as_children(
    session: AsyncSession,
) -> None:
    """Outdent re-parents following siblings under the moved task."""
    project = await _create_project(session, suffix="outdent-reparent-following")
    parent = await _create_task(session, project=project, name="Parent", order_index=1)
    await _create_task(
        session,
        project=project,
        name="A",
        order_index=1,
        parent_task_id=parent.id,
        outline_level=2,
        wbs_code="1.1",
    )
    moved = await _create_task(
        session,
        project=project,
        name="B",
        order_index=2,
        parent_task_id=parent.id,
        outline_level=2,
        wbs_code="1.2",
    )
    follower = await _create_task(
        session,
        project=project,
        name="C",
        order_index=3,
        parent_task_id=parent.id,
        outline_level=2,
        wbs_code="1.3",
    )

    await task_hierarchy_service.outdent_task(session, project, moved)
    refreshed_follower = await _get_task(session, follower.id)
    refreshed_moved = await _get_task(session, moved.id)

    assert str(refreshed_follower.parent_task_id) == str(refreshed_moved.id)


@pytest.mark.asyncio
async def test_outdent_root_task_rejected(session: AsyncSession) -> None:
    """Outdent rejects root-level tasks."""
    project = await _create_project(session, suffix="outdent-root-reject")
    root = await _create_task(session, project=project, name="Root", order_index=1)

    with pytest.raises(InvalidOperationError):
        await task_hierarchy_service.outdent_task(session, project, root)


@pytest.mark.asyncio
async def test_outdent_updates_wbs_codes(session: AsyncSession) -> None:
    """Outdent regenerates root-level WBS order."""
    project = await _create_project(session, suffix="outdent-wbs")
    parent = await _create_task(session, project=project, name="Parent", order_index=1)
    child = await _create_task(
        session,
        project=project,
        name="Child",
        order_index=1,
        parent_task_id=parent.id,
        outline_level=2,
        wbs_code="1.1",
    )
    await _create_task(session, project=project, name="Root2", order_index=2)

    await task_hierarchy_service.outdent_task(session, project, child)
    tasks = await _list_active_tasks(session, project)

    assert _task_by_name(tasks, "Parent").wbs_code == "1"
    assert _task_by_name(tasks, "Child").wbs_code == "2"
    assert _task_by_name(tasks, "Root2").wbs_code == "3"


@pytest.mark.asyncio
async def test_reorder_within_same_parent(session: AsyncSession) -> None:
    """Reorder in one sibling group updates order indexes deterministically."""
    project = await _create_project(session, suffix="reorder-same-parent")
    a = await _create_task(session, project=project, name="A", order_index=1)
    await _create_task(session, project=project, name="B", order_index=2)
    c = await _create_task(session, project=project, name="C", order_index=3)

    await task_hierarchy_service.reorder_task(
        session,
        project,
        c,
        after_task_id=a.id,
        before_task_id=None,
        new_parent_id=None,
    )
    tasks = await _list_active_tasks(session, project)

    assert _task_by_name(tasks, "A").order_index == 1
    assert _task_by_name(tasks, "C").order_index == 2
    assert _task_by_name(tasks, "B").order_index == 3


@pytest.mark.asyncio
async def test_reorder_to_different_parent(session: AsyncSession) -> None:
    """Reorder with new_parent_id moves task under the target parent."""
    project = await _create_project(session, suffix="reorder-new-parent")
    parent = await _create_task(session, project=project, name="Parent", order_index=1)
    child = await _create_task(session, project=project, name="Child", order_index=2)

    await task_hierarchy_service.reorder_task(
        session,
        project,
        child,
        after_task_id=None,
        before_task_id=None,
        new_parent_id=parent.id,
    )
    refreshed_parent = await _get_task(session, parent.id)
    refreshed_child = await _get_task(session, child.id)

    assert str(refreshed_child.parent_task_id) == str(parent.id)
    assert refreshed_child.order_index == 1
    assert refreshed_parent.is_summary is True


@pytest.mark.asyncio
async def test_reorder_descendant_under_self_rejected(
    session: AsyncSession,
) -> None:
    """Reorder rejects moving a task under one of its descendants."""
    project = await _create_project(session, suffix="reorder-descendant-reject")
    root = await _create_task(session, project=project, name="Root", order_index=1)
    child = await _create_task(
        session,
        project=project,
        name="Child",
        order_index=1,
        parent_task_id=root.id,
        outline_level=2,
        wbs_code="1.1",
    )
    grandchild = await _create_task(
        session,
        project=project,
        name="Grandchild",
        order_index=1,
        parent_task_id=child.id,
        outline_level=3,
        wbs_code="1.1.1",
    )

    with pytest.raises(InvalidOperationError):
        await task_hierarchy_service.reorder_task(
            session,
            project,
            root,
            after_task_id=None,
            before_task_id=None,
            new_parent_id=grandchild.id,
        )


@pytest.mark.asyncio
async def test_deep_nesting_5_levels_correct_outline_levels(
    session: AsyncSession,
) -> None:
    """A 5-level chain keeps correct outline levels and WBS hierarchy."""
    project = await _create_project(session, suffix="deep-nesting-5-levels")
    a = await _create_task(session, project=project, name="A", order_index=1)
    b = await _create_task(session, project=project, name="B", order_index=2)
    c = await _create_task(session, project=project, name="C", order_index=3)
    d = await _create_task(session, project=project, name="D", order_index=4)
    e = await _create_task(session, project=project, name="E", order_index=5)

    await task_hierarchy_service.reorder_task(
        session,
        project,
        b,
        after_task_id=None,
        before_task_id=None,
        new_parent_id=a.id,
    )
    await task_hierarchy_service.reorder_task(
        session,
        project,
        c,
        after_task_id=None,
        before_task_id=None,
        new_parent_id=b.id,
    )
    await task_hierarchy_service.reorder_task(
        session,
        project,
        d,
        after_task_id=None,
        before_task_id=None,
        new_parent_id=c.id,
    )
    await task_hierarchy_service.reorder_task(
        session,
        project,
        e,
        after_task_id=None,
        before_task_id=None,
        new_parent_id=d.id,
    )
    tasks = await _list_active_tasks(session, project)

    assert _task_by_name(tasks, "A").outline_level == 1
    assert _task_by_name(tasks, "B").outline_level == 2
    assert _task_by_name(tasks, "C").outline_level == 3
    assert _task_by_name(tasks, "D").outline_level == 4
    assert _task_by_name(tasks, "E").outline_level == 5
    assert _task_by_name(tasks, "A").wbs_code == "1"
    assert _task_by_name(tasks, "B").wbs_code == "1.1"
    assert _task_by_name(tasks, "C").wbs_code == "1.1.1"
    assert _task_by_name(tasks, "D").wbs_code == "1.1.1.1"
    assert _task_by_name(tasks, "E").wbs_code == "1.1.1.1.1"
