from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.enums import RoleScope
from app.models.role import Role
from app.service import auth_service, email_service
from app.tasks import notification_tasks


async def _ensure_system_user_role(session: AsyncSession) -> None:
    result = await session.execute(
        select(Role).where(Role.name == "user", Role.scope == RoleScope.SYSTEM)
    )
    role = result.scalar_one_or_none()
    if role is None:
        session.add(Role(name="user", scope=RoleScope.SYSTEM, is_system=True))
        await session.flush()


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid7()}@example.com"


@pytest.mark.asyncio
async def test_send_verification_reminder_email_sends_before_grace_expiry(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _ensure_system_user_role(session)
    send_mock = AsyncMock()
    monkeypatch.setattr(email_service, "send_verification_email", send_mock)

    user, _, _ = await auth_service.register_user(
        session,
        _unique_email("verification-reminder"),
        "StrongPassword123!",
        "Reminder User",
    )

    sent = await notification_tasks._send_verification_reminder_email_with_db(
        session,
        user_id=str(user.id),
    )

    assert sent is True
    send_mock.assert_awaited_once_with(
        session,
        user.id,
        user.email,
        is_reminder=True,
    )


@pytest.mark.asyncio
async def test_send_verification_reminder_email_skips_expired_unverified_user(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _ensure_system_user_role(session)
    send_mock = AsyncMock()
    monkeypatch.setattr(email_service, "send_verification_email", send_mock)

    user, _, _ = await auth_service.register_user(
        session,
        _unique_email("verification-reminder-expired"),
        "StrongPassword123!",
        "Expired Reminder User",
    )
    user.created_at = datetime.now(UTC) - timedelta(hours=25)
    await session.commit()

    sent = await notification_tasks._send_verification_reminder_email_with_db(
        session,
        user_id=str(user.id),
    )

    assert sent is False
    send_mock.assert_not_awaited()
