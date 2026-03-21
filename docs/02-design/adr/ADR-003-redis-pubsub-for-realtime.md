# ADR-003: Redis Pub/Sub for Realtime Fan-Out and Presence

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

Realtime project events and notification updates must reach multiple websocket clients and support multi-process deployment.

## Decision

Use Redis as a shared bus/state layer for realtime:
- pub/sub channels for project/user websocket fan-out
- Redis hash + TTL for project presence snapshots

## Evidence

- Project realtime manager: `backend/app/core/websocket_manager.py`
- User notifications manager: `backend/app/core/user_notification_websocket_manager.py`
- Publish-after-commit path: `backend/app/service/realtime_service.py`
- Git history signal: `6e6fa99 feat(collaboration): add backend realtime websocket pipeline`

## Consequences

- Realtime fan-out works across backend worker processes.
- Presence survives per-process in-memory boundaries.
- Redis is now a hard dependency for websocket and notification realtime behavior.
