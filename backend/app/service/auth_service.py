"""
Authentication business logic.

Handles registration, login, token refresh, and logout.
"""

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_flow import create_email_action_token
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    InvalidOperationError,
    PermissionDeniedError,
    ResourceConflictError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.service import email_service
from app.service.organization_service import create_personal_organization

# ── Helpers ──


GOOGLE_PROVIDER = "google"
GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_OAUTH_SCOPES = "openid email profile"

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_google_redirect_uri() -> str:
    """OAuth callback URL used in Google auth code exchange."""
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI
    return f"{settings.BACKEND_URL.rstrip('/')}/api/v1/auth/oauth/google/callback"


def ensure_google_oauth_configured() -> None:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise InvalidOperationError("Google OAuth is not configured")


def build_google_oauth_authorize_url(state_token: str) -> str:
    """Build Google OAuth authorize URL."""
    ensure_google_oauth_configured()
    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": get_google_redirect_uri(),
            "response_type": "code",
            "scope": GOOGLE_OAUTH_SCOPES,
            "state": state_token,
            "access_type": "online",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{query}"


async def _get_user_by_oauth_id(
    db: AsyncSession,
    *,
    provider: str,
    oauth_id: str,
) -> User | None:
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id,
        )
    )
    return result.scalar_one_or_none()


def _get_required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AuthenticationError("Google account payload is invalid")
    return value


async def _fetch_google_userinfo(code: str) -> Mapping[str, object]:
    """Exchange Google auth code and fetch user profile."""
    ensure_google_oauth_configured()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                GOOGLE_OAUTH_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": get_google_redirect_uri(),
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise AuthenticationError("Google OAuth token exchange failed")

            token_payload = token_response.json()
            if not isinstance(token_payload, Mapping):
                raise AuthenticationError("Google OAuth token exchange failed")

            access_token = _get_required_str(token_payload, "access_token")

            userinfo_response = await client.get(
                GOOGLE_OAUTH_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise AuthenticationError("Google OAuth user lookup failed")

            profile_payload = userinfo_response.json()
            if not isinstance(profile_payload, Mapping):
                raise AuthenticationError("Google OAuth user lookup failed")

            return profile_payload
    except httpx.HTTPError as exc:
        raise AuthenticationError("Google OAuth request failed") from exc


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    normalized_email = normalize_email(email)
    result = await db.execute(select(User).where(User.email == normalized_email))
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
        raise AppException("Default 'user' role not found. Run seed migration.")
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
        expires_at=datetime.now(UTC)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    return access_token, raw_refresh


# ── Public API ──


async def _revoke_active_tokens_for_user(
    db: AsyncSession,
    *,
    user_id,
    reason: str,
) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    active_tokens = list(result.scalars().all())
    now = datetime.now(UTC)
    for token in active_tokens:
        token.is_revoked = True
        token.revoked_at = now
        token.revoked_reason = reason


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[User, str, str]:
    """Register a new user. Returns (user, access_token, refresh_token)."""
    normalized_email = normalize_email(email)

    # bcrypt only uses the first 72 bytes; enforce this explicitly to avoid
    # silent truncation and make validation behavior deterministic.
    if len(password.encode("utf-8")) > 72:
        raise ValidationError("Password must be at most 72 bytes")

    existing = await get_user_by_email(db, normalized_email)
    if existing:
        raise ResourceConflictError("Email already registered")

    role = await get_default_role(db)

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        full_name=full_name,
        system_role_id=role.id,
    )
    db.add(user)
    await db.flush()  # populate user.id

    # Create personal organization
    await create_personal_organization(db, user, commit=False)

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
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise PermissionDeniedError("Account is deactivated")

    access_token, raw_refresh = await _create_token_pair(db, user, device_info, ip)
    user.last_login_at = datetime.now(UTC)
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

    if not db_token:
        raise AuthenticationError("Invalid refresh token")
    if db_token.is_revoked:
        # Reuse detection: if a rotated refresh token is presented again,
        # revoke remaining active tokens in that user's token family.
        if db_token.revoked_reason == "rotated":
            await _revoke_active_tokens_for_user(
                db,
                user_id=db_token.user_id,
                reason="reuse_detected",
            )
            await db.commit()
        raise AuthenticationError("Invalid refresh token")
    if db_token.expires_at < datetime.now(UTC):
        raise AuthenticationError("Refresh token expired")

    # Revoke old token
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(UTC)
    db_token.revoked_reason = "rotated"

    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or deactivated")

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
        db_token.revoked_at = datetime.now(UTC)
        db_token.revoked_reason = "logout"
        await db.commit()


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """
    Create a single-use password reset token and send reset email.

    This function is intentionally silent for unknown emails. The endpoint
    always returns a generic message to prevent account enumeration.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        return

    # Invalidate any existing unused tokens first.
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.user_id == user.id,
            PasswordReset.used_at.is_(None),
        )
    )
    for old_token in result.scalars().all():
        await db.delete(old_token)

    raw_token = create_email_action_token()
    reset_token = PasswordReset(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()

    try:
        await email_service.send_password_reset_email(
            email=user.email,
            full_name=user.full_name,
            token=raw_token,
        )
    except Exception:
        # Keep response behavior enumeration-safe; request endpoint always
        # returns generic success even if downstream email delivery fails.
        logger.warning(
            "Failed to send password reset email",
            extra={"user_id": str(user.id)},
            exc_info=True,
        )


async def confirm_password_reset(
    db: AsyncSession,
    *,
    token: str,
    new_password: str,
) -> None:
    """
    Validate reset token and rotate user password.
    """
    if len(new_password.encode("utf-8")) > 72:
        raise ValidationError("Password must be at most 72 bytes")

    token_hash_value = hash_token(token)
    now = datetime.now(UTC)

    # Atomically consume reset token only if still unused + unexpired and user is active.
    # This prevents double-success under concurrent confirm requests.
    consume_result = await db.execute(
        update(PasswordReset)
        .where(
            PasswordReset.token_hash == token_hash_value,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at >= now,
            exists(
                select(User.id).where(
                    User.id == PasswordReset.user_id,
                    User.is_active.is_(True),
                )
            ),
        )
        .values(used_at=now)
        .returning(PasswordReset.user_id)
    )
    user_id = consume_result.scalar_one_or_none()
    if user_id is None:
        # Preserve error semantics for valid token + inactive account.
        candidate_result = await db.execute(
            select(PasswordReset.user_id).where(
                PasswordReset.token_hash == token_hash_value,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at >= now,
            )
        )
        candidate_user_id = candidate_result.scalar_one_or_none()
        if candidate_user_id is None:
            raise InvalidOperationError("Invalid or expired reset token")

        candidate_user = await get_user_by_id(db, candidate_user_id)
        if candidate_user is None:
            raise InvalidOperationError("Invalid or expired reset token")
        if not candidate_user.is_active:
            raise PermissionDeniedError("Account is deactivated")
        raise InvalidOperationError("Invalid or expired reset token")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise InvalidOperationError("Invalid or expired reset token")

    user.password_hash = hash_password(new_password)
    await _revoke_active_tokens_for_user(
        db,
        user_id=user.id,
        reason="password_reset",
    )
    await db.commit()


async def update_user_profile(
    db: AsyncSession,
    *,
    user: User,
    patch: Mapping[str, object],
) -> User:
    """
    Update mutable profile fields for the current user.
    """
    if "full_name" in patch:
        full_name = patch["full_name"]
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValidationError("Full name cannot be empty")
        user.full_name = full_name.strip()

    if "avatar_url" in patch:
        avatar_url = patch["avatar_url"]
        user.avatar_url = avatar_url if isinstance(avatar_url, str) else None

    if "timezone" in patch:
        timezone = patch["timezone"]
        if not isinstance(timezone, str) or not timezone.strip():
            raise ValidationError("Timezone cannot be empty")
        user.timezone = timezone.strip()

    if "locale" in patch:
        locale = patch["locale"]
        if not isinstance(locale, str) or not locale.strip():
            raise ValidationError("Locale cannot be empty")
        user.locale = locale.strip()

    if "preferences" in patch:
        preferences = patch["preferences"]
        if not isinstance(preferences, dict):
            raise ValidationError("Preferences must be an object")
        # PATCH semantics: merge provided keys into existing preferences.
        merged_preferences = dict(user.preferences or {})
        merged_preferences.update(preferences)
        user.preferences = merged_preferences

    await db.commit()
    await db.refresh(user)
    return user


async def login_with_google_code(
    db: AsyncSession,
    *,
    code: str,
    device_info: str | None = None,
    ip: str | None = None,
) -> tuple[User, str, str]:
    """
    Resolve/create a user from Google OAuth profile and issue auth tokens.
    """
    profile = await _fetch_google_userinfo(code)

    oauth_id = _get_required_str(profile, "sub")
    email = normalize_email(_get_required_str(profile, "email"))
    if profile.get("email_verified") is not True:
        raise AuthenticationError("Google account email is not verified")

    user = await _get_user_by_oauth_id(
        db,
        provider=GOOGLE_PROVIDER,
        oauth_id=oauth_id,
    )

    if user is None:
        existing_by_email = await get_user_by_email(db, email)
        if existing_by_email is not None:
            if (
                existing_by_email.oauth_provider
                and existing_by_email.oauth_provider != GOOGLE_PROVIDER
            ):
                raise ResourceConflictError(
                    "Email is already linked to another sign-in method"
                )

            if (
                existing_by_email.oauth_provider == GOOGLE_PROVIDER
                and existing_by_email.oauth_id
                and existing_by_email.oauth_id != oauth_id
            ):
                raise ResourceConflictError(
                    "Google account does not match existing linked identity"
                )

            existing_by_email.oauth_provider = GOOGLE_PROVIDER
            existing_by_email.oauth_id = oauth_id
            existing_by_email.email_verified = True

            picture = profile.get("picture")
            if not existing_by_email.avatar_url and isinstance(picture, str):
                existing_by_email.avatar_url = picture
            user = existing_by_email
        else:
            role = await get_default_role(db)
            full_name = (
                str(profile.get("name")).strip()
                if isinstance(profile.get("name"), str)
                else ""
            )
            picture = profile.get("picture")

            user = User(
                email=email,
                password_hash=None,
                full_name=full_name or email.split("@")[0],
                avatar_url=picture if isinstance(picture, str) else None,
                system_role_id=role.id,
                oauth_provider=GOOGLE_PROVIDER,
                oauth_id=oauth_id,
                email_verified=True,
            )
            db.add(user)
            await db.flush()
            await create_personal_organization(db, user, commit=False)

    if not user.is_active:
        raise PermissionDeniedError("Account is deactivated")

    access_token, raw_refresh = await _create_token_pair(db, user, device_info, ip)
    user.last_login_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh
