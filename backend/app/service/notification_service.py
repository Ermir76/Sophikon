"""
Notification business logic.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import UUID as UUIDUtils

from app.core.exceptions import NotFoundError
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.repository import notification_repo
from app.service import realtime_service

DEFAULT_NOTIFICATION_SETTINGS = {
    "email_task_assigned": True,
    "email_mentioned": True,
    "email_deadline_approaching": True,
    "push_enabled": False,
}
_SETTINGS_KEY = "notification_settings"
_UUID_ENCODERS = {UUIDUtils: lambda value: UUID(bytes=value.bytes)}


def _encode_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return jsonable_encoder(payload, custom_encoder=_UUID_ENCODERS)


def _notification_to_payload(
    *,
    notification: Notification,
    actor_id: UUID | None = None,
    actor_full_name: str | None = None,
    actor_avatar_url: str | None = None,
) -> dict[str, Any]:
    actor = None
    if actor_id is not None:
        actor = {
            "id": actor_id,
            "full_name": actor_full_name,
            "avatar_url": actor_avatar_url,
        }

    return _encode_payload(
        {
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "actor": actor,
            "is_read": notification.is_read,
            "read_at": notification.read_at,
            "created_at": notification.created_at,
        }
    )


async def get_unread_count(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> int:
    return await notification_repo.count_unread(db, user_id=user_id)


async def build_snapshot_payload(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> dict:
    unread_count = await get_unread_count(db, user_id=user_id)
    return {"type": "notification_snapshot", "unread_count": unread_count}


async def list_notifications(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
) -> tuple[list[notification_repo.NotificationRow], int, int]:
    items, total = await notification_repo.list_with_actor(
        db,
        user_id=user_id,
        page=page,
        per_page=per_page,
        unread_only=unread_only,
    )
    unread_count = await get_unread_count(db, user_id=user_id)
    return items, total, unread_count


async def get_notification_by_id(
    db: AsyncSession,
    *,
    user_id: UUID,
    notification_id: UUID,
) -> notification_repo.NotificationRow:
    row = await notification_repo.get_with_actor_by_id(
        db,
        user_id=user_id,
        notification_id=notification_id,
    )
    if row is None:
        raise NotFoundError("Notification not found")
    return row


async def create_notification(
    db: AsyncSession,
    *,
    user_id: UUID,
    type: NotificationType,
    title: str,
    message: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
) -> Notification:
    notification = await notification_repo.create_notification(
        db,
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
    )

    actor_id_value = actor_id
    actor_name: str | None = None
    actor_avatar: str | None = None
    if actor_id_value is not None:
        actor_profile = await notification_repo.get_actor_profile(
            db,
            actor_id=actor_id_value,
        )
        if actor_profile is not None:
            actor_name, actor_avatar = actor_profile

    unread_count = await get_unread_count(db, user_id=user_id)
    realtime_service.queue_user_notification_event(
        db,
        user_id=user_id,
        payload={
            "type": "notification_created",
            "notification": _notification_to_payload(
                notification=notification,
                actor_id=actor_id_value,
                actor_full_name=actor_name,
                actor_avatar_url=actor_avatar,
            ),
            "unread_count": unread_count,
        },
    )
    return notification


async def mark_read(
    db: AsyncSession,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> notification_repo.NotificationRow:
    row = await notification_repo.get_with_actor_by_id(
        db,
        user_id=user_id,
        notification_id=notification_id,
    )
    if row is None:
        raise NotFoundError("Notification not found")
    notification = row.notification

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await db.flush()

    unread_count = await get_unread_count(db, user_id=user_id)
    realtime_service.queue_user_notification_event(
        db,
        user_id=user_id,
        payload=_encode_payload(
            {
                "type": "notification_updated",
                "notification_id": notification.id,
                "is_read": notification.is_read,
                "read_at": notification.read_at,
                "unread_count": unread_count,
            }
        ),
    )
    return row


async def mark_all_read(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> tuple[int, int]:
    notifications = await notification_repo.list_unread_for_user(
        db,
        user_id=user_id,
    )
    if notifications:
        read_at = datetime.now(UTC)
        for notification in notifications:
            notification.is_read = True
            notification.read_at = read_at
        await db.flush()

    unread_count = await get_unread_count(db, user_id=user_id)
    realtime_service.queue_user_notification_event(
        db,
        user_id=user_id,
        payload={
            "type": "notifications_read_all",
            "unread_count": unread_count,
        },
    )
    return len(notifications), unread_count


def get_settings(user: User) -> dict[str, bool]:
    preferences = user.preferences if isinstance(user.preferences, dict) else {}
    raw = preferences.get(_SETTINGS_KEY, {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        "email_task_assigned": bool(
            raw.get(
                "email_task_assigned",
                DEFAULT_NOTIFICATION_SETTINGS["email_task_assigned"],
            )
        ),
        "email_mentioned": bool(
            raw.get(
                "email_mentioned",
                DEFAULT_NOTIFICATION_SETTINGS["email_mentioned"],
            )
        ),
        "email_deadline_approaching": bool(
            raw.get(
                "email_deadline_approaching",
                DEFAULT_NOTIFICATION_SETTINGS["email_deadline_approaching"],
            )
        ),
        "push_enabled": bool(
            raw.get("push_enabled", DEFAULT_NOTIFICATION_SETTINGS["push_enabled"])
        ),
    }


def update_settings(user: User, patch: dict[str, bool]) -> dict[str, bool]:
    current = get_settings(user)
    next_settings = {
        **current,
        **patch,
    }

    preferences = dict(user.preferences or {})
    preferences[_SETTINGS_KEY] = next_settings
    user.preferences = preferences
    return next_settings
