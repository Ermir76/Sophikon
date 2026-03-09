import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
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
