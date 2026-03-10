"""
Activity log repository helpers.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.enums import AuditAction
from app.models.user import User
from app.service.contracts.activity_log import ActivityEntityType


async def create(
    db: AsyncSession,
    *,
    project_id: UUID | None,
    user_id: UUID | None,
    action: AuditAction,
    entity_type: ActivityEntityType,
    entity_id: UUID | None,
    entity_name: str | None,
    changes: dict | None,
    ip_address: str | None,
    user_agent: str | None,
) -> ActivityLog:
    entry = ActivityLog(
        project_id=project_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_with_user_info(
    db: AsyncSession,
    *,
    project_id: UUID,
    page: int,
    per_page: int,
    user_id: UUID | None = None,
    entity_type: ActivityEntityType | None = None,
    action: AuditAction | None = None,
) -> tuple[list[tuple[ActivityLog, UUID | None, str | None, str | None]], int]:
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
    total = int(total_result.scalar() or 0)

    offset = (page - 1) * per_page
    result = await db.execute(
        select(ActivityLog, User.id, User.full_name, User.avatar_url)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .where(*filters)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.all()), total
