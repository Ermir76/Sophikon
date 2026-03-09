import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.user import User
from tests.fixtures.project_members import add_project_member


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


async def _create_project_and_task(client: AsyncClient) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Notifications Org",
            "slug": f"notifications-org-{uuid.uuid4().hex[:8]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Notifications Project",
            "organization_id": org_id,
            "start_date": "2026-03-08",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Notification Task",
            "start_date": "2026-03-08",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project_id, task_response.json()["id"]


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


@pytest.mark.asyncio
async def test_list_and_read_notifications_with_unread_count(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-list@example.com", "Notif List")
    await _login(client, "notif-list@example.com")
    user = await _get_user(session, "notif-list@example.com")

    session.add_all(
        [
            Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.MENTIONED,
                title="Mention one",
                entity_type="comment",
                entity_id=uuid.uuid4(),
            ),
            Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.TASK_ASSIGNED,
                title="Assigned",
                entity_type="task",
                entity_id=uuid.uuid4(),
                is_read=True,
            ),
            Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.MENTIONED,
                title="Mention two",
                entity_type="comment",
                entity_id=uuid.uuid4(),
            ),
        ]
    )
    await session.commit()

    list_response = await client.get("/api/v1/notifications")
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()
    assert payload["total"] == 3
    assert payload["unread_count"] == 2

    unread_only_response = await client.get(
        "/api/v1/notifications",
        params={"unread_only": "true"},
    )
    assert unread_only_response.status_code == 200, unread_only_response.text
    unread_payload = unread_only_response.json()
    assert unread_payload["total"] == 2
    assert all(item["is_read"] is False for item in unread_payload["items"])

    notification_id = unread_payload["items"][0]["id"]
    mark_response = await client.patch(f"/api/v1/notifications/{notification_id}/read")
    assert mark_response.status_code == 200, mark_response.text
    assert mark_response.json()["is_read"] is True

    after_response = await client.get("/api/v1/notifications")
    assert after_response.status_code == 200, after_response.text
    assert after_response.json()["unread_count"] == 1


@pytest.mark.asyncio
async def test_mark_read_enforces_notification_ownership(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-owner-a@example.com", "Owner A")
    await _register(client, "notif-owner-b@example.com", "Owner B")
    await _login(client, "notif-owner-a@example.com")
    user_a = await _get_user(session, "notif-owner-a@example.com")

    notification = Notification(
        user_id=user_a.id,
        type=NotificationType.MENTIONED,
        title="Private",
        entity_type="comment",
        entity_id=uuid.uuid4(),
    )
    session.add(notification)
    await session.commit()

    await _login(client, "notif-owner-b@example.com")
    response = await client.patch(f"/api/v1/notifications/{notification.id}/read")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read_is_idempotent(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-read-all@example.com", "Read All")
    await _login(client, "notif-read-all@example.com")
    user = await _get_user(session, "notif-read-all@example.com")

    session.add_all(
        [
            Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.MENTIONED,
                title="Unread one",
                entity_type="comment",
                entity_id=uuid.uuid4(),
            ),
            Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.MENTIONED,
                title="Unread two",
                entity_type="comment",
                entity_id=uuid.uuid4(),
            ),
        ]
    )
    await session.commit()

    first = await client.post("/api/v1/notifications/read-all")
    assert first.status_code == 200, first.text
    assert first.json()["updated_count"] == 2
    assert first.json()["unread_count"] == 0

    second = await client.post("/api/v1/notifications/read-all")
    assert second.status_code == 200, second.text
    assert second.json()["updated_count"] == 0
    assert second.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_settings_defaults_and_partial_update(
    client: AsyncClient,
):
    await _register(client, "notif-settings@example.com", "Settings User")
    await _login(client, "notif-settings@example.com")

    default_response = await client.get("/api/v1/notifications/settings")
    assert default_response.status_code == 200, default_response.text
    assert default_response.json() == {
        "email_task_assigned": True,
        "email_mentioned": True,
        "email_deadline_approaching": True,
        "push_enabled": False,
    }

    patch_response = await client.patch(
        "/api/v1/notifications/settings",
        json={"push_enabled": True, "email_mentioned": False},
    )
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json() == {
        "email_task_assigned": True,
        "email_mentioned": False,
        "email_deadline_approaching": True,
        "push_enabled": True,
    }

    after_response = await client.get("/api/v1/notifications/settings")
    assert after_response.status_code == 200, after_response.text
    assert after_response.json() == {
        "email_task_assigned": True,
        "email_mentioned": False,
        "email_deadline_approaching": True,
        "push_enabled": True,
    }


@pytest.mark.asyncio
async def test_notification_settings_rejects_explicit_null(
    client: AsyncClient,
):
    await _register(client, "notif-settings-null@example.com", "Settings Null")
    await _login(client, "notif-settings-null@example.com")

    response = await client.patch(
        "/api/v1/notifications/settings",
        json={"email_mentioned": None},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_assignment_create_emits_task_assigned_notification_for_linked_user(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    await _register(client, "notif-assignment-owner@example.com", "Assignment Owner")
    await _login(client, "notif-assignment-owner@example.com")
    project_id, task_id = await _create_project_and_task(client)

    await _register(client, "notif-assignee@example.com", "Assignee User")
    await add_project_member(
        session, project_id, "notif-assignee@example.com", "member"
    )
    assignee = await _get_user(session, "notif-assignee@example.com")
    await _login(client, "notif-assignment-owner@example.com")

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Assigned Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    resource_result = await session.execute(
        select(Resource).where(Resource.id == uuid.UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = assignee.id
    await session.commit()

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.0,
            "start_date": "2026-03-08",
            "finish_date": "2026-03-08",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    notif_result = await session.execute(
        select(Notification).where(
            Notification.user_id == assignee.id,
            Notification.type == NotificationType.TASK_ASSIGNED,
            Notification.entity_type == "task",
            Notification.entity_id == uuid.UUID(task_id),
        )
    )
    notification = notif_result.scalar_one_or_none()
    assert notification is not None


@pytest.mark.asyncio
async def test_assignment_create_skips_task_assigned_notification_for_unlinked_resource(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-unlinked-owner@example.com", "Unlinked Owner")
    await _login(client, "notif-unlinked-owner@example.com")
    project_id, task_id = await _create_project_and_task(client)
    owner = await _get_user(session, "notif-unlinked-owner@example.com")

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Unlinked Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_response.json()["id"],
            "units": 1.0,
            "start_date": "2026-03-08",
            "finish_date": "2026-03-08",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    notif_result = await session.execute(
        select(Notification).where(
            Notification.user_id == owner.id,
            Notification.type == NotificationType.TASK_ASSIGNED,
        )
    )
    notifications = list(notif_result.scalars().all())
    assert notifications == []
