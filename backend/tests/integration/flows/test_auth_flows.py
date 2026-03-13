from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from uuid_utils import uuid7

from app.core.auth_flow import build_password_reset_link
from app.core.security import hash_token
from app.models.organization import Organization
from app.models.password_reset import PasswordReset
from app.models.user import User


@pytest.mark.asyncio
async def test_register_creates_personal_org(client: AsyncClient):
    """
    Integration: Register -> Personal Org auto-created -> Appears in Org List.
    """
    # 1. Register
    email = "new_user_auth_flow@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Auth Flow User",
        },
    )
    assert resp.status_code == 201

    # 2. List Organizations
    # The user should be automatically logged in (cookies set)
    org_resp = await client.get("/api/v1/organizations")
    assert org_resp.status_code == 200
    items = org_resp.json()["items"]

    # After registration, exactly 1 personal org should exist
    assert len(items) == 1
    # Optional: Verify name format if known, but existence is key here.


@pytest.mark.asyncio
async def test_token_rotation_security(client: AsyncClient):
    """
    Integration: Refresh Token Rotation -> Old token invalidated.
    """
    # 1. Register (login)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "token_flow_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Token Flow User",
        },
    )

    # Capture initial cookies
    # Note: client.cookies automatically manages them.
    # We need to extract the refresh token value to manually send it later.
    refresh_token_1 = client.cookies.get("refresh_token")
    assert refresh_token_1

    # 2. Refresh (Rotates token)
    resp_ref = await client.post("/api/v1/auth/refresh")
    assert resp_ref.status_code == 200
    refresh_token_2 = client.cookies.get("refresh_token")

    # Verify token changed
    assert refresh_token_2 != refresh_token_1

    # 3. Try to use Old Refresh Token
    # We need to clear cookies and manually set the old one.
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token_1)

    # Attempt refresh again
    resp_reuse = await client.post("/api/v1/auth/refresh")

    # Should be 401 Unauthorized (Token Reuse Detection or simply Invalid Token)
    assert resp_reuse.status_code == 401


@pytest.mark.asyncio
async def test_register_atomic_failure(client: AsyncClient, session):
    """
    If token creation fails, neither the user nor the org should be committed.
    """
    email = "fail_atomic@example.com"
    with patch(
        "app.service.auth_service._create_token_pair",
        side_effect=Exception("Simulated failure"),
    ):
        with pytest.raises(Exception, match="Simulated failure"):
            await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongPassword123!",
                    "full_name": "Atomic Fail User",
                },
            )

    # User should not exist
    user_resp = await session.execute(select(User).where(User.email == email))
    assert user_resp.scalar_one_or_none() is None

    # Org should not exist
    org_resp = await session.execute(
        select(Organization).where(Organization.slug == "fail-atomic")
    )
    assert org_resp.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_oauth_callback_end_to_end_with_provider_stub(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Full OAuth web flow with provider stub:
    start -> callback -> auth cookies -> /auth/me works.
    """
    email = f"oauth-flow-{uuid7()}@example.com"

    def _fake_authorize_url(state_token: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state_token}"

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return {
            "sub": f"google-sub-{uuid7()}",
            "email": email,
            "name": "OAuth Flow User",
            "picture": "https://example.com/avatar.png",
            "email_verified": True,
        }

    monkeypatch.setattr(
        "app.service.auth_service.build_google_oauth_authorize_url",
        _fake_authorize_url,
    )
    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    start_response = await client.get(
        "/api/v1/auth/oauth/google",
        params={"next": "/projects"},
        follow_redirects=False,
    )
    assert start_response.status_code == 302
    state_token = start_response.cookies["oauth_google_state"]

    callback_response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "oauth-code", "state": state_token},
        follow_redirects=False,
    )
    assert callback_response.status_code == 302
    assert callback_response.headers["location"].endswith("/projects")
    assert callback_response.cookies.get("access_token")
    assert callback_response.cookies.get("refresh_token")

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    assert me_response.json()["full_name"] == "OAuth Flow User"


@pytest.mark.asyncio
async def test_password_reset_email_link_contains_expected_token_contract(
    client: AsyncClient,
    session,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Password reset email contains frontend reset link with token that hashes
    to the persisted single-use PasswordReset row.
    """
    email = f"reset-link-{uuid7()}@example.com"
    captured: dict[str, object] = {}

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Reset Link User",
        },
    )

    class _CaptureMailClient:
        async def send_message(self, message):
            captured["subject"] = message.subject
            captured["body"] = message.body
            captured["recipients"] = message.recipients

    monkeypatch.setattr(
        "app.service.email_service._get_mail_client",
        lambda: _CaptureMailClient(),
    )

    reset_response = await client.post(
        "/api/v1/auth/password-reset",
        json={"email": email},
    )
    assert reset_response.status_code == 200
    assert "reset instructions" in reset_response.json()["message"]

    body = str(captured.get("body") or "")
    marker = "token="
    token_start = body.find(marker)
    assert token_start != -1
    token = body[token_start + len(marker) :].split('"', 1)[0].split("&", 1)[0]
    assert token
    assert build_password_reset_link(token) in body

    user_result = await session.execute(select(User).where(User.email == email))
    user = user_result.scalar_one()
    reset_result = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    reset_token_row = reset_result.scalar_one()
    assert reset_token_row.token_hash == hash_token(token)
