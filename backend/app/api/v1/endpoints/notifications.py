"""
User notification endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.repository.notification_repo import NotificationRow
from app.schema.notification import (
    NotificationActor,
    NotificationItem,
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationSettings,
    NotificationSettingsUpdate,
)
from app.service import notification_service, realtime_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_notification_item(row: NotificationRow) -> NotificationItem:
    actor = None
    if row.actor_id is not None:
        actor = NotificationActor(
            id=row.actor_id,
            full_name=row.actor_full_name,
            avatar_url=row.actor_avatar_url,
        )
    notification = row.notification
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


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    unread_only: Annotated[bool, Query()] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total, unread_count = await notification_service.list_notifications(
        db,
        user_id=user.id,
        unread_only=unread_only,
        page=page,
        per_page=per_page,
    )
    return NotificationListResponse(
        items=[_to_notification_item(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_read(
    notification_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    row = await notification_service.mark_read(
        db,
        notification_id=notification_id,
        user_id=user.id,
    )
    await realtime_service.commit_and_publish(db)
    return _to_notification_item(row)


@router.post("/read-all", response_model=NotificationReadAllResponse)
async def mark_all_notifications_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    updated_count, unread_count = await notification_service.mark_all_read(
        db, user_id=user.id
    )
    await realtime_service.commit_and_publish(db)
    return NotificationReadAllResponse(
        updated_count=updated_count,
        unread_count=unread_count,
    )


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(
    user: Annotated[User, Depends(get_current_active_user)],
):
    return NotificationSettings.model_validate(notification_service.get_settings(user))


@router.patch("/settings", response_model=NotificationSettings)
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    settings = notification_service.update_settings(
        user,
        body.model_dump(exclude_unset=True),
    )
    await db.commit()
    return NotificationSettings.model_validate(settings)
