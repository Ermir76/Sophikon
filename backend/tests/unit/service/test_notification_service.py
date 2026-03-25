import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.project_invitation import ProjectInvitation
from app.models.role import Role
from app.models.user import User
from app.service import notification_service, realtime_service


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


async def _create_project(client: AsyncClient, slug: str) -> str:
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Notification Service Org",
            "slug": slug,
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Notification Service Project",
            "organization_id": org_id,
            "start_date": "2026-03-25",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


@pytest.mark.asyncio
async def test_create_mark_read_and_mark_all_queue_user_notification_events(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-service@example.com", "Notif Service")
    user_result = await session.execute(
        select(User).where(User.email == "notif-service@example.com")
    )
    user = user_result.scalar_one()

    realtime_service.clear_pending_events(session)
    notification = await notification_service.create_notification(
        session,
        user_id=user.id,
        type=NotificationType.MENTIONED,
        title="Mentioned",
        entity_type="comment",
        entity_id=uuid.uuid4(),
    )
    pending = session.info[realtime_service.PENDING_USER_NOTIFICATION_EVENTS_KEY]
    assert pending[-1]["payload"]["type"] == "notification_created"
    assert pending[-1]["payload"]["unread_count"] == 1

    await notification_service.mark_read(
        session,
        notification_id=notification.id,
        user_id=user.id,
    )
    pending = session.info[realtime_service.PENDING_USER_NOTIFICATION_EVENTS_KEY]
    assert pending[-1]["payload"]["type"] == "notification_updated"
    assert pending[-1]["payload"]["is_read"] is True
    assert pending[-1]["payload"]["unread_count"] == 0

    await notification_service.mark_all_read(session, user_id=user.id)
    pending = session.info[realtime_service.PENDING_USER_NOTIFICATION_EVENTS_KEY]
    assert pending[-1]["payload"]["type"] == "notifications_read_all"
    assert pending[-1]["payload"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_resolved_project_invitation_notifications_are_hidden_and_unread_count_drops(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "notif-hidden@example.com", "Notif Hidden")
    project_id = await _create_project(client, "notif-service-hidden-org")
    user_result = await session.execute(
        select(User).where(User.email == "notif-hidden@example.com")
    )
    user = user_result.scalar_one()
    role_result = await session.execute(select(Role).where(Role.name == "member"))
    role = role_result.scalar_one()

    invitation = ProjectInvitation(
        invited_by_id=user.id,
        project_id=uuid.UUID(project_id),
        role_id=role.id,
        email=user.email,
        token_hash="token-hash",
        expires_at=datetime.now(UTC),
        accepted_at=datetime.now(UTC),
        is_revoked=False,
    )
    session.add(invitation)
    await session.flush()

    session.add(
        Notification(
            user_id=user.id,
            type=NotificationType.INVITATION_RECEIVED,
            title="Invited to Hidden Project",
            entity_type="project_invitation",
            entity_id=invitation.id,
        )
    )
    await session.commit()

    items, total, unread_count = await notification_service.list_notifications(
        session,
        user_id=user.id,
    )

    assert items == []
    assert total == 0
    assert unread_count == 0
