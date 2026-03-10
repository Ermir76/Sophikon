"""
Activity log business logic.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.enums import AuditAction
from app.models.user import User
from app.repository import activity_log_repo
from app.service.contracts.activity_log import (
    ActivityActorData,
    ActivityChangesData,
    ActivityEntityType,
    ActivityLogItemData,
)


@dataclass(frozen=True, slots=True)
class ActivityContext:
    user_id: UUID | None
    full_name: str | None = None
    avatar_url: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    occurred_at: datetime | None = None


def activity_context_from_request(
    user: User | None,
    request: Request | None,
) -> ActivityContext:
    """Build log context from the current user and request metadata."""
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    return ActivityContext(
        user_id=user.id if user is not None else None,
        full_name=user.full_name if user is not None else None,
        avatar_url=user.avatar_url if user is not None else None,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        occurred_at=datetime.now(UTC),
    )


def serialize_activity_value(value: Any) -> Any:
    """Convert ORM and schema values to JSON-safe primitives."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): serialize_activity_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_activity_value(v) for v in value]
    return value


def build_change_set(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, list[dict[str, Any]]] | None:
    """Build a stable field diff payload for audit entries."""
    fields: list[dict[str, Any]] = []
    for field in sorted(set(before) | set(after)):
        old = serialize_activity_value(before.get(field))
        new = serialize_activity_value(after.get(field))
        if old == new:
            continue
        fields.append({"field": field, "old": old, "new": new})

    if not fields:
        return None
    return {"fields": fields}


async def log_activity(
    db: AsyncSession,
    *,
    project_id: UUID | None,
    action: AuditAction,
    entity_type: ActivityEntityType,
    entity_id: UUID | None = None,
    entity_name: str | None = None,
    changes: dict[str, Any] | None = None,
    context: ActivityContext | None = None,
) -> ActivityLog:
    """Insert an activity row into the current transaction."""
    entry = await activity_log_repo.create(
        db,
        project_id=project_id,
        user_id=context.user_id if context else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        changes=changes,
        ip_address=context.ip_address if context else None,
        user_agent=context.user_agent if context else None,
    )
    if project_id is not None:
        from app.service import realtime_service

        realtime_service.queue_activity_event(
            db,
            project_id=project_id,
            activity_id=entry.id,
            entity_type=entity_type,
            action=action,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            context=context,
        )
    return entry


async def list_activity(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int = 1,
    per_page: int = 50,
    user_id: UUID | None = None,
    entity_type: ActivityEntityType | None = None,
    action: AuditAction | None = None,
) -> tuple[list[ActivityLogItemData], int]:
    """List paginated project activity entries, newest first."""
    rows, total = await activity_log_repo.list_with_user_info(
        db,
        project_id=project_id,
        page=page,
        per_page=per_page,
        user_id=user_id,
        entity_type=entity_type,
        action=action,
    )

    items: list[ActivityLogItemData] = []
    for entry, actor_id, actor_name, avatar_url in rows:
        actor: ActivityActorData | None = None
        if actor_id is not None:
            actor = {
                "id": actor_id,
                "full_name": actor_name,
                "avatar_url": avatar_url,
            }
        changes: ActivityChangesData | None = None
        if entry.changes:
            changes = entry.changes
        items.append(
            {
                "id": entry.id,
                "user": actor,
                "action": entry.action,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "entity_name": entry.entity_name,
                "changes": changes,
                "created_at": entry.created_at,
            }
        )

    return items, int(total)
