"""
Authentication business logic.

Handles registration, login, token refresh, and logout.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.service.organization_service import create_personal_organization


# ── Helpers ──


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_default_role(db: AsyncSession) -> Role:
    result = await db.execute(
        select(Role).where(Role.name == "user", Role.scope == "system")
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default 'user' role not found. Run seed migration.",
        )
    return role


async def _create_token_pair(
    db: AsyncSession,
    user: User,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[str, str]:
    """Create an access + refresh token pair and persist the refresh token."""
    access_token = create_access_token(subject=str(user.id))
    raw_refresh = create_refresh_token()

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        device_info=device_info,
        ip_address=ip,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    return access_token, raw_refresh


# ── Public API ──


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[User, str, str]:
    """Register a new user. Returns (user, access_token, refresh_token)."""
    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    role = await get_default_role(db)

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        system_role_id=role.id,
    )
    db.add(user)
    await db.flush()  # populate user.id

    # Create personal organization
    await create_personal_organization(db, user)

    access_token, raw_refresh = await _create_token_pair(db, user, device_info, ip)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[User, str, str]:
    """Authenticate and return (user, access_token, refresh_token)."""
    user = await get_user_by_email(db, email)
    if (
        not user
        or not user.password_hash
        or not verify_password(password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token, raw_refresh = await _create_token_pair(db, user, device_info, ip)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    # Return tokens separately so controller can set cookies
    return user, access_token, raw_refresh


async def refresh_tokens(
    db: AsyncSession,
    raw_refresh_token: str,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[User, str, str]:
    """Rotate a refresh token. Returns (user, new_access, new_refresh)."""
    token_hash = hash_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke old token
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db_token.revoked_reason = "rotated"

    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    access_token, raw_refresh = await _create_token_pair(db, user, device_info, ip)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh


async def logout_user(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a refresh token. Idempotent — always succeeds."""
    token_hash = hash_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()
    if db_token and not db_token.is_revoked:
        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db_token.revoked_reason = "logout"
        await db.commit()
