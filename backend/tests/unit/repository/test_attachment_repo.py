from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.enums import RoleScope
from app.models.role import Role
from app.models.user import User
from app.repository import attachment_repo


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
        email=f"attachment-repo-{suffix}-{uuid7()}@example.com",
        password_hash="hashed",
        full_name=f"Attachment Repo {suffix}",
        system_role_id=role.id,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_create_and_list_for_task_scopes_to_task_id(
    session: AsyncSession,
) -> None:
    user = await _create_user(session, "scope")
    task_a = uuid7()
    task_b = uuid7()

    await attachment_repo.create(
        session,
        task_id=task_a,
        uploaded_by_id=user.id,
        payload={
            "file_name": "a.txt",
            "file_size": 1,
            "mime_type": "text/plain",
            "storage_path": "tasks/a/a.txt",
            "description": None,
        },
    )
    await attachment_repo.create(
        session,
        task_id=task_b,
        uploaded_by_id=user.id,
        payload={
            "file_name": "b.txt",
            "file_size": 1,
            "mime_type": "text/plain",
            "storage_path": "tasks/b/b.txt",
            "description": None,
        },
    )
    await session.commit()

    listed = await attachment_repo.list_for_task(session, task_id=task_a)
    assert len(listed) == 1
    assert str(listed[0].entity_id) == str(task_a)
    assert listed[0].file_name == "a.txt"


@pytest.mark.asyncio
async def test_get_for_task_requires_matching_task_and_not_deleted(
    session: AsyncSession,
) -> None:
    user = await _create_user(session, "get")
    task_id = uuid7()
    attachment = await attachment_repo.create(
        session,
        task_id=task_id,
        uploaded_by_id=user.id,
        payload={
            "file_name": "doc.txt",
            "file_size": 3,
            "mime_type": "text/plain",
            "storage_path": "tasks/get/doc.txt",
            "description": "hello",
        },
    )
    await session.commit()

    found = await attachment_repo.get_for_task(
        session,
        attachment_id=attachment.id,
        task_id=task_id,
    )
    assert found is not None
    assert str(found.id) == str(attachment.id)

    wrong_task = await attachment_repo.get_for_task(
        session,
        attachment_id=attachment.id,
        task_id=uuid7(),
    )
    assert wrong_task is None


@pytest.mark.asyncio
async def test_soft_delete_marks_deleted_and_hides_from_listing(
    session: AsyncSession,
) -> None:
    user = await _create_user(session, "soft-delete")
    task_id = uuid7()
    attachment = await attachment_repo.create(
        session,
        task_id=task_id,
        uploaded_by_id=user.id,
        payload={
            "file_name": "delete.txt",
            "file_size": 10,
            "mime_type": "text/plain",
            "storage_path": "tasks/delete/delete.txt",
            "description": None,
        },
    )
    await session.commit()

    await attachment_repo.soft_delete(session, attachment=attachment)
    await session.commit()

    listed = await attachment_repo.list_for_task(session, task_id=task_id)
    assert listed == []
    assert attachment.is_deleted is True
    assert isinstance(attachment.deleted_at, datetime)
    assert attachment.deleted_at.tzinfo is not None
