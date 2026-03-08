"""
Activity log business logic.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.enums import AuditAction
from app.models.user import User
from app.schema.activity_log import ActivityEntityType

if TYPE_CHECKING:
    from app.schema.activity_log import ActivityLogItem


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
    entry = ActivityLog(
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
    db.add(entry)
    await db.flush()
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
) -> tuple[list["ActivityLogItem"], int]:
    """List paginated project activity entries, newest first."""
    from app.schema.activity_log import ActivityActor, ActivityChanges, ActivityLogItem

    filters = [ActivityLog.project_id == project_id]
    if user_id is not None:
        filters.append(ActivityLog.user_id == user_id)
    if entity_type is not None:
        filters.append(ActivityLog.entity_type == entity_type)
    if action is not None:
        filters.append(ActivityLog.action == action)

    count_query = select(func.count()).select_from(
        select(ActivityLog.id).where(*filters).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(ActivityLog, User.id, User.full_name, User.avatar_url)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .where(*filters)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    items: list[ActivityLogItem] = []
    for entry, actor_id, actor_name, avatar_url in result.all():
        items.append(
            ActivityLogItem(
                id=entry.id,
                user=(
                    ActivityActor(
                        id=actor_id,
                        full_name=actor_name,
                        avatar_url=avatar_url,
                    )
                    if actor_id is not None
                    else None
                ),
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                entity_name=entry.entity_name,
                changes=ActivityChanges.model_validate(entry.changes)
                if entry.changes
                else None,
                created_at=entry.created_at,
            )
        )

    return items, total
