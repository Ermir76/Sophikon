"""
Project-scoped websocket endpoint for realtime updates and presence.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    authenticate_access_token,
    get_project_membership_for_user,
    normalize_access_token,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.websocket_manager import websocket_manager
from app.schema.realtime import (
    PresenceMessage,
    RealtimeErrorMessage,
    SubscribeMessage,
)

router = APIRouter(tags=["ws"])

DEFAULT_CHANNELS = {"tasks", "resources", "members", "activity", "project"}
TERMINAL_PROTOCOL_CLOSE_CODE = 4400


async def _with_session[T](handler: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async with AsyncSessionLocal() as db:
        return await handler(db)


async def _resolve_socket_context(websocket: WebSocket, project_id: UUID):
    async def _handler(db: AsyncSession):
        token = normalize_access_token(
            websocket.query_params.get("token")
            or websocket.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
            or websocket.headers.get("authorization")
        )
        user = await authenticate_access_token(db, token)
        access = await get_project_membership_for_user(db, project_id, user)
        return user, access

    return await _with_session(_handler)


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: UUID):
    try:
        user, access = await _resolve_socket_context(websocket, project_id)
    except Exception as exc:
        from app.core.exceptions import (
            AuthenticationError,
            NotFoundError,
            PermissionDeniedError,
        )

        close_code = None
        if isinstance(exc, AuthenticationError):
            close_code = 4401
        elif isinstance(exc, PermissionDeniedError):
            close_code = 4403
        elif isinstance(exc, NotFoundError):
            close_code = 4404
        if close_code is not None:
            await websocket.accept()
            await websocket.close(code=close_code)
            return
        raise

    await websocket.accept()
    connection_id, snapshot = await websocket_manager.connect(
        websocket,
        project_id=access.project.id,
        user_id=user.id,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        channels=set(DEFAULT_CHANNELS),
    )
    await websocket.send_json(snapshot)
    await websocket_manager.publish_presence(access.project.id)

    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")

            if message_type == "subscribe":
                message = SubscribeMessage.model_validate(payload)
                await websocket_manager.update_subscriptions(
                    connection_id,
                    access.project.id,
                    set(message.channels),
                )
                continue

            if message_type == "presence":
                message = PresenceMessage.model_validate(payload)
                await websocket_manager.update_presence(
                    connection_id=connection_id,
                    project_id=access.project.id,
                    user_id=user.id,
                    full_name=user.full_name,
                    avatar_url=user.avatar_url,
                    status=message.status,
                    entity_type=message.entity_type,
                    entity_id=message.entity_id,
                )
                continue

            await websocket.send_json(
                RealtimeErrorMessage(
                    code="INVALID_MESSAGE_TYPE",
                    message="Unsupported websocket message type",
                ).model_dump(mode="json")
            )
            continue
    except ValidationError:
        await websocket.send_json(
            RealtimeErrorMessage(
                code="INVALID_MESSAGE",
                message="Malformed websocket payload",
            ).model_dump(mode="json")
        )
        await websocket.close(code=TERMINAL_PROTOCOL_CLOSE_CODE)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id, access.project.id)
