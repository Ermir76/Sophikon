"""
Attachment repository helpers.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.models.enums import StorageProvider


async def list_for_task(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> list[Attachment]:
    result = await db.execute(
        select(Attachment)
        .where(
            Attachment.entity_type == "task",
            Attachment.entity_id == task_id,
            Attachment.is_deleted.is_(False),
        )
        .order_by(Attachment.created_at.desc())
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    *,
    task_id: UUID,
    uploaded_by_id: UUID,
    payload: Mapping[str, Any],
) -> Attachment:
    attachment = Attachment(
        entity_type="task",
        entity_id=task_id,
        uploaded_by_id=uploaded_by_id,
        file_name=payload["file_name"],
        file_size=payload["file_size"],
        mime_type=payload["mime_type"],
        storage_path=payload["storage_path"],
        storage_provider=StorageProvider.LOCAL,
        description=payload.get("description"),
    )
    db.add(attachment)
    await db.flush()
    return attachment


async def get_for_task(
    db: AsyncSession,
    *,
    attachment_id: UUID,
    task_id: UUID,
) -> Attachment | None:
    result = await db.execute(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.entity_type == "task",
            Attachment.entity_id == task_id,
            Attachment.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete(
    db: AsyncSession,
    *,
    attachment: Attachment,
) -> None:
    attachment.is_deleted = True
    attachment.deleted_at = datetime.now(UTC)
    await db.flush()
