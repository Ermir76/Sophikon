from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.api.deps.auth import authenticate_access_token
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    InvalidOperationError,
    PermissionDeniedError,
    ResourceConflictError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_token,
    verify_password,
)
from app.models.enums import RoleScope
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.service import auth_service


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


def _unique_value(prefix: str) -> str:
    return f"{prefix}-{uuid7()}"


@pytest.mark.asyncio
async def test_register_user_hashes_password_and_persists_refresh_token(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    password = "StrongPassword123!"
    email = _unique_email("auth-register")

    user, access_token, refresh_token = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Register",
    )

    assert user.email == email
    assert user.password_hash != password
    assert verify_password(password, user.password_hash or "")

    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"
    assert "exp" in payload

    tokens_result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    tokens = list(tokens_result.scalars().all())
    assert len(tokens) == 1
    assert tokens[0].token_hash == hash_token(refresh_token)
    assert tokens[0].is_revoked is False


@pytest.mark.asyncio
async def test_register_user_rejects_password_over_72_bytes(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-register-too-long")
    too_long_password = "a" * 73

    with pytest.raises(ValidationError):
        await auth_service.register_user(
            session,
            email,
            too_long_password,
            "Auth Too Long",
        )


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email(session: AsyncSession) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-duplicate")

    await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Auth Duplicate",
    )

    with pytest.raises(ResourceConflictError):
        await auth_service.register_user(
            session,
            email,
            "StrongPassword123!",
            "Auth Duplicate Again",
        )


@pytest.mark.asyncio
async def test_register_user_creates_user_with_correct_fields(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-register-fields")
    full_name = "Auth Correct Fields"

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        full_name,
    )

    assert user.email == email
    assert user.full_name == full_name
    assert user.is_active is True
    assert user.system_role_id is not None


@pytest.mark.asyncio
async def test_register_user_normalizes_email_and_rejects_case_duplicate(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    mixed_case_email = _unique_email("auth-case-duplicate").upper()

    user, _, _ = await auth_service.register_user(
        session,
        mixed_case_email,
        "StrongPassword123!",
        "Auth Case Duplicate",
    )
    assert user.email == mixed_case_email.strip().lower()

    with pytest.raises(ResourceConflictError):
        await auth_service.register_user(
            session,
            mixed_case_email.lower(),
            "StrongPassword123!",
            "Auth Case Duplicate Again",
        )


@pytest.mark.asyncio
async def test_login_user_returns_tokens_for_valid_credentials(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-login-ok")
    password = "StrongPassword123!"

    user, _, _ = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Login",
    )
    logged_user, access_token, refresh_token = await auth_service.login_user(
        session,
        email,
        password,
    )

    assert logged_user.id == user.id
    assert refresh_token
    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_login_user_accepts_mixed_case_email_lookup(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    base_email = _unique_email("auth-login-case")
    password = "StrongPassword123!"

    user, _, _ = await auth_service.register_user(
        session,
        base_email,
        password,
        "Auth Login Case",
    )

    mixed_case_email = f"  {base_email.upper()}  "
    logged_user, _, _ = await auth_service.login_user(
        session,
        mixed_case_email,
        password,
    )
    assert logged_user.id == user.id


@pytest.mark.asyncio
async def test_access_token_expires_after_configured_minutes(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-token-exp")
    password = "StrongPassword123!"

    _, access_token, _ = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Token Exp",
    )
    payload = decode_access_token(access_token)
    iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    ttl_seconds = int((exp - iat).total_seconds())

    assert ttl_seconds == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


@pytest.mark.asyncio
async def test_login_user_rejects_wrong_password(session: AsyncSession) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-login-wrong-password")

    await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Auth Wrong Password",
    )

    with pytest.raises(AuthenticationError):
        await auth_service.login_user(
            session,
            email,
            "WrongPassword!",
        )


@pytest.mark.asyncio
async def test_login_user_rejects_inactive_user(session: AsyncSession) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-login-inactive")
    password = "StrongPassword123!"

    user, _, _ = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Inactive",
    )
    user.is_active = False
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await auth_service.login_user(
            session,
            email,
            password,
        )


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_and_revokes_old_token(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-refresh")
    password = "StrongPassword123!"

    user, _, old_refresh_token = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Refresh",
    )
    refreshed_user, access_token, new_refresh_token = await auth_service.refresh_tokens(
        session,
        old_refresh_token,
    )

    assert refreshed_user.id == user.id
    assert new_refresh_token != old_refresh_token
    decoded = decode_access_token(access_token)
    assert decoded["sub"] == str(user.id)
    assert decoded["type"] == "access"

    old_token_result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(old_refresh_token)
        )
    )
    old_token = old_token_result.scalar_one()
    assert old_token.is_revoked is True
    assert old_token.revoked_reason == "rotated"

    new_token_result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(new_refresh_token)
        )
    )
    new_token = new_token_result.scalar_one()
    assert new_token.is_revoked is False

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_tokens(session, old_refresh_token)


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_expired_token(session: AsyncSession) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-refresh-expired")
    password = "StrongPassword123!"

    user, _, old_refresh_token = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Refresh Expired",
    )

    token_result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(old_refresh_token)
        )
    )
    token = token_result.scalar_one()
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await session.commit()

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_tokens(session, old_refresh_token)

    await session.refresh(user)
    assert user.id is not None


@pytest.mark.asyncio
async def test_refresh_tokens_rejects_malformed_token(session: AsyncSession) -> None:
    await _ensure_system_user_role(session)

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_tokens(session, "not-a-valid-refresh-token")


@pytest.mark.asyncio
async def test_refresh_reuse_detection_revokes_active_token_family(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-refresh-reuse")
    password = "StrongPassword123!"

    _, _, old_refresh_token = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Refresh Reuse",
    )
    _, _, rotated_refresh_token = await auth_service.refresh_tokens(
        session,
        old_refresh_token,
    )

    with pytest.raises(AuthenticationError):
        await auth_service.refresh_tokens(session, old_refresh_token)
    with pytest.raises(AuthenticationError):
        await auth_service.refresh_tokens(session, rotated_refresh_token)

    rotated_result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(rotated_refresh_token)
        )
    )
    rotated_token = rotated_result.scalar_one()
    assert rotated_token.is_revoked is True
    assert rotated_token.revoked_reason == "reuse_detected"


@pytest.mark.asyncio
async def test_expired_access_token_raises_authentication_error(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-access-expired")

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Auth Access Expired",
    )
    expired_access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(AuthenticationError):
        await authenticate_access_token(session, expired_access_token)


@pytest.mark.asyncio
async def test_logout_user_revokes_token_and_is_idempotent(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-logout")
    password = "StrongPassword123!"

    _, _, refresh_token = await auth_service.register_user(
        session,
        email,
        password,
        "Auth Logout",
    )

    await auth_service.logout_user(session, refresh_token)
    await auth_service.logout_user(session, refresh_token)

    token_result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    token = token_result.scalar_one()
    assert token.is_revoked is True
    assert token.revoked_reason == "logout"


@pytest.mark.asyncio
async def test_request_password_reset_stores_hashed_token_and_sends_email(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-reset-store")
    raw_token = _unique_value("fixed-reset-token")
    sent_payload: dict[str, str] = {}

    async def _fake_send_password_reset_email(
        *, email: str, full_name: str, token: str
    ):
        sent_payload["email"] = email
        sent_payload["full_name"] = full_name
        sent_payload["token"] = token

    monkeypatch.setattr(
        "app.service.auth_service.create_email_action_token",
        lambda: raw_token,
    )
    monkeypatch.setattr(
        "app.service.email_service.send_password_reset_email",
        _fake_send_password_reset_email,
    )

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Reset Store",
    )

    await auth_service.request_password_reset(session, email)

    reset_result = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    rows = list(reset_result.scalars().all())
    assert len(rows) == 1
    assert rows[0].token_hash == hash_token(raw_token)
    assert rows[0].used_at is None
    assert rows[0].expires_at > datetime.now(UTC)

    assert sent_payload["email"] == email
    assert sent_payload["full_name"] == "Reset Store"
    assert sent_payload["token"] == raw_token


@pytest.mark.asyncio
async def test_request_password_reset_accepts_mixed_case_email_lookup(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-reset-case")
    raw_token = _unique_value("reset-case-token")

    async def _noop_send_password_reset_email(
        *, email: str, full_name: str, token: str
    ):
        _ = email, full_name, token
        return None

    monkeypatch.setattr(
        "app.service.auth_service.create_email_action_token",
        lambda: raw_token,
    )
    monkeypatch.setattr(
        "app.service.email_service.send_password_reset_email",
        _noop_send_password_reset_email,
    )

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Reset Case",
    )

    await auth_service.request_password_reset(session, f"  {email.upper()}  ")

    reset_result = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    rows = list(reset_result.scalars().all())
    assert len(rows) == 1
    assert rows[0].token_hash == hash_token(raw_token)


@pytest.mark.asyncio
async def test_request_password_reset_invalidates_previous_unused_tokens(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-reset-rotate")
    token_one = _unique_value("token-one")
    token_two = _unique_value("token-two")
    tokens = iter([token_one, token_two])

    async def _noop_send_password_reset_email(
        *, email: str, full_name: str, token: str
    ):
        _ = email, full_name, token
        return None

    monkeypatch.setattr(
        "app.service.auth_service.create_email_action_token",
        lambda: next(tokens),
    )
    monkeypatch.setattr(
        "app.service.email_service.send_password_reset_email",
        _noop_send_password_reset_email,
    )

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Reset Rotate",
    )

    await auth_service.request_password_reset(session, email)
    await auth_service.request_password_reset(session, email)

    reset_result = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    rows = list(reset_result.scalars().all())
    assert len(rows) == 1
    assert rows[0].token_hash == hash_token(token_two)


@pytest.mark.asyncio
async def test_confirm_password_reset_marks_token_used_and_revokes_refresh_tokens(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-reset-confirm")
    old_password = "StrongPassword123!"
    new_password = "StrongPassword456!"
    raw_reset_token = _unique_value("raw-reset-token")

    user, _, refresh_token = await auth_service.register_user(
        session,
        email,
        old_password,
        "Reset Confirm",
    )
    session.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(raw_reset_token),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    await session.commit()

    await auth_service.confirm_password_reset(
        session,
        token=raw_reset_token,
        new_password=new_password,
    )

    user_result = await session.execute(select(User).where(User.id == user.id))
    updated_user = user_result.scalar_one()
    assert verify_password(new_password, updated_user.password_hash or "")

    reset_result = await session.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id)
    )
    reset_row = reset_result.scalar_one()
    assert reset_row.used_at is not None

    refresh_result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    refresh_row = refresh_result.scalar_one()
    assert refresh_row.is_revoked is True
    assert refresh_row.revoked_reason == "password_reset"

    with pytest.raises(AuthenticationError):
        await auth_service.login_user(session, email, old_password)
    logged_in_user, _, _ = await auth_service.login_user(session, email, new_password)
    assert logged_in_user.id == user.id


@pytest.mark.asyncio
async def test_confirm_password_reset_rejects_expired_token(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-reset-expired")
    expired_token = _unique_value("expired-token")

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Reset Expired",
    )
    session.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(expired_token),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    await session.commit()

    with pytest.raises(InvalidOperationError):
        await auth_service.confirm_password_reset(
            session,
            token=expired_token,
            new_password="StrongPassword456!",
        )


@pytest.mark.asyncio
async def test_update_user_profile_updates_allowed_fields_only(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-profile-update")

    user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Profile Original",
    )
    updated = await auth_service.update_user_profile(
        session,
        user=user,
        patch={
            "full_name": "Profile Updated",
            "timezone": "Europe/Stockholm",
            "locale": "sv-SE",
            "avatar_url": "https://example.com/avatar.png",
            "preferences": {"theme": "dark", "email_notifications": True},
            "email": "should-not-change@example.com",
        },
    )

    assert updated.full_name == "Profile Updated"
    assert updated.timezone == "Europe/Stockholm"
    assert updated.locale == "sv-SE"
    assert updated.avatar_url == "https://example.com/avatar.png"
    assert updated.preferences["theme"] == "dark"
    assert updated.preferences["email_notifications"] is True
    assert updated.email == email


@pytest.mark.asyncio
async def test_update_user_profile_rejects_blank_timezone_and_locale(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    user, _, _ = await auth_service.register_user(
        session,
        _unique_email("auth-profile-validation"),
        "StrongPassword123!",
        "Profile Validation",
    )

    with pytest.raises(ValidationError):
        await auth_service.update_user_profile(
            session,
            user=user,
            patch={"timezone": ""},
        )

    with pytest.raises(ValidationError):
        await auth_service.update_user_profile(
            session,
            user=user,
            patch={"locale": "   "},
        )


@pytest.mark.asyncio
async def test_update_user_profile_merges_preferences_patch(
    session: AsyncSession,
) -> None:
    await _ensure_system_user_role(session)
    user, _, _ = await auth_service.register_user(
        session,
        _unique_email("auth-profile-preferences"),
        "StrongPassword123!",
        "Profile Preferences",
    )
    user.preferences = {"theme": "light", "email_notifications": False}
    await session.commit()

    updated = await auth_service.update_user_profile(
        session,
        user=user,
        patch={"preferences": {"theme": "dark"}},
    )

    assert updated.preferences["theme"] == "dark"
    assert updated.preferences["email_notifications"] is False


@pytest.mark.asyncio
async def test_login_with_google_code_creates_user_and_persists_refresh_token(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    google_sub = _unique_value("google-sub")
    google_profile = {
        "sub": google_sub,
        "email": _unique_email("auth-google-create"),
        "name": "Google Created User",
        "picture": "https://example.com/google.png",
        "email_verified": True,
    }

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return google_profile

    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    user, access_token, refresh_token = await auth_service.login_with_google_code(
        session,
        code="oauth-code",
    )

    assert user.email == google_profile["email"]
    assert user.oauth_provider == "google"
    assert user.oauth_id == google_sub
    assert user.email_verified is True
    assert user.password_hash is None

    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"

    token_result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    persisted = token_result.scalar_one()
    assert persisted.user_id == user.id
    assert persisted.is_revoked is False


@pytest.mark.asyncio
async def test_login_with_google_code_links_existing_email_user(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-google-link")
    google_sub = _unique_value("google-sub-link")
    existing_user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Local User",
    )
    assert existing_user.oauth_provider is None

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return {
            "sub": google_sub,
            "email": email,
            "name": "Local User",
            "picture": "https://example.com/avatar.png",
            "email_verified": True,
        }

    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    linked_user, _, _ = await auth_service.login_with_google_code(
        session,
        code="oauth-code",
    )
    assert linked_user.id == existing_user.id
    assert linked_user.oauth_provider == "google"
    assert linked_user.oauth_id == google_sub


@pytest.mark.asyncio
async def test_login_with_google_code_rejects_conflicting_provider_link(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)
    email = _unique_email("auth-google-conflict")
    google_sub = _unique_value("google-sub-conflict")
    existing_user, _, _ = await auth_service.register_user(
        session,
        email,
        "StrongPassword123!",
        "Conflict User",
    )
    existing_user.oauth_provider = "github"
    existing_user.oauth_id = _unique_value("github-sub")
    await session.commit()

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return {
            "sub": google_sub,
            "email": email,
            "name": "Conflict User",
            "picture": "https://example.com/conflict.png",
            "email_verified": True,
        }

    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    with pytest.raises(ResourceConflictError):
        await auth_service.login_with_google_code(
            session,
            code="oauth-code",
        )


@pytest.mark.asyncio
async def test_login_with_google_code_rejects_unverified_email_claim(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return {
            "sub": "google-sub-unverified",
            "email": _unique_email("auth-google-unverified"),
            "name": "Unverified Google User",
            "picture": "https://example.com/unverified.png",
            "email_verified": False,
        }

    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    with pytest.raises(AuthenticationError):
        await auth_service.login_with_google_code(
            session,
            code="oauth-code",
        )


@pytest.mark.asyncio
async def test_login_with_google_code_rejects_missing_verified_email_claim(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _ensure_system_user_role(session)

    async def _fake_fetch_google_userinfo(code: str):
        _ = code
        return {
            "sub": "google-sub-missing-verified",
            "email": _unique_email("auth-google-missing-verified"),
            "name": "Missing Verified Claim",
            "picture": "https://example.com/missing-verified.png",
        }

    monkeypatch.setattr(
        "app.service.auth_service._fetch_google_userinfo",
        _fake_fetch_google_userinfo,
    )

    with pytest.raises(AuthenticationError):
        await auth_service.login_with_google_code(
            session,
            code="oauth-code",
        )
