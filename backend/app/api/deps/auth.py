"""
Authentication dependencies and token helpers.
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.models.user import User
from app.service.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def normalize_access_token(token: str | None) -> str | None:
    if token is None:
        return None
    if token.lower().startswith("bearer "):
        return token.split(" ", 1)[1]
    return token


async def authenticate_access_token(
    db: AsyncSession,
    token: str | None,
) -> User:
    token = normalize_access_token(token)
    if not token:
        raise AuthenticationError("Could not validate credentials")

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Could not validate credentials")
    except JWTError:
        raise AuthenticationError("Could not validate credentials")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise AuthenticationError("Could not validate credentials")
    return user


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User:
    # If header token is missing, check cookie
    if not token:
        token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    return await authenticate_access_token(db, token)


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_active:
        raise PermissionDeniedError("Inactive user")
    return user
