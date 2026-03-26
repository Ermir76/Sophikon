"""
Task attachment business logic.
"""

import asyncio
import re
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.attachment_storage import ensure_attachment_root, resolve_attachment_path
from app.core.config import settings
from app.core.exceptions import InvalidOperationError, ValidationError
from app.models.attachment import Attachment
from app.models.task import Task
from app.repository import attachment_repo

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

ALLOWED_ATTACHMENT_CONTENT_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}


def sanitize_filename(file_name: str) -> str:
    """
    Produce a storage-safe filename while preserving extension when possible.
    """
    cleaned = _SAFE_FILENAME_RE.sub("_", file_name.strip())
    cleaned = cleaned.strip("._")
    return cleaned[:160] or "attachment"


def build_task_attachment_storage_path(
    task_id: UUID,
    file_name: str,
) -> str:
    safe_name = sanitize_filename(file_name)
    return str(Path("tasks") / str(task_id) / f"{uuid7()}_{safe_name}")


def validate_attachment_content_type(content_type: str | None) -> str:
    content_type_value = (content_type or "").strip().lower()
    if content_type_value not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
        raise ValidationError("Unsupported attachment type")
    return content_type_value


def validate_attachment_size(size_bytes: int) -> None:
    if size_bytes <= 0:
        raise ValidationError("Attachment cannot be empty")
    if size_bytes > settings.MAX_ATTACHMENT_UPLOAD_BYTES:
        raise ValidationError("Attachment exceeds size limit")


async def list_task_attachments(
    db: AsyncSession,
    *,
    task_id: UUID,
) -> list[Attachment]:
    return await attachment_repo.list_for_task(db, task_id=task_id)


async def create_task_attachment(
    db: AsyncSession,
    *,
    task: Task,
    uploaded_by_id: UUID,
    file_name: str,
    mime_type: str,
    file_bytes: bytes,
    description: str | None,
) -> Attachment:
    validate_attachment_size(len(file_bytes))
    validate_attachment_content_type(mime_type)

    storage_path = build_task_attachment_storage_path(task.id, file_name)
    ensure_attachment_root()
    absolute_path = resolve_attachment_path(storage_path)
    if absolute_path is None:
        raise InvalidOperationError("Invalid attachment storage path")

    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(absolute_path.write_bytes, file_bytes)

    try:
        attachment = await attachment_repo.create(
            db,
            task_id=task.id,
            uploaded_by_id=uploaded_by_id,
            payload={
                "file_name": sanitize_filename(file_name),
                "file_size": len(file_bytes),
                "mime_type": mime_type,
                "storage_path": storage_path,
                "description": description,
            },
        )
        await db.commit()
        await db.refresh(attachment)
        return attachment
    except Exception:
        if await asyncio.to_thread(absolute_path.exists):
            await asyncio.to_thread(absolute_path.unlink, True)
        raise


async def get_task_attachment_by_id(
    db: AsyncSession,
    *,
    attachment_id: UUID,
    task_id: UUID,
) -> Attachment | None:
    return await attachment_repo.get_for_task(
        db,
        attachment_id=attachment_id,
        task_id=task_id,
    )


async def delete_task_attachment(
    db: AsyncSession,
    *,
    attachment: Attachment,
) -> None:
    absolute_path = resolve_attachment_path(attachment.storage_path)
    if absolute_path and await asyncio.to_thread(absolute_path.exists):
        await asyncio.to_thread(absolute_path.unlink, True)

    await attachment_repo.soft_delete(db, attachment=attachment)
    await db.commit()
