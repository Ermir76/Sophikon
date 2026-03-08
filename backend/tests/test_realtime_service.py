from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuditAction
from app.service import realtime_service
from app.service.activity_log_service import ActivityContext


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entity_type", "expected_channels"),
    [
        ("project", ["project"]),
        ("task", ["tasks"]),
        ("resource", ["resources"]),
        ("assignment", ["tasks", "resources"]),
        ("dependency", ["tasks"]),
        ("project_member", ["members"]),
        ("comment", ["comments"]),
    ],
)
async def test_queue_entity_event_maps_channels(
    session: AsyncSession,
    entity_type: str,
    expected_channels: list[str],
):
    realtime_service.clear_pending_events(session)
    project_id = uuid4()
    entity_id = uuid4()
    actor_id = uuid4()

    realtime_service.queue_entity_event(
        session,
        project_id=project_id,
        entity_type=entity_type,
        action=AuditAction.CREATED,
        entity_id=entity_id,
        entity_name=f"{entity_type}-name",
        context=ActivityContext(
            user_id=actor_id,
            full_name="Realtime User",
            avatar_url=None,
            occurred_at=datetime(2026, 3, 8, tzinfo=UTC),
        ),
        metadata={"related_id": uuid4()},
    )

    pending = session.info[realtime_service.PENDING_REALTIME_EVENTS_KEY]
    assert len(pending) == 1
    assert pending[0]["project_id"] == str(project_id)
    assert pending[0]["channels"] == expected_channels
    assert pending[0]["payload"]["type"] == f"{entity_type}_created"
    assert pending[0]["payload"]["action"] == "created"
    assert pending[0]["payload"]["actor"]["id"] == str(actor_id)
    assert pending[0]["payload"]["entity_id"] == str(entity_id)
    assert pending[0]["payload"]["occurred_at"] == "2026-03-08T00:00:00Z"
    assert isinstance(pending[0]["payload"]["metadata"]["related_id"], str)


@pytest.mark.asyncio
async def test_queue_activity_event_targets_activity_channel(session: AsyncSession):
    realtime_service.clear_pending_events(session)
    project_id = uuid4()
    activity_id = uuid4()

    realtime_service.queue_activity_event(
        session,
        project_id=project_id,
        activity_id=activity_id,
        entity_type="task",
        action=AuditAction.UPDATED,
        entity_id=uuid4(),
        entity_name="Realtime Task",
        changes={"fields": [{"field": "name", "old": "A", "new": "B"}]},
        context=ActivityContext(
            user_id=uuid4(),
            full_name="Realtime User",
            avatar_url=None,
            occurred_at=datetime(2026, 3, 8, tzinfo=UTC),
        ),
    )

    pending = session.info[realtime_service.PENDING_REALTIME_EVENTS_KEY]
    assert pending[0]["channels"] == ["activity"]
    assert pending[0]["payload"]["type"] == "activity_logged"
    assert pending[0]["payload"]["metadata"]["activity_id"] == str(activity_id)


@pytest.mark.asyncio
async def test_commit_and_publish_and_rollback_clear_queue(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    published: list[tuple[str, list[str], str]] = []

    async def _capture_publish(*, project_id, channels, payload):
        published.append((str(project_id), channels, payload["type"]))

    monkeypatch.setattr(
        "app.service.realtime_service.websocket_manager.publish_message",
        _capture_publish,
    )

    realtime_service.queue_message(
        session,
        project_id=uuid4(),
        channels=["project"],
        payload={"type": "project_created"},
    )
    await realtime_service.commit_and_publish(session)

    assert published == [(published[0][0], ["project"], "project_created")]
    assert realtime_service.PENDING_REALTIME_EVENTS_KEY not in session.info

    realtime_service.queue_message(
        session,
        project_id=uuid4(),
        channels=["tasks"],
        payload={"type": "task_created"},
    )
    await realtime_service.rollback_and_clear(session)

    assert published == [(published[0][0], ["project"], "project_created")]
    assert realtime_service.PENDING_REALTIME_EVENTS_KEY not in session.info


@pytest.mark.asyncio
async def test_commit_and_publish_continues_after_individual_publish_failure(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    published: list[str] = []

    async def _capture_publish(*, project_id, channels, payload):
        _ = project_id, channels
        if payload["type"] == "project_created":
            raise RuntimeError("redis unavailable")
        published.append(payload["type"])

    monkeypatch.setattr(
        "app.service.realtime_service.websocket_manager.publish_message",
        _capture_publish,
    )

    realtime_service.queue_message(
        session,
        project_id=uuid4(),
        channels=["project"],
        payload={"type": "project_created"},
    )
    realtime_service.queue_message(
        session,
        project_id=uuid4(),
        channels=["tasks"],
        payload={"type": "task_created"},
    )

    with caplog.at_level("INFO"):
        await realtime_service.commit_and_publish(session)

    assert published == ["task_created"]
    assert realtime_service.PENDING_REALTIME_EVENTS_KEY not in session.info
    assert any(record.message == "realtime_publish_failed" for record in caplog.records)
    summary = next(
        record
        for record in caplog.records
        if record.message == "realtime_publish_batch_completed"
    )
    assert summary.events_total == 2
    assert summary.events_published == 1
    assert summary.events_failed == 1
