from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_token
from app.models.password_reset import PasswordReset
from app.service import ai_service, auth_service


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Register creates a user, returns user data, and sets auth cookies."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    # User data is nested under "user"
    user = data["user"]
    assert user["email"] == "newuser@example.com"
    assert user["full_name"] == "New User"
    assert "id" in user
    assert user["is_active"] is True

    # Tokens structure exists (values are empty because they're in cookies)
    assert "tokens" in data

    # Auth cookies are set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Register — duplicate email returns 409"""
    email = "duplicate@example.com"
    password = "StrongPassword123!"

    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "First User",
        },
    )

    # Second registration with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "AnotherPassword456!",
            "full_name": "Second User",
        },
    )

    assert response.status_code == 409
    assert "already registered" in response.text


@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    """Register — missing required fields returns 422"""
    # Missing email
    resp1 = await client.post(
        "/api/v1/auth/register",
        json={
            "password": "StrongPassword123!",
            "full_name": "No Email",
        },
    )
    assert resp1.status_code == 422

    # Missing password
    resp2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nopassword@example.com",
            "full_name": "No Password",
        },
    )
    assert resp2.status_code == 422

    # Missing name
    resp3 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "noname@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert resp3.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Register — weak password (less than 8 chars) returns 422"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weakpass@example.com",
            "password": "short",  # < 8 chars
            "full_name": "Weak Password",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Register — invalid email format returns 422"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
            "full_name": "Invalid Email",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Success — valid credentials return user data + set cookies (200)"""
    email = "login_success@example.com"
    password = "StrongPassword123!"

    # 1. Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login User",
        },
    )

    # 2. Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == email
    # Check cookies are set
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login — wrong password returns 401"""
    email = "wrong_password@example.com"
    password = "StrongPassword123!"

    # 1. Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login User",
        },
    )

    # 2. Login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword!",
        },
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_login_non_existent_email(client: AsyncClient):
    """Login — non-existent email returns 401"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "doesntexist@example.com",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    """Login — missing required fields returns 422"""
    # Missing email
    resp1 = await client.post(
        "/api/v1/auth/login",
        json={
            "password": "StrongPassword123!",
        },
    )
    assert resp1.status_code == 422

    # Missing password
    resp2 = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
        },
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """Success — valid refresh cookie rotates tokens (200)"""
    email = "refresh@example.com"
    password = "StrongPassword123!"

    # 1. Register to get tokens
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Refresh User",
        },
    )
    assert register_response.status_code == 201

    # client automatically stores cookies from register_response

    # 2. Refresh
    # Need to wait a tiny bit? Probably not for functional test unless
    # there is a strict "not before" check that fails instantly.
    # Usually refresh is allowed immediately.

    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200

    # Check new tokens
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Verify we can user new access token
    # (By calling /me or similar, but test plan doesn't strictly require it here,
    # just checking 200 and cookies is enough for "rotates tokens")


@pytest.mark.asyncio
async def test_refresh_token_missing_cookie(client: AsyncClient):
    """Refresh — missing cookie returns 401"""
    # Simply call refresh without logging in first.
    # The client fixture is fresh for each test.
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient):
    """Success — revokes token, clears cookies (200)"""
    email = "logout@example.com"
    password = "StrongPassword123!"

    # 1. Register and get cookies
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Logout User",
        },
    )

    # 2. Call logout
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    # 3. Check cookies are cleared (usually by setting them to empty or expired)
    # Be careful: AsyncClient might just remove them or set them to ""
    # We should check if they are NOT present or empty.

    # Actually, httpx client updates cookies based on Set-Cookie headers.
    # If server sends Set-Cookie: access_token="", then client.cookies['access_token'] might be ""

    # Let's check if we can access protected route.
    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_logout_idempotent(client: AsyncClient):
    """Idempotent — no error when called without cookies (200)"""
    # Calling logout without being logged in should succeed (idempotent)
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient):
    """Authenticated — returns current user (200)"""
    email = "me@example.com"
    password = "StrongPassword123!"

    # 1. Register and get cookies
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Me User",
        },
    )

    # 2. Get current user
    # Cookie is sent automatically by client
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()

    # Assert fields are present
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthenticated(client: AsyncClient):
    """Unauthenticated — returns 401"""
    # Simply call without logging in.
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_google_oauth_start_redirects_and_sets_state_cookie(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """OAuth start route redirects to provider and sets signed state cookie."""

    def _fake_authorize_url(state_token: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state_token}"

    monkeypatch.setattr(
        "app.service.auth_service.build_google_oauth_authorize_url",
        _fake_authorize_url,
    )

    response = await client.get(
        "/api/v1/auth/oauth/google",
        params={"next": "/projects"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith(
        "https://accounts.google.com/o/oauth2/v2/auth"
    )
    assert "oauth_google_state" in response.cookies


@pytest.mark.asyncio
async def test_google_oauth_callback_rejects_invalid_state(client: AsyncClient):
    """OAuth callback with invalid/missing state redirects to frontend error."""
    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "test-code", "state": "invalid-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/login?oauth=error")


@pytest.mark.asyncio
async def test_oauth_google_callback_handles_provider_error_safely(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Provider-side OAuth errors redirect safely and clear callback state cookie."""

    def _fake_authorize_url(state_token: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state_token}"

    monkeypatch.setattr(
        "app.service.auth_service.build_google_oauth_authorize_url",
        _fake_authorize_url,
    )

    start = await client.get("/api/v1/auth/oauth/google", follow_redirects=False)
    assert start.status_code == 302
    assert "oauth_google_state" in start.cookies

    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"error": "access_denied"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/login?oauth=error")
    assert any(
        "oauth_google_state=" in set_cookie
        for set_cookie in response.headers.get_list("set-cookie")
    )


@pytest.mark.asyncio
async def test_google_oauth_callback_success_sets_auth_cookies_and_redirects(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """OAuth callback success sets auth cookies and redirects to next path."""

    async def _fake_login_with_google_code(*args, **kwargs):
        return (None, "oauth-access-token", "oauth-refresh-token")

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.validate_oauth_state",
        lambda expected_state, provided_state: True,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.decode_oauth_state",
        lambda state_token: {"next": "/projects"},
    )
    monkeypatch.setattr(
        "app.service.auth_service.login_with_google_code",
        _fake_login_with_google_code,
    )
    client.cookies.set("oauth_google_state", "oauth-state")

    response = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "oauth-code", "state": "oauth-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/projects")
    assert response.cookies["access_token"] == "oauth-access-token"
    assert response.cookies["refresh_token"] == "oauth-refresh-token"


@pytest.mark.asyncio
async def test_oauth_state_rejects_replay(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    OAuth callback is one-time in practice because callback state cookie is consumed.
    """

    def _fake_authorize_url(state_token: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state_token}"

    async def _fake_login_with_google_code(*args, **kwargs):
        _ = args, kwargs
        return (None, "oauth-access-token", "oauth-refresh-token")

    monkeypatch.setattr(
        "app.service.auth_service.build_google_oauth_authorize_url",
        _fake_authorize_url,
    )
    monkeypatch.setattr(
        "app.service.auth_service.login_with_google_code",
        _fake_login_with_google_code,
    )

    start = await client.get(
        "/api/v1/auth/oauth/google",
        params={"next": "/projects"},
        follow_redirects=False,
    )
    state_token = start.cookies["oauth_google_state"]

    first_callback = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "oauth-code", "state": state_token},
        follow_redirects=False,
    )
    assert first_callback.status_code == 302
    assert first_callback.headers["location"].endswith("/projects")

    replay_callback = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "oauth-code", "state": state_token},
        follow_redirects=False,
    )
    assert replay_callback.status_code == 302
    assert replay_callback.headers["location"].endswith("/login?oauth=error")


@pytest.mark.asyncio
async def test_oauth_callback_rejects_open_redirect_attempts(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """External next targets are normalized to safe in-app redirect paths."""

    def _fake_authorize_url(state_token: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?state={state_token}"

    async def _fake_login_with_google_code(*args, **kwargs):
        _ = args, kwargs
        return (None, "oauth-access-token", "oauth-refresh-token")

    monkeypatch.setattr(
        "app.service.auth_service.build_google_oauth_authorize_url",
        _fake_authorize_url,
    )
    monkeypatch.setattr(
        "app.service.auth_service.login_with_google_code",
        _fake_login_with_google_code,
    )

    start = await client.get(
        "/api/v1/auth/oauth/google",
        params={"next": "https://evil.example.com/phish"},
        follow_redirects=False,
    )
    state_token = start.cookies["oauth_google_state"]

    callback = await client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "oauth-code", "state": state_token},
        follow_redirects=False,
    )
    assert callback.status_code == 302
    location = callback.headers["location"]
    assert location.startswith(settings.FRONTEND_URL)
    assert "evil.example.com" not in location


@pytest.mark.asyncio
async def test_password_reset_request_returns_generic_success_for_unknown_email(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/auth/password-reset",
        json={"email": "unknown-user@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the email exists, reset instructions were sent."
    }


@pytest.mark.asyncio
async def test_password_reset_request_returns_generic_success_for_existing_email(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "known-reset@example.com",
            "password": "StrongPassword123!",
            "full_name": "Known Reset",
        },
    )

    response = await client.post(
        "/api/v1/auth/password-reset",
        json={"email": "known-reset@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If the email exists, reset instructions were sent."
    }


@pytest.mark.asyncio
async def test_password_reset_confirm_success_and_token_is_single_use(
    client: AsyncClient,
    session: AsyncSession,
):
    email = "password-reset-confirm@example.com"
    old_password = "StrongPassword123!"
    new_password = "StrongPassword456!"
    raw_token = "manual-reset-token"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "full_name": "Reset Confirm"},
    )
    user = await auth_service.get_user_by_email(session, email)
    assert user is not None

    session.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    await session.commit()

    confirm_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": new_password},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["message"] == "Password has been reset"

    reused_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "AnotherPassword789!"},
    )
    assert reused_response.status_code == 400
    assert reused_response.json()["error"]["code"] == "INVALID_OPERATION"

    old_login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert old_login_response.status_code == 401

    new_login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert new_login_response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_confirm_rejects_expired_token(
    client: AsyncClient,
    session: AsyncSession,
):
    email = "password-reset-expired@example.com"
    old_password = "StrongPassword123!"
    expired_token = "expired-reset-token"

    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "full_name": "Reset Expired"},
    )
    user = await auth_service.get_user_by_email(session, email)
    assert user is not None

    session.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(expired_token),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await session.commit()

    response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": expired_token, "new_password": "StrongPassword456!"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_patch_users_me_requires_authentication(client: AsyncClient):
    response = await client.patch("/api/v1/users/me", json={"full_name": "Updated"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_patch_users_me_partial_update_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile-update@example.com",
            "password": "StrongPassword123!",
            "full_name": "Profile User",
        },
    )

    response = await client.patch(
        "/api/v1/users/me",
        json={
            "full_name": "Updated Name",
            "timezone": "Europe/Stockholm",
            "preferences": {"theme": "dark", "email_notifications": True},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["timezone"] == "Europe/Stockholm"
    assert data["preferences"]["theme"] == "dark"
    assert data["preferences"]["email_notifications"] is True

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["full_name"] == "Updated Name"
    assert me_data["timezone"] == "Europe/Stockholm"
    assert me_data["preferences"]["theme"] == "dark"
    assert me_data["preferences"]["email_notifications"] is True


@pytest.mark.asyncio
async def test_patch_users_me_service_validation_error(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile-validation@example.com",
            "password": "StrongPassword123!",
            "full_name": "Profile Validation",
        },
    )

    response = await client.patch(
        "/api/v1/users/me",
        json={"timezone": ""},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_patch_users_me_rejects_unknown_fields(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile-unknown-field@example.com",
            "password": "StrongPassword123!",
            "full_name": "Profile Unknown Field",
        },
    )

    response = await client.patch(
        "/api/v1/users/me",
        json={"unknown_setting": "value"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_profile_patch_rejects_invalid_timezone_locale_avatar(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile-invalid-fields@example.com",
            "password": "StrongPassword123!",
            "full_name": "Profile Invalid Fields",
        },
    )

    timezone_response = await client.patch(
        "/api/v1/users/me",
        json={"timezone": "t" * 51},
    )
    assert timezone_response.status_code == 422

    locale_response = await client.patch(
        "/api/v1/users/me",
        json={"locale": "locale-too-long"},
    )
    assert locale_response.status_code == 422

    avatar_response = await client.patch(
        "/api/v1/users/me",
        json={"avatar_url": "https://example.com/" + ("a" * 600)},
    )
    assert avatar_response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_requires_authentication(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "old", "new_password": "StrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_change_password_success_rotates_credentials(client: AsyncClient):
    email = "change-password-success@example.com"
    old_password = "StrongPassword123!"
    new_password = "StrongPassword456!"

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": old_password,
            "full_name": "Change Password Success",
        },
    )

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": old_password,
            "new_password": new_password,
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password has been changed"

    await client.post("/api/v1/auth/logout")

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "change-password-wrong-current@example.com",
            "password": "StrongPassword123!",
            "full_name": "Change Password Wrong Current",
        },
    )

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongPassword!",
            "new_password": "StrongPassword456!",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_upload_avatar_requires_authentication(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", b"png", "image/png")},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_upload_avatar_rejects_invalid_content_type(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setattr(settings, "AVATAR_UPLOAD_SUBDIR", "avatars")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "avatar-invalid-type@example.com",
            "password": "StrongPassword123!",
            "full_name": "Avatar Invalid Type",
        },
    )

    response = await client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.gif", b"gif", "image/gif")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upload_avatar_rejects_oversized_file(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setattr(settings, "AVATAR_UPLOAD_SUBDIR", "avatars")
    monkeypatch.setattr(settings, "MAX_AVATAR_UPLOAD_BYTES", 10)

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "avatar-too-large@example.com",
            "password": "StrongPassword123!",
            "full_name": "Avatar Too Large",
        },
    )

    response = await client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", b"01234567890", "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upload_and_delete_avatar_success(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path / "media"))
    monkeypatch.setattr(settings, "AVATAR_UPLOAD_SUBDIR", "avatars")

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "avatar-success@example.com",
            "password": "StrongPassword123!",
            "full_name": "Avatar Success",
        },
    )

    upload_response = await client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", b"\x89PNG\r\n", "image/png")},
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["avatar_url"].startswith("/media/avatars/")

    delete_response = await client.delete("/api/v1/users/me/avatar")
    assert delete_response.status_code == 200
    assert delete_response.json()["avatar_url"] is None


@pytest.mark.asyncio
async def test_get_ai_preferences_includes_catalog_and_defaults(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai-preferences-get@example.com",
            "password": "StrongPassword123!",
            "full_name": "AI Preferences Get",
        },
    )

    async def fake_get_model_catalog(*, force_refresh=False):
        _ = force_refresh
        return {
            "providers": [
                {
                    "provider_id": "anthropic",
                    "display_name": "Anthropic",
                    "requires_env_key": "ANTHROPIC_API_KEY",
                    "available": True,
                    "models": [
                        {
                            "model_id": "claude-3-7-sonnet-latest",
                            "label": "Claude 3.7 Sonnet",
                            "recommended": True,
                        }
                    ],
                }
            ],
            "defaults": {
                "provider": "anthropic",
                "model": "claude-3-7-sonnet-latest",
                "mode": "live",
            },
        }

    monkeypatch.setattr(ai_service, "get_model_catalog", fake_get_model_catalog)

    response = await client.get("/api/v1/users/me/ai-preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "anthropic"
    assert data["model"] == "claude-3-7-sonnet-latest"
    assert len(data["providers"]) == 1
    assert data["defaults"]["provider"] == "anthropic"


@pytest.mark.asyncio
async def test_patch_ai_preferences_stores_provider_and_model(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai-preferences-patch@example.com",
            "password": "StrongPassword123!",
            "full_name": "AI Preferences Patch",
        },
    )

    async def fake_get_model_catalog(*, force_refresh=False):
        _ = force_refresh
        return {
            "providers": [
                {
                    "provider_id": "anthropic",
                    "display_name": "Anthropic",
                    "requires_env_key": "ANTHROPIC_API_KEY",
                    "available": True,
                    "models": [
                        {
                            "model_id": "claude-3-7-sonnet-latest",
                            "label": "Claude 3.7 Sonnet",
                            "recommended": True,
                        }
                    ],
                },
                {
                    "provider_id": "openai",
                    "display_name": "OpenAI",
                    "requires_env_key": "OPENAI_API_KEY",
                    "available": True,
                    "models": [
                        {
                            "model_id": "gpt-5-mini",
                            "label": "GPT-5 mini",
                            "recommended": True,
                        }
                    ],
                },
            ],
            "defaults": {
                "provider": "anthropic",
                "model": "claude-3-7-sonnet-latest",
                "mode": "live",
            },
        }

    monkeypatch.setattr(ai_service, "get_model_catalog", fake_get_model_catalog)

    response = await client.patch(
        "/api/v1/users/me/ai-preferences",
        json={"provider": "openai", "model": "gpt-5-mini"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-5-mini"

    me_response = await client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["preferences"]["ai"]["provider"] == "openai"
    assert me_data["preferences"]["ai"]["model"] == "gpt-5-mini"


@pytest.mark.asyncio
async def test_patch_ai_preferences_rejects_invalid_provider_model_pair(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai-preferences-invalid@example.com",
            "password": "StrongPassword123!",
            "full_name": "AI Preferences Invalid",
        },
    )

    async def fake_get_model_catalog(*, force_refresh=False):
        _ = force_refresh
        return {
            "providers": [
                {
                    "provider_id": "openai",
                    "display_name": "OpenAI",
                    "requires_env_key": "OPENAI_API_KEY",
                    "available": True,
                    "models": [
                        {
                            "model_id": "gpt-5-mini",
                            "label": "GPT-5 mini",
                            "recommended": True,
                        }
                    ],
                }
            ],
            "defaults": {
                "provider": "openai",
                "model": "gpt-5-mini",
                "mode": "live",
            },
        }

    monkeypatch.setattr(ai_service, "get_model_catalog", fake_get_model_catalog)

    response = await client.patch(
        "/api/v1/users/me/ai-preferences",
        json={"provider": "openai", "model": "gemini-2.5-flash"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_patch_ai_preferences_rejects_unavailable_provider(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai-preferences-provider-unavailable@example.com",
            "password": "StrongPassword123!",
            "full_name": "AI Preferences Unavailable Provider",
        },
    )

    async def fake_get_model_catalog(*, force_refresh=False):
        _ = force_refresh
        return {
            "providers": [
                {
                    "provider_id": "gemini",
                    "display_name": "Google Gemini",
                    "requires_env_key": "GEMINI_API_KEY",
                    "available": False,
                    "models": [
                        {
                            "model_id": "gemini-2.5-flash",
                            "label": "Gemini 2.5 Flash",
                            "recommended": True,
                        }
                    ],
                }
            ],
            "defaults": {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "mode": "live",
            },
        }

    monkeypatch.setattr(ai_service, "get_model_catalog", fake_get_model_catalog)

    response = await client.patch(
        "/api/v1/users/me/ai-preferences",
        json={"provider": "gemini", "model": "gemini-2.5-flash"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
