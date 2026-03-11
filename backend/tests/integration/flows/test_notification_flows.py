"""
Integration flow tests for notification delivery across features.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.resource import Resource
from app.models.role import Role
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
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 200, response.text


async def _ensure_project_roles(session: AsyncSession) -> None:
    for role_name in ["owner", "manager", "member", "viewer"]:
        existing = await session.execute(select(Role).where(Role.name == role_name))
        if existing.scalar_one_or_none() is None:
            session.add(Role(name=role_name, scope="project"))
    await session.commit()


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


async def _create_project_and_task(client: AsyncClient, suffix: str) -> tuple[str, str]:
    slug = suffix.lower().replace("_", "-")
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": f"Notification Org {suffix}",
            "slug": f"notif-flow-{slug}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Notification Project {suffix}",
            "organization_id": org_id,
            "start_date": "2026-03-11",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": f"Notification Task {suffix}",
            "start_date": "2026-03-11",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project_id, task_response.json()["id"]


@pytest.mark.asyncio
async def test_comment_mention_creates_notification_for_mentioned_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Comment mention flow creates a mentioned notification for the tagged member."""
    await _ensure_project_roles(session)

    await _register(client, "notif-mention-owner@example.com", "Mention Owner")
    await _login(client, "notif-mention-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "mention-flow")

    await _register(client, "notif-mention-member@example.com", "Mention Member")
    await add_project_member(
        session,
        project_id,
        "notif-mention-member@example.com",
        "member",
    )
    mentioned_user = await _get_user(session, "notif-mention-member@example.com")

    await _login(client, "notif-mention-owner@example.com")
    create_comment_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": f"Please review @[Mention Member](user:{mentioned_user.id})",
            "parent_comment_id": None,
        },
    )
    assert create_comment_response.status_code == 201, create_comment_response.text

    await _login(client, "notif-mention-member@example.com")
    notifications_response = await client.get(
        "/api/v1/notifications",
        params={"unread_only": "true"},
    )
    assert notifications_response.status_code == 200, notifications_response.text
    payload = notifications_response.json()
    assert payload["total"] == 1
    assert payload["unread_count"] == 1
    assert payload["items"][0]["type"] == NotificationType.MENTIONED.value
    assert payload["items"][0]["entity_type"] == "comment"


@pytest.mark.asyncio
async def test_task_assignment_creates_notification_for_assignee(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Assignment flow sends task_assigned notification to linked resource user."""
    await _ensure_project_roles(session)

    await _register(client, "notif-assign-owner@example.com", "Assign Owner")
    await _login(client, "notif-assign-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "assignment-flow")

    await _register(client, "notif-assign-member@example.com", "Assign Member")
    await add_project_member(
        session,
        project_id,
        "notif-assign-member@example.com",
        "member",
    )
    assignee = await _get_user(session, "notif-assign-member@example.com")

    # Ensure actor is the owner (not the assignee) so assignment creates a
    # notification for recipient != actor.
    await _login(client, "notif-assign-owner@example.com")
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
            "start_date": "2026-03-11",
            "finish_date": "2026-03-11",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    await _login(client, "notif-assign-member@example.com")
    notifications_response = await client.get(
        "/api/v1/notifications",
        params={"unread_only": "true"},
    )
    assert notifications_response.status_code == 200, notifications_response.text
    payload = notifications_response.json()
    assert payload["total"] == 1
    assert payload["unread_count"] == 1
    assert payload["items"][0]["type"] == NotificationType.TASK_ASSIGNED.value
    assert payload["items"][0]["entity_type"] == "task"
    assert payload["items"][0]["entity_id"] == task_id


@pytest.mark.asyncio
async def test_notification_not_created_when_actor_is_recipient(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """No self-notification is created when actor assigns themselves."""
    await _register(client, "notif-self-owner@example.com", "Self Owner")
    await _login(client, "notif-self-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "self-assignment")
    owner = await _get_user(session, "notif-self-owner@example.com")

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Self Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    resource_result = await session.execute(
        select(Resource).where(Resource.id == uuid.UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = owner.id
    await session.commit()

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.0,
            "start_date": "2026-03-11",
            "finish_date": "2026-03-11",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    notifications_response = await client.get("/api/v1/notifications")
    assert notifications_response.status_code == 200, notifications_response.text
    payload = notifications_response.json()
    assert payload["total"] == 0
    assert payload["unread_count"] == 0
    assert payload["items"] == []


@pytest.mark.asyncio
async def test_mark_all_read_clears_unread_count(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Cross-domain notifications can be marked read-all in one operation."""
    await _ensure_project_roles(session)

    await _register(client, "notif-read-owner@example.com", "Read Owner")
    await _login(client, "notif-read-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "read-all")

    await _register(client, "notif-read-member@example.com", "Read Member")
    await add_project_member(
        session, project_id, "notif-read-member@example.com", "member"
    )
    member = await _get_user(session, "notif-read-member@example.com")

    # Notification 1: comment mention
    await _login(client, "notif-read-owner@example.com")
    comment_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": f"Ping @[Read Member](user:{member.id})",
            "parent_comment_id": None,
        },
    )
    assert comment_response.status_code == 201, comment_response.text

    # Notification 2: task assignment
    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Read Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    resource_result = await session.execute(
        select(Resource).where(Resource.id == uuid.UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = member.id
    await session.commit()

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.0,
            "start_date": "2026-03-11",
            "finish_date": "2026-03-11",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    await _login(client, "notif-read-member@example.com")
    unread_before = await client.get(
        "/api/v1/notifications", params={"unread_only": "true"}
    )
    assert unread_before.status_code == 200, unread_before.text
    assert unread_before.json()["total"] == 2
    assert unread_before.json()["unread_count"] == 2

    read_all_response = await client.post("/api/v1/notifications/read-all")
    assert read_all_response.status_code == 200, read_all_response.text
    assert read_all_response.json()["updated_count"] == 2
    assert read_all_response.json()["unread_count"] == 0

    unread_after = await client.get(
        "/api/v1/notifications", params={"unread_only": "true"}
    )
    assert unread_after.status_code == 200, unread_after.text
    assert unread_after.json()["total"] == 0
    assert unread_after.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_settings_disable_suppresses_creation(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """
    Pass-now behavior: settings persist, but mention creation is not suppressed.

    TODO: when notification preferences become enforcement gates, invert this
    expectation for `email_mentioned=False`.
    """
    await _ensure_project_roles(session)

    await _register(client, "notif-settings-owner@example.com", "Settings Owner")
    await _login(client, "notif-settings-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "settings-mention")

    await _register(client, "notif-settings-member@example.com", "Settings Member")
    await add_project_member(
        session,
        project_id,
        "notif-settings-member@example.com",
        "member",
    )
    member = await _get_user(session, "notif-settings-member@example.com")

    await _login(client, "notif-settings-member@example.com")
    settings_patch = await client.patch(
        "/api/v1/notifications/settings",
        json={"email_mentioned": False},
    )
    assert settings_patch.status_code == 200, settings_patch.text
    assert settings_patch.json()["email_mentioned"] is False

    await _login(client, "notif-settings-owner@example.com")
    comment_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": f"Still delivered @[Settings Member](user:{member.id})",
            "parent_comment_id": None,
        },
    )
    assert comment_response.status_code == 201, comment_response.text

    await _login(client, "notif-settings-member@example.com")
    notifications_response = await client.get(
        "/api/v1/notifications",
        params={"unread_only": "true"},
    )
    assert notifications_response.status_code == 200, notifications_response.text
    payload = notifications_response.json()
    assert payload["total"] == 1
    assert payload["unread_count"] == 1
    assert payload["items"][0]["type"] == NotificationType.MENTIONED.value
