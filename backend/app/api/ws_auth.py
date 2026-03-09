"""
WebSocket authentication and access-context helpers.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    authenticate_access_token,
    get_project_membership_for_user,
    normalize_access_token,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal


async def _with_session[T](handler: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async with AsyncSessionLocal() as db:
        return await handler(db)


def _resolve_websocket_token(websocket: WebSocket) -> str | None:
    return normalize_access_token(
        websocket.query_params.get("token")
        or websocket.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        or websocket.headers.get("authorization")
    )


async def resolve_project_socket_context(websocket: WebSocket, project_id: UUID):
    async def _handler(db: AsyncSession):
        token = _resolve_websocket_token(websocket)
        user = await authenticate_access_token(db, token)
        access = await get_project_membership_for_user(db, project_id, user)
        return user, access

    return await _with_session(_handler)


async def resolve_user_socket(websocket: WebSocket):
    async def _handler(db: AsyncSession):
        token = _resolve_websocket_token(websocket)
        return await authenticate_access_token(db, token)

    return await _with_session(_handler)
