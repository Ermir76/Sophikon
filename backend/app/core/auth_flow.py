"""
Auth-flow helpers shared by OAuth and password-reset endpoints.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from jose import JWTError, jwt

from app.core.config import settings

PASSWORD_RESET_REQUEST_GENERIC_MESSAGE = (
    "If the email exists, reset instructions were sent."
)


def create_email_action_token(bytes_length: int = 32) -> str:
    """
    Generate a high-entropy token for email action links.
    """
    return secrets.token_urlsafe(bytes_length)


def build_frontend_url(path: str, *, params: dict[str, str] | None = None) -> str:
    """
    Build a frontend URL from configured FRONTEND_URL plus path/query params.
    """
    base = settings.FRONTEND_URL.rstrip("/")
    normalized_path = f"/{path.lstrip('/')}"
    url = f"{base}{normalized_path}"
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def build_password_reset_link(token: str) -> str:
    """
    Build the frontend reset-password link with a reset token.
    """
    return build_frontend_url("/reset-password", params={"token": token})


def _normalize_next_path(next_path: str | None) -> str:
    """
    Restrict redirect targets to relative in-app paths.
    """
    if not next_path:
        return "/"
    if not next_path.startswith("/") or next_path.startswith("//"):
        return "/"
    return next_path


def create_oauth_state(
    *,
    next_path: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create signed OAuth state with nonce and expiry.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "type": "oauth_state",
        "nonce": secrets.token_urlsafe(32),
        "next": _normalize_next_path(next_path),
        "iat": now,
        "exp": now + (expires_delta or timedelta(minutes=10)),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_oauth_state(state_token: str) -> dict[str, Any]:
    """
    Decode and validate a signed OAuth state token.
    """
    payload = jwt.decode(
        state_token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    if payload.get("type") != "oauth_state":
        raise JWTError("Invalid oauth state token type")

    nonce = payload.get("nonce")
    if not isinstance(nonce, str) or not nonce:
        raise JWTError("Invalid oauth state nonce")

    next_path = payload.get("next")
    if not isinstance(next_path, str) or not next_path.startswith("/"):
        raise JWTError("Invalid oauth state redirect path")

    return payload


def validate_oauth_state(
    expected_state: str | None,
    provided_state: str | None,
) -> bool:
    """
    Constant-time compare for double-submit oauth state checks.
    """
    if not expected_state or not provided_state:
        return False
    return secrets.compare_digest(expected_state, provided_state)
