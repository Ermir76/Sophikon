from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import WebSocketDisconnect

from app.service import ws_session_service


class FakeWebSocket:
    def __init__(self, messages: list[object] | None = None):
        self._messages = list(messages or [])
        self.sent: list[dict] = []
        self.close_code: int | None = None

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    async def close(self, code: int = 1000) -> None:
        self.close_code = code

    async def receive_json(self):
        if not self._messages:
            raise WebSocketDisconnect(code=1000)
        message = self._messages.pop(0)
        if isinstance(message, BaseException):
            raise message
        return message


class FakeProjectWebSocketManager:
    def __init__(self):
        self.connect_calls: list[dict] = []
        self.publish_presence_calls: list[str] = []
        self.update_subscriptions_calls: list[tuple[str, str, set[str]]] = []
        self.update_presence_calls: list[dict] = []
        self.disconnect_calls: list[tuple[str, str]] = []

    async def connect(
        self,
        websocket,
        *,
        project_id,
        user_id,
        full_name,
        avatar_url,
        channels,
    ):
        self.connect_calls.append(
            {
                "websocket": websocket,
                "project_id": str(project_id),
                "user_id": str(user_id),
                "full_name": full_name,
                "avatar_url": avatar_url,
                "channels": set(channels),
            }
        )
        return (
            "project-conn-1",
            {"type": "presence_snapshot", "project_id": str(project_id), "users": []},
        )

    async def publish_presence(self, project_id):
        self.publish_presence_calls.append(str(project_id))

    async def update_subscriptions(self, connection_id, project_id, channels):
        self.update_subscriptions_calls.append(
            (connection_id, str(project_id), set(channels))
        )

    async def update_presence(self, **kwargs):
        self.update_presence_calls.append(kwargs)

    async def disconnect(self, connection_id, project_id):
        self.disconnect_calls.append((connection_id, str(project_id)))


class FakeUserNotificationManager:
    def __init__(self):
        self.connect_calls: list[dict] = []
        self.disconnect_calls: list[tuple[str, str]] = []

    async def connect(self, websocket, *, user_id):
        self.connect_calls.append({"websocket": websocket, "user_id": str(user_id)})
        return "notification-conn-1"

    async def disconnect(self, connection_id, user_id):
        self.disconnect_calls.append((connection_id, str(user_id)))


@pytest.mark.asyncio
async def test_serve_project_socket_connects_and_dispatches_messages(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeProjectWebSocketManager()
    monkeypatch.setattr(ws_session_service, "websocket_manager", manager)

    project_id = uuid4()
    entity_id = uuid4()
    user = SimpleNamespace(id=uuid4(), full_name="WS User", avatar_url=None)
    websocket = FakeWebSocket(
        messages=[
            {"type": "subscribe", "channels": ["activity", "project"]},
            {
                "type": "presence",
                "status": "editing",
                "entity_type": "task",
                "entity_id": str(entity_id),
            },
            WebSocketDisconnect(code=1000),
        ]
    )

    await ws_session_service.serve_project_socket(
        websocket,
        user=user,
        project_id=project_id,
        default_channels={"tasks", "activity"},
        terminal_close_code=4400,
    )

    assert websocket.sent == [
        {"type": "presence_snapshot", "project_id": str(project_id), "users": []}
    ]
    assert manager.connect_calls[0]["project_id"] == str(project_id)
    assert manager.publish_presence_calls == [str(project_id)]
    assert manager.update_subscriptions_calls == [
        ("project-conn-1", str(project_id), {"activity", "project"})
    ]
    assert manager.update_presence_calls[0]["status"] == "editing"
    assert str(manager.update_presence_calls[0]["entity_id"]) == str(entity_id)
    assert manager.disconnect_calls == [("project-conn-1", str(project_id))]
    assert websocket.close_code is None


@pytest.mark.asyncio
async def test_serve_project_socket_closes_on_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeProjectWebSocketManager()
    monkeypatch.setattr(ws_session_service, "websocket_manager", manager)

    project_id = uuid4()
    user = SimpleNamespace(id=uuid4(), full_name="WS User", avatar_url=None)
    websocket = FakeWebSocket(messages=[{"type": "presence", "status": "editing"}])

    await ws_session_service.serve_project_socket(
        websocket,
        user=user,
        project_id=project_id,
        default_channels={"tasks"},
        terminal_close_code=4400,
    )

    assert websocket.close_code == 4400
    assert websocket.sent[1] == {
        "type": "error",
        "code": "INVALID_MESSAGE",
        "message": "Malformed websocket payload",
    }
    assert manager.disconnect_calls == [("project-conn-1", str(project_id))]


@pytest.mark.asyncio
async def test_serve_project_socket_keeps_open_on_unknown_message_type(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeProjectWebSocketManager()
    monkeypatch.setattr(ws_session_service, "websocket_manager", manager)

    project_id = uuid4()
    user = SimpleNamespace(id=uuid4(), full_name="WS User", avatar_url=None)
    websocket = FakeWebSocket(
        messages=[
            {"type": "ping"},
            WebSocketDisconnect(code=1000),
        ]
    )

    await ws_session_service.serve_project_socket(
        websocket,
        user=user,
        project_id=project_id,
        default_channels={"tasks"},
        terminal_close_code=4400,
    )

    assert websocket.close_code is None
    assert websocket.sent[1] == {
        "type": "error",
        "code": "INVALID_MESSAGE_TYPE",
        "message": "Unsupported websocket message type",
    }
    assert manager.disconnect_calls == [("project-conn-1", str(project_id))]


@pytest.mark.asyncio
async def test_serve_notification_socket_sends_snapshot_and_unknown_error(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeUserNotificationManager()
    monkeypatch.setattr(
        ws_session_service,
        "user_notification_websocket_manager",
        manager,
    )

    async def _with_session(handler):
        return await handler(None)

    async def _build_snapshot_payload(db, *, user_id):
        _ = db, user_id
        return {"type": "notification_snapshot", "unread_count": 5}

    monkeypatch.setattr(ws_session_service, "_with_session", _with_session)
    monkeypatch.setattr(
        ws_session_service.notification_service,
        "build_snapshot_payload",
        _build_snapshot_payload,
    )

    user = SimpleNamespace(id=uuid4())
    websocket = FakeWebSocket(
        messages=[
            {"type": "ping"},
            WebSocketDisconnect(code=1000),
        ]
    )

    await ws_session_service.serve_notification_socket(
        websocket,
        user=user,
        terminal_close_code=4400,
    )

    assert websocket.sent == [
        {"type": "notification_snapshot", "unread_count": 5},
        {
            "type": "error",
            "code": "INVALID_MESSAGE_TYPE",
            "message": "Unsupported websocket message type",
        },
    ]
    assert websocket.close_code is None
    assert manager.disconnect_calls == [("notification-conn-1", str(user.id))]


@pytest.mark.asyncio
async def test_serve_notification_socket_closes_on_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeUserNotificationManager()
    monkeypatch.setattr(
        ws_session_service,
        "user_notification_websocket_manager",
        manager,
    )

    async def _with_session(handler):
        return await handler(None)

    async def _build_snapshot_payload(db, *, user_id):
        _ = db, user_id
        return {"type": "notification_snapshot", "unread_count": 0}

    monkeypatch.setattr(ws_session_service, "_with_session", _with_session)
    monkeypatch.setattr(
        ws_session_service.notification_service,
        "build_snapshot_payload",
        _build_snapshot_payload,
    )

    user = SimpleNamespace(id=uuid4())
    websocket = FakeWebSocket(messages=[[]])

    await ws_session_service.serve_notification_socket(
        websocket,
        user=user,
        terminal_close_code=4400,
    )

    assert websocket.sent == [
        {"type": "notification_snapshot", "unread_count": 0},
        {
            "type": "error",
            "code": "INVALID_MESSAGE",
            "message": "Malformed websocket payload",
        },
    ]
    assert websocket.close_code == 4400
    assert manager.disconnect_calls == [("notification-conn-1", str(user.id))]
