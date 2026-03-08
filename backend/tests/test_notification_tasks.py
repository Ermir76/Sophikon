from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.user import User
from app.tasks.notification_tasks import enqueue_deadline_approaching_notifications


async def _register(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200, response.text


async def _create_project(client: AsyncClient, *, slug: str, start_date: str) -> str:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Deadline Project",
            "organization_id": org_id,
            "start_date": start_date,
            "settings": {"auto_calculate": False},
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


async def _create_task(client: AsyncClient, project_id: str, *, start_date: str) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"name": f"Task {start_date}", "start_date": start_date, "duration": 480},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_resource(client: AsyncClient, project_id: str, *, name: str) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": name, "max_units": 1.0},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _assign_resource(
    client: AsyncClient,
    project_id: str,
    task_id: str,
    resource_id: str,
    *,
    start_date: str,
    finish_date: str,
) -> None:
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.0,
            "start_date": start_date,
            "finish_date": finish_date,
        },
    )
    assert response.status_code == 201, response.text


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


@pytest.mark.asyncio
async def test_deadline_task_creates_notifications_and_dedupes_same_day(
    client: AsyncClient,
    session: AsyncSession,
):
    now = datetime.now(UTC).replace(microsecond=0)
    in_window_start = now.date().isoformat()

    await _register(client, "deadline-owner@example.com", "Deadline Owner")
    await _register(client, "deadline-assignee@example.com", "Deadline Assignee")
    await _login(client, "deadline-owner@example.com")
    assignee = await _get_user(session, "deadline-assignee@example.com")

    project_id = await _create_project(
        client,
        slug="deadline-org-a",
        start_date=in_window_start,
    )
    task_id = await _create_task(client, project_id, start_date=in_window_start)
    resource_id = await _create_resource(client, project_id, name="Mapped Resource")
    await _assign_resource(
        client,
        project_id,
        task_id,
        resource_id,
        start_date=in_window_start,
        finish_date=in_window_start,
    )

    resource_result = await session.execute(
        select(Resource).where(Resource.id == UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = assignee.id
    await session.commit()

    first_count = await enqueue_deadline_approaching_notifications(now=now, db=session)
    second_count = await enqueue_deadline_approaching_notifications(now=now, db=session)

    assert first_count == 1
    assert second_count == 0
    notif_result = await session.execute(
        select(Notification).where(
            Notification.user_id == assignee.id,
            Notification.type == NotificationType.DEADLINE_APPROACHING,
            Notification.entity_type == "task",
        )
    )
    notifications = list(notif_result.scalars().all())
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_deadline_task_skips_out_of_window_completed_deleted_and_unlinked(
    client: AsyncClient,
    session: AsyncSession,
):
    now = datetime.now(UTC).replace(microsecond=0)
    in_window_start = now.date().isoformat()
    out_of_window_start = (now.date() + timedelta(days=14)).isoformat()

    await _register(client, "deadline-owner-b@example.com", "Deadline Owner")
    await _register(client, "deadline-assignee-b@example.com", "Deadline Assignee")
    await _login(client, "deadline-owner-b@example.com")
    assignee = await _get_user(session, "deadline-assignee-b@example.com")

    project_id = await _create_project(
        client,
        slug="deadline-org-b",
        start_date=in_window_start,
    )

    in_window_task = await _create_task(client, project_id, start_date=in_window_start)
    out_of_window_task = await _create_task(
        client, project_id, start_date=out_of_window_start
    )
    completed_task = await _create_task(client, project_id, start_date=in_window_start)
    deleted_task = await _create_task(client, project_id, start_date=in_window_start)

    for task_id, name, assignment_date in [
        (in_window_task, "In Window", in_window_start),
        (out_of_window_task, "Out Window", out_of_window_start),
        (completed_task, "Completed", in_window_start),
        (deleted_task, "Deleted", in_window_start),
    ]:
        resource_id = await _create_resource(client, project_id, name=name)
        await _assign_resource(
            client,
            project_id,
            task_id,
            resource_id,
            start_date=assignment_date,
            finish_date=assignment_date,
        )
        result = await session.execute(
            select(Resource).where(Resource.id == UUID(resource_id))
        )
        resource = result.scalar_one_or_none()
        assert resource is not None
        if name != "Out Window":
            resource.user_id = assignee.id

    complete_response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{completed_task}",
        json={"percent_complete": 100},
    )
    assert complete_response.status_code == 200, complete_response.text
    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{deleted_task}"
    )
    assert delete_response.status_code == 204, delete_response.text

    count = await enqueue_deadline_approaching_notifications(
        now=now,
        db=session,
    )

    assert count == 1
    notif_result = await session.execute(
        select(Notification).where(
            Notification.user_id == assignee.id,
            Notification.type == NotificationType.DEADLINE_APPROACHING,
        )
    )
    notifications = list(notif_result.scalars().all())
    assert len(notifications) == 1
    assert str(notifications[0].entity_id) == in_window_task
