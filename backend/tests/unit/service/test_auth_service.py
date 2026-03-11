import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ResourceConflictError,
)
from app.core.security import decode_access_token, hash_token, verify_password
from app.models.enums import RoleScope
from app.models.refresh_token import RefreshToken
from app.models.role import Role
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
