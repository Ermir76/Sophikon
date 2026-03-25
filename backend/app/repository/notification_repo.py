"""
Notification repository helpers.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, and_, exists, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.project_invitation import ProjectInvitation
from app.models.user import User


@dataclass(frozen=True, slots=True)
class NotificationRow:
    notification: Notification
    actor_id: UUID | None
    actor_full_name: str | None
    actor_avatar_url: str | None


def query_for_user(user_id: UUID) -> Select[tuple[Notification]]:
    return select(Notification).where(Notification.user_id == user_id)


def _active_notification_filters(user_id: UUID) -> list:
    now = datetime.now(UTC)
    invitation_notification = and_(
        Notification.type == NotificationType.INVITATION_RECEIVED,
        Notification.entity_type == "project_invitation",
    )
    actionable_invitation = and_(
        Notification.entity_id.is_not(None),
        exists(
            select(ProjectInvitation.id).where(
                ProjectInvitation.id == Notification.entity_id,
                ProjectInvitation.accepted_at.is_(None),
                ProjectInvitation.is_revoked == False,  # noqa: E712
                ProjectInvitation.expires_at >= now,
            )
        ),
    )

    return [
        Notification.user_id == user_id,
        or_(not_(invitation_notification), actionable_invitation),
    ]


async def count_unread(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            *_active_notification_filters(user_id),
            Notification.is_read == False,  # noqa: E712
        )
    )
    return int(result.scalar() or 0)


async def list_with_actor(
    db: AsyncSession,
    *,
    user_id: UUID,
    page: int,
    per_page: int,
    unread_only: bool,
) -> tuple[list[NotificationRow], int]:
    filters = _active_notification_filters(user_id)
    if unread_only:
        filters.append(Notification.is_read == False)  # noqa: E712

    count_query = select(func.count()).select_from(
        select(Notification.id).where(*filters).subquery()
    )
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

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
        NotificationRow(
            notification=notification,
            actor_id=actor_id,
            actor_full_name=actor_name,
            actor_avatar_url=avatar_url,
        )
        for notification, actor_id, actor_name, avatar_url in rows.all()
    ]
    return items, total


async def get_with_actor_by_id(
    db: AsyncSession,
    *,
    user_id: UUID,
    notification_id: UUID,
) -> NotificationRow | None:
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
        return None

    notification, actor_id, actor_name, avatar_url = result
    return NotificationRow(
        notification=notification,
        actor_id=actor_id,
        actor_full_name=actor_name,
        actor_avatar_url=avatar_url,
    )


async def get_by_id_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    notification_id: UUID,
) -> Notification | None:
    result = await db.execute(
        query_for_user(user_id).where(Notification.id == notification_id)
    )
    return result.scalar_one_or_none()


async def list_unread_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> list[Notification]:
    result = await db.execute(
        query_for_user(user_id).where(
            *_active_notification_filters(user_id)[1:],
            Notification.is_read == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def list_for_entity(
    db: AsyncSession,
    *,
    user_id: UUID,
    type: NotificationType,
    entity_type: str,
    entity_id: UUID,
) -> list[Notification]:
    result = await db.execute(
        query_for_user(user_id).where(
            Notification.type == type,
            Notification.entity_type == entity_type,
            Notification.entity_id == entity_id,
        )
    )
    return list(result.scalars().all())


async def get_actor_profile(
    db: AsyncSession,
    *,
    actor_id: UUID,
) -> tuple[str | None, str | None] | None:
    result = await db.execute(
        select(User.full_name, User.avatar_url).where(User.id == actor_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    full_name, avatar_url = row
    return full_name, avatar_url


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
    return notification
