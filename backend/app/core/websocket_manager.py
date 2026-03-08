"""
Project-scoped websocket connection and Redis fan-out manager.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket
from redis import asyncio as redis

from app.core.config import settings
from app.schema.realtime import (
    PresenceEntityType,
    PresenceSnapshotMessage,
    PresenceStatus,
    PresenceUpdateMessage,
    RealtimeChannel,
    RealtimePresenceUser,
)

logger = logging.getLogger(__name__)

PUBSUB_CHANNEL = "sophikon:realtime"
PRESENCE_KEY_PREFIX = "sophikon:presence:"
STATUS_PRIORITY: dict[PresenceStatus, int] = {"viewing": 0, "editing": 1}
PRESENCE_TTL_SECONDS = 30
PRESENCE_REFRESH_INTERVAL_SECONDS = 10


@dataclass(slots=True)
class ConnectionState:
    connection_id: str
    websocket: WebSocket
    project_id: str
    user_id: str
    full_name: str | None
    avatar_url: str | None
    status: PresenceStatus
    entity_type: PresenceEntityType
    entity_id: str | None
    channels: set[RealtimeChannel] = field(default_factory=set)


class WebSocketManager:
    """Own local websocket connections and Redis-backed fan-out."""

    def __init__(self):
        # TODO(2026-03-08): Consider per-project asyncio locks for connection-map
        # mutations/snapshots under high churn. Keep locks out of send I/O paths.
        self._connections: dict[str, dict[str, ConnectionState]] = defaultdict(dict)
        self._redis: redis.Redis | None = None
        self._pubsub: Any = None
        self._listener_task: asyncio.Task | None = None
        self._presence_refresh_task: asyncio.Task | None = None
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
            await self._redis.ping()

            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(PUBSUB_CHANNEL)
            self._listener_task = asyncio.create_task(self._listen_for_messages())
            self._presence_refresh_task = asyncio.create_task(
                self._refresh_presence_loop()
            )
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

            if self._presence_refresh_task is not None:
                self._presence_refresh_task.cancel()
                try:
                    await self._presence_refresh_task
                except asyncio.CancelledError:
                    pass

            await self._clear_local_presence_records()

            if self._pubsub is not None:
                await self._pubsub.unsubscribe(PUBSUB_CHANNEL)
                await self._pubsub.close()

            if self._redis is not None:
                await self._redis.close()

            self._connections.clear()
            self._redis = None
            self._pubsub = None
            self._listener_task = None
            self._presence_refresh_task = None
            self._started = False

    async def connect(
        self,
        websocket: WebSocket,
        *,
        project_id: UUID,
        user_id: UUID,
        full_name: str | None,
        avatar_url: str | None,
        channels: set[RealtimeChannel],
    ) -> tuple[str, dict[str, Any]]:
        connection_id = str(uuid4())
        project_key = str(project_id)
        self._connections[project_key][connection_id] = ConnectionState(
            connection_id=connection_id,
            websocket=websocket,
            project_id=project_key,
            user_id=str(user_id),
            full_name=full_name,
            avatar_url=avatar_url,
            status="viewing",
            entity_type="project",
            entity_id=project_key,
            channels=set(channels),
        )
        await self._upsert_presence_record(
            project_id=project_id,
            connection_id=connection_id,
            user_id=user_id,
            full_name=full_name,
            avatar_url=avatar_url,
            status="viewing",
            entity_type="project",
            entity_id=project_id,
        )
        snapshot = await self.build_presence_snapshot(project_id)
        return connection_id, snapshot

    async def disconnect(self, connection_id: str, project_id: UUID | str) -> None:
        project_key = str(project_id)
        project_connections = self._connections.get(project_key)
        if project_connections is not None:
            project_connections.pop(connection_id, None)
            if not project_connections:
                self._connections.pop(project_key, None)

        await self._delete_presence_record(project_key, connection_id)
        await self.publish_presence(project_key)

    async def update_subscriptions(
        self,
        connection_id: str,
        project_id: UUID | str,
        channels: set[RealtimeChannel],
    ) -> None:
        connection = self._connections.get(str(project_id), {}).get(connection_id)
        if connection is not None:
            connection.channels = set(channels)

    async def update_presence(
        self,
        *,
        connection_id: str,
        project_id: UUID,
        user_id: UUID,
        full_name: str | None,
        avatar_url: str | None,
        status: PresenceStatus,
        entity_type: PresenceEntityType,
        entity_id: UUID | None,
    ) -> None:
        connection = self._connections.get(str(project_id), {}).get(connection_id)
        if connection is not None:
            connection.full_name = full_name
            connection.avatar_url = avatar_url
            connection.status = status
            connection.entity_type = entity_type
            connection.entity_id = str(entity_id) if entity_id is not None else None

        await self._upsert_presence_record(
            project_id=project_id,
            connection_id=connection_id,
            user_id=user_id,
            full_name=full_name,
            avatar_url=avatar_url,
            status=status,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        await self.publish_presence(project_id)

    async def build_presence_snapshot(self, project_id: UUID | str) -> dict[str, Any]:
        users = await self._load_presence_users(project_id)
        return PresenceSnapshotMessage(
            project_id=str(project_id),
            users=users,
        ).model_dump(mode="json")

    async def publish_presence(self, project_id: UUID | str) -> None:
        users = await self._load_presence_users(project_id)
        await self.publish_message(
            project_id=project_id,
            channels=[],
            payload=PresenceUpdateMessage(
                project_id=str(project_id),
                users=users,
            ).model_dump(mode="json"),
        )

    async def publish_message(
        self,
        *,
        project_id: UUID | str,
        channels: list[RealtimeChannel],
        payload: dict[str, Any],
    ) -> None:
        if self._redis is None:
            raise RuntimeError("WebSocketManager has not been started")

        envelope = {
            "project_id": str(project_id),
            "channels": channels,
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
                    logger.warning("Ignoring malformed realtime pubsub message")
                    continue

                await self._dispatch_pubsub_message(envelope)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Realtime pubsub listener crashed")
            raise

    async def _dispatch_pubsub_message(self, envelope: dict[str, Any]) -> None:
        project_key = str(envelope["project_id"])
        payload = envelope["payload"]
        channels = set(envelope.get("channels", []))
        is_presence = payload.get("type") in {"presence_snapshot", "presence_update"}

        dead_connections: list[str] = []
        for connection_id, connection in list(
            self._connections.get(project_key, {}).items()
        ):
            if (
                not is_presence
                and channels
                and connection.channels.isdisjoint(channels)
            ):
                continue

            try:
                await connection.websocket.send_json(payload)
            except Exception:
                dead_connections.append(connection_id)

        for connection_id in dead_connections:
            await self.disconnect(connection_id, project_key)

    async def _refresh_presence_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(PRESENCE_REFRESH_INTERVAL_SECONDS)
                await self._refresh_local_presence_records()
        except asyncio.CancelledError:
            raise

    async def _refresh_local_presence_records(self) -> None:
        if self._redis is None:
            return

        for project_connections in self._connections.values():
            for connection in list(project_connections.values()):
                await self._upsert_presence_record(
                    project_id=connection.project_id,
                    connection_id=connection.connection_id,
                    user_id=connection.user_id,
                    full_name=connection.full_name,
                    avatar_url=connection.avatar_url,
                    status=connection.status,
                    entity_type=connection.entity_type,
                    entity_id=connection.entity_id,
                )

    async def _clear_local_presence_records(self) -> None:
        if self._redis is None:
            return

        for project_connections in self._connections.values():
            for connection in list(project_connections.values()):
                await self._delete_presence_record(
                    connection.project_id,
                    connection.connection_id,
                )

    async def _upsert_presence_record(
        self,
        *,
        project_id: UUID | str,
        connection_id: str,
        user_id: UUID | str,
        full_name: str | None,
        avatar_url: str | None,
        status: PresenceStatus,
        entity_type: PresenceEntityType,
        entity_id: UUID | str | None,
    ) -> None:
        if self._redis is None:
            raise RuntimeError("WebSocketManager has not been started")

        await self._redis.hset(
            self._presence_key(project_id),
            connection_id,
            json.dumps(
                {
                    "connection_id": connection_id,
                    "id": str(user_id),
                    "full_name": full_name,
                    "avatar_url": avatar_url,
                    "status": status,
                    "entity_type": entity_type,
                    "entity_id": str(entity_id) if entity_id is not None else None,
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            ),
        )
        await self._redis.expire(
            self._presence_key(project_id),
            PRESENCE_TTL_SECONDS * 3,
        )

    async def _delete_presence_record(
        self,
        project_id: UUID | str,
        connection_id: str,
    ) -> None:
        if self._redis is None:
            raise RuntimeError("WebSocketManager has not been started")
        await self._redis.hdel(self._presence_key(project_id), connection_id)

    async def _load_presence_users(
        self,
        project_id: UUID | str,
    ) -> list[RealtimePresenceUser]:
        if self._redis is None:
            raise RuntimeError("WebSocketManager has not been started")

        raw_records = await self._redis.hgetall(self._presence_key(project_id))
        deduped: dict[str, dict[str, Any]] = {}
        stale_connection_ids: list[str] = []
        now = datetime.now(UTC)

        for connection_id, raw in raw_records.items():
            try:
                record = json.loads(raw)
            except (TypeError, ValueError):
                stale_connection_ids.append(connection_id)
                continue

            try:
                updated_at = datetime.fromisoformat(record["updated_at"])
            except (KeyError, TypeError, ValueError):
                stale_connection_ids.append(connection_id)
                continue

            if (now - updated_at).total_seconds() > PRESENCE_TTL_SECONDS:
                stale_connection_ids.append(connection_id)
                continue

            status = record.get("status")
            if status not in STATUS_PRIORITY:
                logger.warning(
                    "Ignoring presence record with unsupported status",
                    extra={
                        "project_id": str(project_id),
                        "connection_id": connection_id,
                        "status": status,
                    },
                )
                stale_connection_ids.append(connection_id)
                continue

            user_id = record["id"]
            current = deduped.get(user_id)
            if current is None:
                deduped[user_id] = record
                continue

            current_priority = STATUS_PRIORITY[current["status"]]
            next_priority = STATUS_PRIORITY[status]
            if next_priority > current_priority:
                deduped[user_id] = record
                continue
            if (
                next_priority == current_priority
                and record["updated_at"] > current["updated_at"]
            ):
                deduped[user_id] = record

        users = [
            RealtimePresenceUser(
                id=record["id"],
                full_name=record.get("full_name"),
                avatar_url=record.get("avatar_url"),
                status=record["status"],
                entity_type=record["entity_type"],
                entity_id=record["entity_id"] if record.get("entity_id") else None,
            )
            for record in deduped.values()
        ]
        if stale_connection_ids:
            await self._redis.hdel(
                self._presence_key(project_id), *stale_connection_ids
            )
        users.sort(
            key=lambda user: (
                (0 if user.status == "editing" else 1),
                user.full_name or "",
            )
        )
        return users

    @staticmethod
    def _presence_key(project_id: UUID | str) -> str:
        return f"{PRESENCE_KEY_PREFIX}{project_id}"


websocket_manager = WebSocketManager()
