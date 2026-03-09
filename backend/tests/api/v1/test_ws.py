from uuid import UUID, uuid4

import pytest
from fastapi import WebSocketDisconnect
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import ws_auth
from app.api.v1.endpoints import ws as ws_endpoint
from app.core.config import settings
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.service import ws_session_service


async def _register_user(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _login_user(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200, response.text
    token = client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    assert token
    return token


async def _create_project(
    client: AsyncClient,
    *,
    org_slug: str,
    project_name: str,
) -> str:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {org_slug}", "slug": org_slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": project_name,
            "organization_id": org_id,
            "start_date": "2026-03-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


class FakeWebSocket:
    def __init__(
        self, *, token: str | None = None, messages: list[object] | None = None
    ):
        self.query_params: dict[str, str] = {}
        self.cookies: dict[str, str] = {}
        self.headers: dict[str, str] = {}
        if token is not None:
            self.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = token
        self._messages = list(messages or [])
        self.accepted = False
        self.close_code: int | None = None
        self.sent: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = 1000) -> None:
        self.close_code = code

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)

    async def receive_json(self):
        if not self._messages:
            raise WebSocketDisconnect(code=1000)
        message = self._messages.pop(0)
        if isinstance(message, BaseException):
            raise message
        return message


class FakeWebSocketManager:
    def __init__(self):
        self.connect_calls: list[dict] = []
        self.publish_presence_calls: list[str] = []
        self.subscription_updates: list[tuple[str, str, set[str]]] = []
        self.presence_updates: list[dict] = []
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
            "conn-1",
            {"type": "presence_snapshot", "project_id": str(project_id), "users": []},
        )

    async def publish_presence(self, project_id):
        self.publish_presence_calls.append(str(project_id))

    async def update_subscriptions(self, connection_id, project_id, channels):
        self.subscription_updates.append(
            (connection_id, str(project_id), set(channels))
        )

    async def update_presence(self, **kwargs):
        self.presence_updates.append(kwargs)

    async def disconnect(self, connection_id, project_id):
        self.disconnect_calls.append((connection_id, str(project_id)))


class FakeUserNotificationWebSocketManager:
    def __init__(self):
        self.connect_calls: list[dict] = []
        self.disconnect_calls: list[tuple[str, str]] = []

    async def connect(self, websocket, *, user_id):
        self.connect_calls.append(
            {
                "websocket": websocket,
                "user_id": str(user_id),
            }
        )
        return "notif-conn-1"

    async def disconnect(self, connection_id, user_id):
        self.disconnect_calls.append((connection_id, str(user_id)))


def _patch_ws_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    session: AsyncSession,
    manager: FakeWebSocketManager,
):
    async def _with_session(handler):
        return await handler(session)

    monkeypatch.setattr(ws_auth, "_with_session", _with_session)
    monkeypatch.setattr(ws_session_service, "_with_session", _with_session)
    monkeypatch.setattr(ws_session_service, "websocket_manager", manager)


def _patch_notification_ws_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    session: AsyncSession,
    manager: FakeUserNotificationWebSocketManager,
):
    async def _with_session(handler):
        return await handler(session)

    monkeypatch.setattr(ws_auth, "_with_session", _with_session)
    monkeypatch.setattr(ws_session_service, "_with_session", _with_session)
    monkeypatch.setattr(
        ws_session_service,
        "user_notification_websocket_manager",
        manager,
    )


@pytest.mark.asyncio
async def test_project_websocket_connects_and_handles_subscribe_and_presence(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner@example.com", "WS Owner")
    token = await _login_user(client, "ws-owner@example.com")
    project_id = await _create_project(
        client,
        org_slug="ws-org",
        project_name="WebSocket Project",
    )
    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    entity_id = str(uuid4())
    websocket = FakeWebSocket(
        token=token,
        messages=[
            {"type": "subscribe", "channels": ["activity", "project"]},
            {
                "type": "presence",
                "status": "editing",
                "entity_type": "task",
                "entity_id": entity_id,
            },
            WebSocketDisconnect(code=1000),
        ],
    )

    await ws_endpoint.project_websocket(websocket, UUID(project_id))

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.sent == [
        {"type": "presence_snapshot", "project_id": project_id, "users": []}
    ]
    assert manager.connect_calls[0]["project_id"] == project_id
    assert manager.connect_calls[0]["channels"] == set(ws_endpoint.DEFAULT_CHANNELS)
    assert manager.publish_presence_calls == [project_id]
    assert manager.subscription_updates == [
        ("conn-1", project_id, {"activity", "project"})
    ]
    assert manager.presence_updates[0]["status"] == "editing"
    assert str(manager.presence_updates[0]["entity_id"]) == entity_id
    assert manager.disconnect_calls == [("conn-1", project_id)]


@pytest.mark.asyncio
async def test_project_websocket_rejects_unauthenticated_client(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket()

    await ws_endpoint.project_websocket(websocket, uuid4())

    assert websocket.accepted is True
    assert websocket.close_code == 4401
    assert manager.connect_calls == []


@pytest.mark.asyncio
async def test_project_websocket_rejects_non_member(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner-denied@example.com", "WS Owner")
    await _login_user(client, "ws-owner-denied@example.com")
    project_id = await _create_project(
        client,
        org_slug="ws-denied-org",
        project_name="Denied Project",
    )
    await _register_user(client, "ws-outsider@example.com", "WS Outsider")
    outsider_token = await _login_user(client, "ws-outsider@example.com")

    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(token=outsider_token)

    await ws_endpoint.project_websocket(websocket, UUID(project_id))

    assert websocket.accepted is True
    assert websocket.close_code == 4403
    assert manager.connect_calls == []


@pytest.mark.asyncio
async def test_project_websocket_rejects_missing_project(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner-missing@example.com", "WS Owner")
    token = await _login_user(client, "ws-owner-missing@example.com")

    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(token=token)

    await ws_endpoint.project_websocket(websocket, uuid4())

    assert websocket.accepted is True
    assert websocket.close_code == 4404
    assert manager.connect_calls == []


@pytest.mark.asyncio
async def test_project_websocket_closes_on_malformed_payload(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner-invalid@example.com", "WS Owner")
    token = await _login_user(client, "ws-owner-invalid@example.com")
    project_id = await _create_project(
        client,
        org_slug="ws-invalid-org",
        project_name="Invalid Payload Project",
    )

    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=token,
        messages=[{"type": "presence", "status": "editing"}],
    )

    await ws_endpoint.project_websocket(websocket, UUID(project_id))

    assert websocket.accepted is True
    assert websocket.close_code == ws_endpoint.TERMINAL_PROTOCOL_CLOSE_CODE
    assert websocket.sent[1] == {
        "type": "error",
        "code": "INVALID_MESSAGE",
        "message": "Malformed websocket payload",
    }
    assert manager.disconnect_calls == [("conn-1", project_id)]


@pytest.mark.asyncio
async def test_project_websocket_closes_on_non_dict_payload(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner-invalid-shape@example.com", "WS Owner")
    token = await _login_user(client, "ws-owner-invalid-shape@example.com")
    project_id = await _create_project(
        client,
        org_slug="ws-invalid-shape-org",
        project_name="Invalid Payload Shape Project",
    )

    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=token,
        messages=[[]],
    )

    await ws_endpoint.project_websocket(websocket, UUID(project_id))

    assert websocket.accepted is True
    assert websocket.close_code == ws_endpoint.TERMINAL_PROTOCOL_CLOSE_CODE
    assert websocket.sent[1] == {
        "type": "error",
        "code": "INVALID_MESSAGE",
        "message": "Malformed websocket payload",
    }
    assert manager.disconnect_calls == [("conn-1", project_id)]


@pytest.mark.asyncio
async def test_project_websocket_keeps_connection_open_on_unknown_message_type(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await _register_user(client, "ws-owner-unknown@example.com", "WS Owner")
    token = await _login_user(client, "ws-owner-unknown@example.com")
    project_id = await _create_project(
        client,
        org_slug="ws-unknown-org",
        project_name="Unknown Message Project",
    )

    manager = FakeWebSocketManager()
    _patch_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=token,
        messages=[
            {"type": "ping"},
            WebSocketDisconnect(code=1000),
        ],
    )

    await ws_endpoint.project_websocket(websocket, UUID(project_id))

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.sent == [
        {"type": "presence_snapshot", "project_id": project_id, "users": []},
        {
            "type": "error",
            "code": "INVALID_MESSAGE_TYPE",
            "message": "Unsupported websocket message type",
        },
    ]
    assert manager.disconnect_calls == [("conn-1", project_id)]


async def _get_user(client: AsyncClient, session: AsyncSession, email: str) -> User:
    await _register_user(client, email, "Notification User")
    await _login_user(client, email)
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


@pytest.mark.asyncio
async def test_notification_websocket_connects_and_sends_snapshot(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user = await _get_user(client, session, "notif-owner@example.com")
    session.add(
        Notification(
            user_id=user.id,
            type=NotificationType.MENTIONED,
            title="You were mentioned",
            message="Test mention",
            entity_type="comment",
            entity_id=uuid4(),
        )
    )
    await session.commit()

    manager = FakeUserNotificationWebSocketManager()
    _patch_notification_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        messages=[WebSocketDisconnect(code=1000)],
    )

    await ws_endpoint.notification_websocket(websocket)

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.sent == [{"type": "notification_snapshot", "unread_count": 1}]
    assert manager.connect_calls[0]["user_id"] == str(user.id)
    assert manager.disconnect_calls == [("notif-conn-1", str(user.id))]


@pytest.mark.asyncio
async def test_notification_websocket_rejects_unauthenticated_client(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    manager = FakeUserNotificationWebSocketManager()
    _patch_notification_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket()

    await ws_endpoint.notification_websocket(websocket)

    assert websocket.accepted is True
    assert websocket.close_code == 4401
    assert manager.connect_calls == []


@pytest.mark.asyncio
async def test_notification_websocket_keeps_connection_open_on_unknown_message_type(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user = await _get_user(client, session, "notif-unknown@example.com")
    manager = FakeUserNotificationWebSocketManager()
    _patch_notification_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        messages=[
            {"type": "ping"},
            WebSocketDisconnect(code=1000),
        ],
    )

    await ws_endpoint.notification_websocket(websocket)

    assert websocket.accepted is True
    assert websocket.close_code is None
    assert websocket.sent == [
        {"type": "notification_snapshot", "unread_count": 0},
        {
            "type": "error",
            "code": "INVALID_MESSAGE_TYPE",
            "message": "Unsupported websocket message type",
        },
    ]
    assert manager.disconnect_calls == [("notif-conn-1", str(user.id))]


@pytest.mark.asyncio
async def test_notification_websocket_closes_on_malformed_payload(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user = await _get_user(client, session, "notif-invalid@example.com")
    manager = FakeUserNotificationWebSocketManager()
    _patch_notification_ws_dependencies(monkeypatch, session, manager)
    websocket = FakeWebSocket(
        token=client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME),
        messages=[[]],
    )

    await ws_endpoint.notification_websocket(websocket)

    assert websocket.accepted is True
    assert websocket.close_code == ws_endpoint.TERMINAL_PROTOCOL_CLOSE_CODE
    assert websocket.sent == [
        {"type": "notification_snapshot", "unread_count": 0},
        {
            "type": "error",
            "code": "INVALID_MESSAGE",
            "message": "Malformed websocket payload",
        },
    ]
    assert manager.disconnect_calls == [("notif-conn-1", str(user.id))]
