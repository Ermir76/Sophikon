"""
Notification business logic.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.schema.notification import (
    NotificationActor,
    NotificationItem,
    NotificationSettings,
    NotificationSettingsUpdate,
)
from app.schema.realtime import (
    NotificationCreatedMessage,
    NotificationSnapshotMessage,
    NotificationsReadAllMessage,
    NotificationUpdatedMessage,
)
from app.service import realtime_service

DEFAULT_NOTIFICATION_SETTINGS = NotificationSettings()
_SETTINGS_KEY = "notification_settings"


def _notification_query_for_user(user_id: UUID) -> Select[tuple[Notification]]:
    return select(Notification).where(Notification.user_id == user_id)


def _to_item(
    notification: Notification,
    *,
    actor_id: UUID | None = None,
    actor_full_name: str | None = None,
    actor_avatar_url: str | None = None,
) -> NotificationItem:
    actor = None
    if actor_id is not None:
        actor = NotificationActor(
            id=actor_id,
            full_name=actor_full_name,
            avatar_url=actor_avatar_url,
        )

    return NotificationItem(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        actor=actor,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


async def get_unread_count(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return int(result.scalar() or 0)


async def build_snapshot_payload(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> dict:
    unread_count = await get_unread_count(db, user_id=user_id)
    return NotificationSnapshotMessage(unread_count=unread_count).model_dump(
        mode="json"
    )


async def list_notifications(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
) -> tuple[list[NotificationItem], int, int]:
    filters = [Notification.user_id == user_id]
    if unread_only:
        filters.append(Notification.is_read == False)  # noqa: E712

    count_query = select(func.count()).select_from(
        select(Notification.id).where(*filters).subquery()
    )
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    unread_count = await get_unread_count(db, user_id=user_id)
    offset = (page - 1) * per_page
    rows = await db.execute(
        select(Notification, User.id, User.full_name, User.avatar_url)
        .outerjoin(User, User.id == Notification.actor_id)
        .where(*filters)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    items = [
        _to_item(
            notification,
            actor_id=actor_id,
            actor_full_name=actor_name,
            actor_avatar_url=avatar_url,
        )
        for notification, actor_id, actor_name, avatar_url in rows.all()
    ]
    return items, total, unread_count


async def get_notification_item_by_id(
    db: AsyncSession,
    *,
    user_id: UUID,
    notification_id: UUID,
) -> NotificationItem:
    row = await db.execute(
        select(Notification, User.id, User.full_name, User.avatar_url)
        .outerjoin(User, User.id == Notification.actor_id)
        .where(
            Notification.user_id == user_id,
            Notification.id == notification_id,
        )
    )
    result = row.one_or_none()
    if result is None:
        raise NotFoundError("Notification not found")
    notification, actor_id, actor_name, actor_avatar_url = result
    return _to_item(
        notification,
        actor_id=actor_id,
        actor_full_name=actor_name,
        actor_avatar_url=actor_avatar_url,
    )


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
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
    )
    db.add(notification)
    await db.flush()

    actor_id_value = actor_id
    actor_name: str | None = None
    actor_avatar: str | None = None
    if actor_id_value is not None:
        actor_result = await db.execute(
            select(User.full_name, User.avatar_url).where(User.id == actor_id_value)
        )
        actor_row = actor_result.one_or_none()
        if actor_row is not None:
            actor_name, actor_avatar = actor_row

    unread_count = await get_unread_count(db, user_id=user_id)
    realtime_service.queue_user_notification_event(
        db,
        user_id=user_id,
        payload=NotificationCreatedMessage(
            notification=_to_item(
                notification,
                actor_id=actor_id_value,
                actor_full_name=actor_name,
                actor_avatar_url=actor_avatar,
            ),
            unread_count=unread_count,
        ).model_dump(mode="json"),
    )
    return notification


async def mark_read(
    db: AsyncSession,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> Notification:
    result = await db.execute(
        _notification_query_for_user(user_id).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise NotFoundError("Notification not found")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await db.flush()

    unread_count = await get_unread_count(db, user_id=user_id)
    realtime_service.queue_user_notification_event(
        db,
        user_id=user_id,
        payload=NotificationUpdatedMessage(
            notification_id=notification.id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            unread_count=unread_count,
        ).model_dump(mode="json"),
    )
    return notification


async def mark_all_read(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> tuple[int, int]:
    result = await db.execute(
        _notification_query_for_user(user_id).where(
            Notification.is_read == False  # noqa: E712
        )
    )
    notifications = list(result.scalars().all())
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
        payload=NotificationsReadAllMessage(unread_count=unread_count).model_dump(
            mode="json"
        ),
    )
    return len(notifications), unread_count


def get_settings(user: User) -> NotificationSettings:
    preferences = user.preferences if isinstance(user.preferences, dict) else {}
    raw = preferences.get(_SETTINGS_KEY, {})
    if not isinstance(raw, dict):
        raw = {}
    return NotificationSettings(
        email_task_assigned=bool(
            raw.get(
                "email_task_assigned",
                DEFAULT_NOTIFICATION_SETTINGS.email_task_assigned,
            )
        ),
        email_mentioned=bool(
            raw.get(
                "email_mentioned",
                DEFAULT_NOTIFICATION_SETTINGS.email_mentioned,
            )
        ),
        email_deadline_approaching=bool(
            raw.get(
                "email_deadline_approaching",
                DEFAULT_NOTIFICATION_SETTINGS.email_deadline_approaching,
            )
        ),
        push_enabled=bool(
            raw.get("push_enabled", DEFAULT_NOTIFICATION_SETTINGS.push_enabled)
        ),
    )


def update_settings(
    user: User, data: NotificationSettingsUpdate
) -> NotificationSettings:
    current = get_settings(user)
    patch = data.model_dump(exclude_unset=True)
    next_settings = current.model_copy(update=patch)

    preferences = dict(user.preferences or {})
    preferences[_SETTINGS_KEY] = next_settings.model_dump()
    user.preferences = preferences
    return next_settings
