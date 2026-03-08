from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.config import settings
from app.core.security import hash_token
from app.models.email_verification import EmailVerification
from app.models.user import User
from app.service import email_service


def _unique_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local}+{uuid7()}@{domain}"


def _unique_token(prefix: str) -> str:
    return f"{prefix}-{uuid7()}"


async def _register_user(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one()


def _mock_mail_client() -> MagicMock:
    client = MagicMock()
    client.send_message = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_send_verification_email_replaces_old_tokens_and_sends_message(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    email = _unique_email("email-service-verify@example.com")
    stale_token = _unique_token("stale-token")
    fresh_token = _unique_token("fresh-verification-token")
    await _register_user(client, email, "Email Service Verify")
    user = await _get_user(session, email)

    old_verification = EmailVerification(
        user_id=user.id,
        token_hash=hash_token(stale_token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session.add(old_verification)
    await session.commit()

    mock_client = _mock_mail_client()
    monkeypatch.setattr(
        "app.service.email_service._get_mail_client", lambda: mock_client
    )
    monkeypatch.setattr(
        "app.service.email_service.secrets.token_urlsafe",
        lambda _: fresh_token,
    )

    await email_service.send_verification_email(session, user.id, user.email)

    verifications = list(
        (
            await session.execute(
                select(EmailVerification).where(EmailVerification.user_id == user.id)
            )
        ).scalars()
    )
    message = mock_client.send_message.await_args.args[0]

    assert len(verifications) == 1
    assert verifications[0].token_hash == hash_token(fresh_token)
    assert settings.BACKEND_URL in message.body
    assert fresh_token in message.body


@pytest.mark.asyncio
async def test_send_project_invitation_email_includes_accept_url(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_client = _mock_mail_client()
    monkeypatch.setattr(
        "app.service.email_service._get_mail_client", lambda: mock_client
    )

    await email_service.send_project_invitation_email(
        email="invitee@example.com",
        inviter_name="Owner",
        project_name="Invitation Project",
        role_name="viewer",
        accept_url="https://frontend.test/project-invitations/accept?token=abc",
    )

    message = mock_client.send_message.await_args.args[0]

    assert message.subject == "Project invitation: Invitation Project"
    assert "https://frontend.test/project-invitations/accept?token=abc" in message.body
    assert "viewer" in message.body


@pytest.mark.asyncio
async def test_verify_email_token_marks_user_verified_and_token_used(
    client: AsyncClient,
    session: AsyncSession,
):
    email = _unique_email("email-service-consume@example.com")
    consume_token = _unique_token("consume-token")
    await _register_user(client, email, "Email Service Consume")
    user = await _get_user(session, email)
    verification = EmailVerification(
        user_id=user.id,
        token_hash=hash_token(consume_token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    session.add(verification)
    await session.commit()

    await email_service.verify_email_token(session, consume_token)
    await session.refresh(user)
    await session.refresh(verification)

    assert user.email_verified is True
    assert verification.used_at is not None
