"""
Helpers for queuing and publishing realtime events after commit.
"""

import logging
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user_notification_websocket_manager import (
    user_notification_websocket_manager,
)
from app.core.websocket_manager import websocket_manager
from app.models.enums import AuditAction
from app.service.activity_log_service import ActivityContext, serialize_activity_value
from app.service.contracts.realtime import (
    JsonValue,
    RealtimeActor,
    RealtimeChannel,
    RealtimeEntityType,
    RealtimeEventPayload,
)

logger = logging.getLogger(__name__)

PENDING_REALTIME_EVENTS_KEY = "pending_realtime_events"
PENDING_USER_NOTIFICATION_EVENTS_KEY = "pending_user_notification_events"

ENTITY_CHANNELS: dict[RealtimeEntityType, list[RealtimeChannel]] = {
    "project": ["project"],
    "task": ["tasks"],
    "resource": ["resources"],
    "assignment": ["tasks", "resources"],
    "dependency": ["tasks"],
    "project_member": ["members"],
    "comment": ["comments"],
}


def clear_pending_events(db: AsyncSession) -> None:
    db.info.pop(PENDING_REALTIME_EVENTS_KEY, None)
    db.info.pop(PENDING_USER_NOTIFICATION_EVENTS_KEY, None)


def queue_message(
    db: AsyncSession,
    *,
    project_id: UUID | str,
    channels: list[RealtimeChannel],
    payload: dict[str, Any],
) -> None:
    db.info.setdefault(PENDING_REALTIME_EVENTS_KEY, []).append(
        {
            "project_id": str(project_id),
            "channels": channels,
            "payload": payload,
        }
    )


def queue_user_notification_event(
    db: AsyncSession,
    *,
    user_id: UUID | str,
    payload: dict[str, Any],
) -> None:
    db.info.setdefault(PENDING_USER_NOTIFICATION_EVENTS_KEY, []).append(
        {
            "user_id": str(user_id),
            "payload": payload,
        }
    )


def queue_entity_event(
    db: AsyncSession,
    *,
    project_id: UUID,
    entity_type: RealtimeEntityType,
    action: AuditAction,
    entity_id: UUID | None,
    entity_name: str | None,
    context: ActivityContext | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload = _build_event_payload(
        event_type=f"{entity_type}_{action.value}",
        project_id=project_id,
        entity_type=entity_type,
        action=action,
        entity_id=entity_id,
        entity_name=entity_name,
        context=context,
        metadata=metadata,
    )
    queue_message(
        db,
        project_id=project_id,
        channels=ENTITY_CHANNELS.get(entity_type, []),
        payload=payload,
    )


def queue_activity_event(
    db: AsyncSession,
    *,
    project_id: UUID,
    activity_id: UUID,
    entity_type: RealtimeEntityType,
    action: AuditAction,
    entity_id: UUID | None,
    entity_name: str | None,
    changes: dict[str, Any] | None,
    context: ActivityContext | None = None,
) -> None:
    payload = _build_event_payload(
        event_type="activity_logged",
        project_id=project_id,
        entity_type=entity_type,
        action=action,
        entity_id=entity_id,
        entity_name=entity_name,
        context=context,
        metadata={
            "activity_id": activity_id,
            "changes": changes,
        },
    )
    queue_message(
        db,
        project_id=project_id,
        channels=["activity"],
        payload=payload,
    )


async def commit_and_publish(db: AsyncSession) -> None:
    try:
        await db.commit()
    except Exception:
        clear_pending_events(db)
        raise

    pending_project_events = db.info.pop(PENDING_REALTIME_EVENTS_KEY, [])
    pending_user_notification_events = db.info.pop(
        PENDING_USER_NOTIFICATION_EVENTS_KEY, []
    )

    published_count = 0
    failed_count = 0
    for event in pending_project_events:
        try:
            await websocket_manager.publish_message(
                project_id=event["project_id"],
                channels=event["channels"],
                payload=event["payload"],
            )
            published_count += 1
        except Exception:
            failed_count += 1
            logger.exception(
                "realtime_publish_failed",
                extra={
                    "project_id": event["project_id"],
                    "channels": event["channels"],
                    "event_type": event["payload"].get("type"),
                },
            )

    user_published_count = 0
    user_failed_count = 0
    for event in pending_user_notification_events:
        try:
            await user_notification_websocket_manager.publish_message(
                user_id=event["user_id"],
                payload=event["payload"],
            )
            user_published_count += 1
        except Exception:
            user_failed_count += 1
            logger.exception(
                "user_notification_publish_failed",
                extra={
                    "user_id": event["user_id"],
                    "event_type": event["payload"].get("type"),
                },
            )

    if pending_project_events or pending_user_notification_events:
        logger.info(
            "realtime_publish_batch_completed",
            extra={
                "events_total": len(pending_project_events),
                "events_published": published_count,
                "events_failed": failed_count,
                "user_events_total": len(pending_user_notification_events),
                "user_events_published": user_published_count,
                "user_events_failed": user_failed_count,
            },
        )


async def rollback_and_clear(db: AsyncSession) -> None:
    clear_pending_events(db)
    await db.rollback()


def _build_event_payload(
    *,
    event_type: str,
    project_id: UUID,
    entity_type: RealtimeEntityType,
    action: AuditAction,
    entity_id: UUID | None,
    entity_name: str | None,
    context: ActivityContext | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    return RealtimeEventPayload(
        type=event_type,
        project_id=project_id,
        actor=_actor_from_context(context),
        entity_type=entity_type,
        action=action,
        entity_id=entity_id,
        entity_name=entity_name,
        occurred_at=_timestamp(context),
        metadata=_serialize_realtime_metadata_object(metadata)
        if metadata is not None
        else None,
    ).model_dump(mode="json")


def _actor_from_context(context: ActivityContext | None) -> RealtimeActor | None:
    if context is None or context.user_id is None:
        return None
    return RealtimeActor(
        id=context.user_id,
        full_name=context.full_name,
        avatar_url=context.avatar_url,
    )


def _timestamp(context: ActivityContext | None):
    if context is not None and context.occurred_at is not None:
        return context.occurred_at
    from datetime import UTC, datetime

    return datetime.now(UTC)


def _serialize_realtime_metadata_object(
    value: Mapping[str, Any],
) -> dict[str, JsonValue]:
    return {
        str(key): _serialize_realtime_metadata_value(item)
        for key, item in value.items()
    }


def _serialize_realtime_metadata_value(value: Any) -> JsonValue:
    if isinstance(value, dict):
        return {
            str(key): _serialize_realtime_metadata_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize_realtime_metadata_value(item) for item in value]

    serialized = serialize_activity_value(value)
    if serialized is not value:
        return serialized

    if value is not None:
        try:
            return str(UUID(str(value)))
        except (TypeError, ValueError, AttributeError):
            pass

    return value
