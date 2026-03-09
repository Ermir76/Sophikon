"""
WebSocket session handlers for project realtime and user notifications.
"""

from collections.abc import Awaitable, Callable

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ProjectAccess
from app.core.database import AsyncSessionLocal
from app.core.user_notification_websocket_manager import (
    user_notification_websocket_manager,
)
from app.core.websocket_manager import websocket_manager
from app.models.user import User
from app.schema.realtime import RealtimeChannel
from app.service import notification_service
from app.service.ws_protocol import (
    build_error_payload,
    parse_notification_client_message,
    parse_project_client_message,
)


async def _with_session[T](handler: Callable[[AsyncSession], Awaitable[T]]) -> T:
    async with AsyncSessionLocal() as db:
        return await handler(db)


async def serve_project_socket(
    websocket: WebSocket,
    *,
    user: User,
    access: ProjectAccess,
    default_channels: set[RealtimeChannel],
    terminal_close_code: int,
) -> None:
    connection_id, snapshot = await websocket_manager.connect(
        websocket,
        project_id=access.project.id,
        user_id=user.id,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        channels=set(default_channels),
    )
    await websocket.send_json(snapshot)
    await websocket_manager.publish_presence(access.project.id)

    try:
        while True:
            payload = await websocket.receive_json()
            parsed = parse_project_client_message(payload)

            if parsed.kind == "malformed":
                await websocket.send_json(
                    build_error_payload(
                        code="INVALID_MESSAGE",
                        message="Malformed websocket payload",
                    )
                )
                await websocket.close(code=terminal_close_code)
                return

            if parsed.kind == "subscribe":
                await websocket_manager.update_subscriptions(
                    connection_id,
                    access.project.id,
                    set(parsed.channels),
                )
                continue

            if parsed.kind == "presence":
                await websocket_manager.update_presence(
                    connection_id=connection_id,
                    project_id=access.project.id,
                    user_id=user.id,
                    full_name=user.full_name,
                    avatar_url=user.avatar_url,
                    status=parsed.status,
                    entity_type=parsed.entity_type,
                    entity_id=parsed.entity_id,
                )
                continue

            await websocket.send_json(
                build_error_payload(
                    code="INVALID_MESSAGE_TYPE",
                    message="Unsupported websocket message type",
                )
            )
    except ValueError:
        await websocket.send_json(
            build_error_payload(
                code="INVALID_MESSAGE",
                message="Malformed websocket payload",
            )
        )
        await websocket.close(code=terminal_close_code)
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id, access.project.id)


async def serve_notification_socket(
    websocket: WebSocket,
    *,
    user: User,
    terminal_close_code: int,
) -> None:
    connection_id = await user_notification_websocket_manager.connect(
        websocket,
        user_id=user.id,
    )
    snapshot = await _with_session(
        lambda db: notification_service.build_snapshot_payload(db, user_id=user.id)
    )
    await websocket.send_json(snapshot)

    try:
        while True:
            payload = await websocket.receive_json()
            parsed = parse_notification_client_message(payload)

            if parsed.kind == "malformed":
                await websocket.send_json(
                    build_error_payload(
                        code="INVALID_MESSAGE",
                        message="Malformed websocket payload",
                    )
                )
                await websocket.close(code=terminal_close_code)
                return

            await websocket.send_json(
                build_error_payload(
                    code="INVALID_MESSAGE_TYPE",
                    message="Unsupported websocket message type",
                )
            )
    except ValueError:
        await websocket.send_json(
            build_error_payload(
                code="INVALID_MESSAGE",
                message="Malformed websocket payload",
            )
        )
        await websocket.close(code=terminal_close_code)
    except WebSocketDisconnect:
        pass
    finally:
        await user_notification_websocket_manager.disconnect(connection_id, user.id)
