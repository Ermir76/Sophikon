import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.websocket_manager import WebSocketManager


class DummyWebSocket:
    async def send_json(self, payload):
        _ = payload
        return None


class FakePubSub:
    def __init__(self):
        self.unsubscribed: list[str] = []
        self.closed = False

    async def unsubscribe(self, channel: str) -> None:
        self.unsubscribed.append(channel)

    async def close(self) -> None:
        self.closed = True


class FakeRedis:
    def __init__(self):
        self.hashes: dict[str, dict[str, str]] = {}
        self.expirations: dict[str, int] = {}
        self.closed = False

    async def hset(self, key: str, field: str, value: str) -> None:
        self.hashes.setdefault(key, {})[field] = value

    async def hdel(self, key: str, *fields: str) -> None:
        bucket = self.hashes.setdefault(key, {})
        for field in fields:
            bucket.pop(field, None)

    async def hgetall(self, key: str) -> dict[str, str]:
        return dict(self.hashes.get(key, {}))

    async def publish(self, channel: str, payload: str) -> None:
        _ = channel, payload
        return None

    async def expire(self, key: str, seconds: int) -> None:
        self.expirations[key] = seconds

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_stop_clears_local_presence_records() -> None:
    manager = WebSocketManager()
    fake_redis = FakeRedis()
    fake_pubsub = FakePubSub()
    manager._redis = fake_redis
    manager._pubsub = fake_pubsub
    manager._listener_task = asyncio.create_task(asyncio.sleep(3600))
    manager._presence_refresh_task = asyncio.create_task(asyncio.sleep(3600))
    manager._started = True

    project_id = uuid4()
    await manager.connect(
        DummyWebSocket(),
        project_id=project_id,
        user_id=uuid4(),
        full_name="Realtime User",
        avatar_url=None,
        channels={"project"},
    )

    assert await fake_redis.hgetall(manager._presence_key(project_id))
    assert fake_redis.expirations[manager._presence_key(project_id)] == 90

    await manager.stop()

    assert await fake_redis.hgetall(manager._presence_key(project_id)) == {}
    assert manager._connections == {}
    assert manager._started is False
    assert fake_pubsub.closed is True
    assert fake_redis.closed is True


@pytest.mark.asyncio
async def test_build_presence_snapshot_prunes_stale_records_and_dedupes_users() -> None:
    manager = WebSocketManager()
    manager._redis = FakeRedis()

    project_id = uuid4()
    key = manager._presence_key(project_id)
    user_id = str(uuid4())
    fresh_connection_id = "fresh-conn"
    stale_connection_id = "stale-conn"
    now = datetime.now(UTC)

    manager._redis.hashes[key] = {
        stale_connection_id: json.dumps(
            {
                "connection_id": stale_connection_id,
                "id": user_id,
                "full_name": "Realtime User",
                "avatar_url": None,
                "status": "viewing",
                "entity_type": "project",
                "entity_id": str(project_id),
                "updated_at": (now - timedelta(seconds=31)).isoformat(),
            }
        ),
        fresh_connection_id: json.dumps(
            {
                "connection_id": fresh_connection_id,
                "id": user_id,
                "full_name": "Realtime User",
                "avatar_url": None,
                "status": "editing",
                "entity_type": "task",
                "entity_id": str(uuid4()),
                "updated_at": now.isoformat(),
            }
        ),
    }

    snapshot = await manager.build_presence_snapshot(project_id)

    assert snapshot["type"] == "presence_snapshot"
    assert len(snapshot["users"]) == 1
    assert snapshot["users"][0]["status"] == "editing"
    assert stale_connection_id not in manager._redis.hashes[key]


@pytest.mark.asyncio
async def test_build_presence_snapshot_prunes_invalid_status_records() -> None:
    manager = WebSocketManager()
    manager._redis = FakeRedis()

    project_id = uuid4()
    key = manager._presence_key(project_id)
    valid_connection_id = "valid-conn"
    invalid_connection_id = "invalid-conn"
    now = datetime.now(UTC)

    manager._redis.hashes[key] = {
        invalid_connection_id: json.dumps(
            {
                "connection_id": invalid_connection_id,
                "id": str(uuid4()),
                "full_name": "Invalid Status User",
                "avatar_url": None,
                "status": "focused",
                "entity_type": "task",
                "entity_id": str(uuid4()),
                "updated_at": now.isoformat(),
            }
        ),
        valid_connection_id: json.dumps(
            {
                "connection_id": valid_connection_id,
                "id": str(uuid4()),
                "full_name": "Valid User",
                "avatar_url": None,
                "status": "viewing",
                "entity_type": "project",
                "entity_id": str(project_id),
                "updated_at": now.isoformat(),
            }
        ),
    }

    snapshot = await manager.build_presence_snapshot(project_id)

    assert snapshot["type"] == "presence_snapshot"
    assert len(snapshot["users"]) == 1
    assert snapshot["users"][0]["status"] == "viewing"
    assert invalid_connection_id not in manager._redis.hashes[key]


@pytest.mark.asyncio
async def test_refresh_local_presence_records_uses_latest_connection_state() -> None:
    manager = WebSocketManager()
    manager._redis = FakeRedis()

    project_id = uuid4()
    user_id = uuid4()
    connection_id, _ = await manager.connect(
        DummyWebSocket(),
        project_id=project_id,
        user_id=user_id,
        full_name="Realtime User",
        avatar_url=None,
        channels={"project"},
    )

    await manager.update_presence(
        connection_id=connection_id,
        project_id=project_id,
        user_id=user_id,
        full_name="Realtime User",
        avatar_url=None,
        status="editing",
        entity_type="task",
        entity_id=uuid4(),
    )
    await manager._delete_presence_record(project_id, connection_id)

    assert await manager._redis.hgetall(manager._presence_key(project_id)) == {}

    await manager._refresh_local_presence_records()

    records = await manager._redis.hgetall(manager._presence_key(project_id))
    payload = json.loads(records[connection_id])
    assert payload["status"] == "editing"
    assert payload["entity_type"] == "task"
    assert manager._redis.expirations[manager._presence_key(project_id)] == 90
