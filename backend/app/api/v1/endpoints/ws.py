"""
Project-scoped websocket endpoint for realtime updates and presence.
"""

from uuid import UUID

from fastapi import APIRouter, WebSocket

from app.api.ws_auth import resolve_project_socket_context, resolve_user_socket
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
)
from app.schema.realtime import RealtimeChannel
from app.service.ws_session_service import (
    serve_notification_socket,
    serve_project_socket,
)

router = APIRouter(tags=["ws"])

DEFAULT_CHANNELS: set[RealtimeChannel] = {
    "tasks",
    "resources",
    "members",
    "activity",
    "project",
    "comments",
}
TERMINAL_PROTOCOL_CLOSE_CODE = 4400


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: UUID):
    try:
        user, access = await resolve_project_socket_context(websocket, project_id)
    except Exception as exc:
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
    await serve_project_socket(
        websocket,
        user=user,
        access=access,
        default_channels=set(DEFAULT_CHANNELS),
        terminal_close_code=TERMINAL_PROTOCOL_CLOSE_CODE,
    )


@router.websocket("/ws/notifications")
async def notification_websocket(websocket: WebSocket):
    try:
        user = await resolve_user_socket(websocket)
    except Exception as exc:
        if isinstance(exc, AuthenticationError):
            await websocket.accept()
            await websocket.close(code=4401)
            return
        raise

    await websocket.accept()
    await serve_notification_socket(
        websocket,
        user=user,
        terminal_close_code=TERMINAL_PROTOCOL_CLOSE_CODE,
    )
