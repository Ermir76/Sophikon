"""
Tests for email verification feature.

Covers:
- GET /api/v1/auth/verify-email  (valid, invalid, expired, reused tokens → 302 redirect)
- POST /api/v1/auth/send-verification-email  (auth, already verified, unauth)
- Registration auto-sends verification email
- Resend invalidates old tokens
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerification
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
SEND_URL = "/api/v1/auth/send-verification-email"

# Known token so we can verify it from the test side
KNOWN_TOKEN = "test-verification-token-abc123"


def _mock_mail_client():
    """Return a mock FastMail client whose send_message is a no-op."""
    mock_fm = MagicMock()
    mock_fm.send_message = AsyncMock()
    return mock_fm


async def _register_user(
    client: AsyncClient,
    email: str = "verify@example.com",
    password: str = "StrongPassword123!",
    full_name: str = "Verify User",
):
    """Register a user and return the response."""
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "full_name": full_name},
    )


async def _get_verification_token_hash(session: AsyncSession, user_id):
    """Get the latest verification token hash for a user from the DB."""
    result = await session.execute(
        select(EmailVerification)
        .where(
            EmailVerification.user_id == user_id,
            EmailVerification.used_at.is_(None),
        )
        .order_by(EmailVerification.created_at.desc())
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# 1. Registration triggers verification email
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_register_sends_verification_email(
    mock_mail, client: AsyncClient, session: AsyncSession
):
    """Registration creates an EmailVerification row and attempts to send."""
    resp = await _register_user(client)
    assert resp.status_code == 201

    user_id = resp.json()["user"]["id"]

    # Verify an EmailVerification row was created
    verification = await _get_verification_token_hash(session, user_id)
    assert verification is not None
    assert verification.token_hash  # hash should be non-empty
    assert verification.used_at is None
    assert verification.expires_at > datetime.now(UTC)

    # Verify send_message was called
    mock_mail.return_value.send_message.assert_called()


# ---------------------------------------------------------------------------
# 2. Verify email — valid token (GET → 302 redirect to ?status=success)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.service.email_service.secrets.token_urlsafe", return_value=KNOWN_TOKEN)
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_verify_email_valid_token(
    mock_mail, mock_token, client: AsyncClient, session: AsyncSession
):
    """Valid token redirects to frontend with ?status=success."""
    resp = await _register_user(client, email="valid_verify@example.com")
    assert resp.status_code == 201

    # GET verify-email with known token (don't follow redirect)
    verify_resp = await client.get(
        VERIFY_URL, params={"token": KNOWN_TOKEN}, follow_redirects=False
    )
    assert verify_resp.status_code == 302
    assert "status=success" in verify_resp.headers["location"]

    # Confirm user.email_verified is True
    user_id = resp.json()["user"]["id"]
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    assert user.email_verified is True


# ---------------------------------------------------------------------------
# 3. Verify email — invalid token (GET → 302 redirect to ?status=error)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_verify_email_invalid_token(mock_mail, client: AsyncClient):
    """Random/wrong token redirects to frontend with ?status=error."""
    resp = await client.get(
        VERIFY_URL, params={"token": "totally-bogus-token"}, follow_redirects=False
    )
    assert resp.status_code == 302
    assert "status=error" in resp.headers["location"]


# ---------------------------------------------------------------------------
# 4. Verify email — expired token (GET → 302 redirect to ?status=error)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.service.email_service.secrets.token_urlsafe", return_value=KNOWN_TOKEN)
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_verify_email_expired_token(
    mock_mail, mock_token, client: AsyncClient, session: AsyncSession
):
    """Expired token redirects to frontend with ?status=error."""
    resp = await _register_user(client, email="expired_verify@example.com")
    assert resp.status_code == 201

    user_id = resp.json()["user"]["id"]

    # Manually expire the token
    verification = await _get_verification_token_hash(session, user_id)
    assert verification is not None
    verification.expires_at = datetime.now(UTC) - timedelta(hours=1)
    await session.commit()

    verify_resp = await client.get(
        VERIFY_URL, params={"token": KNOWN_TOKEN}, follow_redirects=False
    )
    assert verify_resp.status_code == 302
    assert "status=error" in verify_resp.headers["location"]


# ---------------------------------------------------------------------------
# 5. Verify email — already used token (GET → 302 redirect to ?status=error)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.service.email_service.secrets.token_urlsafe", return_value=KNOWN_TOKEN)
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_verify_email_already_used_token(
    mock_mail, mock_token, client: AsyncClient
):
    """Reusing a token after it was consumed redirects to ?status=error."""
    resp = await _register_user(client, email="reuse_verify@example.com")
    assert resp.status_code == 201

    # First call — should succeed (redirect to ?status=success)
    verify_resp1 = await client.get(
        VERIFY_URL, params={"token": KNOWN_TOKEN}, follow_redirects=False
    )
    assert verify_resp1.status_code == 302
    assert "status=success" in verify_resp1.headers["location"]

    # Second call — should fail (redirect to ?status=error)
    verify_resp2 = await client.get(
        VERIFY_URL, params={"token": KNOWN_TOKEN}, follow_redirects=False
    )
    assert verify_resp2.status_code == 302
    assert "status=error" in verify_resp2.headers["location"]


# ---------------------------------------------------------------------------
# 6. Send verification email — authenticated, unverified user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_send_verification_email_authenticated(mock_mail, client: AsyncClient):
    """Authenticated + unverified user can request a new verification email."""
    await _register_user(client, email="resend@example.com")

    # Client has auth cookies from registration
    resp = await client.post(SEND_URL)
    assert resp.status_code == 200
    assert "sent" in resp.json()["message"].lower()


# ---------------------------------------------------------------------------
# 7. Send verification email — already verified
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.service.email_service.secrets.token_urlsafe", return_value=KNOWN_TOKEN)
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_send_verification_email_already_verified(
    mock_mail, mock_token, client: AsyncClient
):
    """Already-verified user gets 400 when requesting verification email."""
    await _register_user(client, email="already_verified@example.com")

    # Verify the email first via GET redirect
    await client.get(VERIFY_URL, params={"token": KNOWN_TOKEN}, follow_redirects=False)

    # Try to request re-send — should be rejected
    resp = await client.post(SEND_URL)
    assert resp.status_code == 400
    assert "already verified" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 8. Send verification email — unauthenticated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_verification_email_unauthenticated(client: AsyncClient):
    """Unauthenticated request to send-verification-email returns 401."""
    resp = await client.post(SEND_URL)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 9. Resending invalidates old tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch(
    "app.service.email_service._get_mail_client",
    return_value=_mock_mail_client(),
)
async def test_send_verification_invalidates_old_tokens(
    mock_mail, client: AsyncClient, session: AsyncSession
):
    """Resending verification email deletes previous unused tokens."""
    resp = await _register_user(client, email="invalidate@example.com")
    assert resp.status_code == 201

    user_id = resp.json()["user"]["id"]

    # Get the first token hash
    first_verification = await _get_verification_token_hash(session, user_id)
    assert first_verification is not None
    first_hash = first_verification.token_hash

    # Request a new verification email
    await client.post(SEND_URL)

    # Refresh the session to see latest state
    session.expire_all()

    # The old token should no longer exist (deleted)
    result = await session.execute(
        select(EmailVerification).where(
            EmailVerification.token_hash == first_hash,
        )
    )
    old_token = result.scalar_one_or_none()
    assert old_token is None

    # A new token should exist
    new_verification = await _get_verification_token_hash(session, user_id)
    assert new_verification is not None
    assert new_verification.token_hash != first_hash
