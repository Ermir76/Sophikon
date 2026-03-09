"""
User-scoped websocket manager for notification fan-out.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket
from redis import asyncio as redis
from redis.asyncio.client import PubSub, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

PUBSUB_CHANNEL = "sophikon:user_notifications"


@dataclass(slots=True)
class NotificationConnectionState:
    connection_id: str
    websocket: WebSocket
    user_id: str


class UserNotificationWebSocketManager:
    """Local connection registry + Redis pubsub fan-out by user."""

    def __init__(self):
        self._connections: dict[str, dict[str, NotificationConnectionState]] = (
            defaultdict(dict)
        )
        self._redis: Redis | None = None
        self._pubsub: PubSub | None = None
        self._listener_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                return

            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()  # type: ignore [union-attr]

            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(PUBSUB_CHANNEL)
            self._listener_task = asyncio.create_task(self._listen_for_messages())
            self._started = True

    async def stop(self) -> None:
        async with self._lock:
            if not self._started:
                return

            if self._listener_task is not None:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass

            if self._pubsub is not None:
                await self._pubsub.unsubscribe(PUBSUB_CHANNEL)
                await self._pubsub.close()

            if self._redis is not None:
                await self._redis.close()

            self._connections.clear()
            self._redis = None
            self._pubsub = None
            self._listener_task = None
            self._started = False

    async def connect(self, websocket: WebSocket, *, user_id: UUID | str) -> str:
        connection_id = str(uuid4())
        user_key = str(user_id)
        self._connections[user_key][connection_id] = NotificationConnectionState(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_key,
        )
        return connection_id

    async def disconnect(self, connection_id: str, user_id: UUID | str) -> None:
        user_key = str(user_id)
        user_connections = self._connections.get(user_key)
        if user_connections is not None:
            user_connections.pop(connection_id, None)
            if not user_connections:
                self._connections.pop(user_key, None)

    async def publish_message(
        self,
        *,
        user_id: UUID | str,
        payload: dict[str, Any],
    ) -> None:
        if self._redis is None:
            raise RuntimeError("UserNotificationWebSocketManager has not been started")
        envelope = {
            "user_id": str(user_id),
            "payload": payload,
        }
        await self._redis.publish(PUBSUB_CHANNEL, json.dumps(envelope))

    async def _listen_for_messages(self) -> None:
        assert self._pubsub is not None
        try:
            while True:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                try:
                    envelope = json.loads(message["data"])
                except (TypeError, ValueError):
                    logger.warning(
                        "Ignoring malformed user-notification pubsub message"
                    )
                    continue

                await self._dispatch_pubsub_message(envelope)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("User notification pubsub listener crashed")
            raise

    async def _dispatch_pubsub_message(self, envelope: dict[str, Any]) -> None:
        user_key = str(envelope.get("user_id"))
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            return

        dead_connections: list[str] = []
        for connection_id, connection in list(
            self._connections.get(user_key, {}).items()
        ):
            try:
                await connection.websocket.send_json(payload)
            except Exception:
                dead_connections.append(connection_id)

        for connection_id in dead_connections:
            await self.disconnect(connection_id, user_key)


user_notification_websocket_manager = UserNotificationWebSocketManager()
