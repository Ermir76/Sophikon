from uuid import uuid4

import pytest

from app.core.user_notification_websocket_manager import (
    UserNotificationWebSocketManager,
)


class _FakeSocket:
    def __init__(self):
        self.messages: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_dispatch_pubsub_message_targets_only_matching_user_connections():
    manager = UserNotificationWebSocketManager()
    user_a = uuid4()
    user_b = uuid4()
    socket_a = _FakeSocket()
    socket_b = _FakeSocket()

    await manager.connect(socket_a, user_id=user_a)
    await manager.connect(socket_b, user_id=user_b)

    await manager._dispatch_pubsub_message(
        {
            "user_id": str(user_a),
            "payload": {"type": "notification_created", "unread_count": 2},
        }
    )

    assert socket_a.messages == [{"type": "notification_created", "unread_count": 2}]
    assert socket_b.messages == []


@pytest.mark.asyncio
async def test_disconnect_removes_connection():
    manager = UserNotificationWebSocketManager()
    user_id = uuid4()
    socket = _FakeSocket()

    connection_id = await manager.connect(socket, user_id=user_id)
    assert str(user_id) in manager._connections

    await manager.disconnect(connection_id, user_id)
    assert str(user_id) not in manager._connections
