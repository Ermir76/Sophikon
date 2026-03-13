from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.attachment import Attachment
from app.models.enums import RoleScope
from app.models.role import Role
from app.models.user import User
from app.service import attachment_service


async def _ensure_system_user_role(session: AsyncSession) -> Role:
    result = await session.execute(
        select(Role).where(Role.name == "user", Role.scope == RoleScope.SYSTEM)
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name="user", scope=RoleScope.SYSTEM, is_system=True)
        session.add(role)
        await session.flush()
    return role


async def _create_user(session: AsyncSession, suffix: str) -> User:
    role = await _ensure_system_user_role(session)
    user = User(
        email=f"attachment-service-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Attachment Service {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()
    return user


def test_sanitize_filename_strips_unsafe_characters() -> None:
    sanitized = attachment_service.sanitize_filename("../weird file<>?.pdf")
    assert sanitized == "weird_file_.pdf"


def test_validate_attachment_content_type_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        attachment_service.validate_attachment_content_type("application/x-sh")


def test_validate_attachment_size_rejects_empty_and_oversized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "MAX_ATTACHMENT_UPLOAD_BYTES", 8)

    with pytest.raises(ValidationError):
        attachment_service.validate_attachment_size(0)

    with pytest.raises(ValidationError):
        attachment_service.validate_attachment_size(9)


@pytest.mark.asyncio
async def test_create_task_attachment_persists_row_and_file(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    user = await _create_user(session, "create")
    task_id = uuid7()
    task_ref = SimpleNamespace(id=task_id)

    created = await attachment_service.create_task_attachment(
        session,
        task=task_ref,
        uploaded_by_id=user.id,
        file_name="spec notes.txt",
        mime_type="text/plain",
        file_bytes=b"attachment-content",
        description="Unit test file",
    )

    assert created.entity_type == "task"
    assert str(created.entity_id) == str(task_id)
    assert created.file_name == "spec_notes.txt"
    assert created.file_size == len(b"attachment-content")
    assert created.mime_type == "text/plain"

    absolute_path = attachment_service.resolve_attachment_path(created.storage_path)
    assert absolute_path is not None
    assert absolute_path.exists()
    assert absolute_path.read_bytes() == b"attachment-content"


@pytest.mark.asyncio
async def test_delete_task_attachment_soft_deletes_and_removes_file(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    user = await _create_user(session, "delete")
    task_ref = SimpleNamespace(id=uuid7())
    created = await attachment_service.create_task_attachment(
        session,
        task=task_ref,
        uploaded_by_id=user.id,
        file_name="delete-me.txt",
        mime_type="text/plain",
        file_bytes=b"delete-content",
        description=None,
    )
    absolute_path = attachment_service.resolve_attachment_path(created.storage_path)
    assert absolute_path is not None
    assert absolute_path.exists()

    await attachment_service.delete_task_attachment(session, attachment=created)

    refreshed = await session.get(Attachment, created.id)
    assert refreshed is not None
    assert refreshed.is_deleted is True
    assert absolute_path.exists() is False
