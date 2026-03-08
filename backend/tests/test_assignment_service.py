import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.schema.assignment import AssignmentCreate
from app.service import assignment_service
from app.service.activity_log_service import ActivityContext


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


async def _create_project_task_resource(client: AsyncClient) -> tuple[str, str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Assignment Service Org",
            "slug": f"assignment-service-org-{uuid.uuid4().hex[:8]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Assignment Service Project",
            "organization_id": org_id,
            "start_date": "2026-03-08",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Assignment Service Task",
            "start_date": "2026-03-08",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Assignment Service Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    return project_id, task_id, resource_id


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


async def _get_task(session: AsyncSession, task_id: str) -> Task:
    result = await session.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    assert task is not None
    return task


@pytest.mark.asyncio
async def test_create_assignment_notifies_mapped_resource_user(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "assignment-owner@example.com", "Assignment Owner")
    await _register(client, "assignment-assignee@example.com", "Assignment Assignee")
    await _login(client, "assignment-owner@example.com")

    _, task_id, resource_id = await _create_project_task_resource(client)
    owner = await _get_user(session, "assignment-owner@example.com")
    assignee = await _get_user(session, "assignment-assignee@example.com")

    resource_result = await session.execute(
        select(Resource).where(Resource.id == uuid.UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = assignee.id
    await session.commit()

    task = await _get_task(session, task_id)
    assignment = await assignment_service.create_assignment(
        session,
        task,
        AssignmentCreate(
            resource_id=uuid.UUID(resource_id),
            units=1.0,
            start_date=date(2026, 3, 8),
            finish_date=date(2026, 3, 8),
        ),
        activity_context=ActivityContext(
            user_id=owner.id,
            full_name=owner.full_name,
            avatar_url=owner.avatar_url,
        ),
    )
    assert assignment.id is not None

    notification_result = await session.execute(
        select(Notification).where(
            Notification.user_id == assignee.id,
            Notification.type == NotificationType.TASK_ASSIGNED,
            Notification.entity_type == "task",
            Notification.entity_id == task.id,
        )
    )
    notification = notification_result.scalar_one_or_none()
    assert notification is not None


@pytest.mark.asyncio
async def test_create_assignment_skips_notification_when_actor_is_assignee(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "assignment-self@example.com", "Assignment Self")
    await _login(client, "assignment-self@example.com")

    _, task_id, resource_id = await _create_project_task_resource(client)
    owner = await _get_user(session, "assignment-self@example.com")

    resource_result = await session.execute(
        select(Resource).where(Resource.id == uuid.UUID(resource_id))
    )
    resource = resource_result.scalar_one_or_none()
    assert resource is not None
    resource.user_id = owner.id
    await session.commit()

    task = await _get_task(session, task_id)
    assignment = await assignment_service.create_assignment(
        session,
        task,
        AssignmentCreate(
            resource_id=uuid.UUID(resource_id),
            units=1.0,
            start_date=date(2026, 3, 8),
            finish_date=date(2026, 3, 8),
        ),
        activity_context=ActivityContext(
            user_id=owner.id,
            full_name=owner.full_name,
            avatar_url=owner.avatar_url,
        ),
    )
    assert assignment.id is not None

    notification_result = await session.execute(
        select(Notification).where(
            Notification.user_id == owner.id,
            Notification.type == NotificationType.TASK_ASSIGNED,
            Notification.entity_type == "task",
            Notification.entity_id == task.id,
        )
    )
    notifications = list(notification_result.scalars().all())
    assert notifications == []
