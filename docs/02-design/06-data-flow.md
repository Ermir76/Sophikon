# Data Flow

Updated: 2026-03-20

Purpose: Define runtime data movement across frontend, backend, AI service, database, Redis, Celery, and WebSocket channels.

## 1) Core CRUD + Realtime Flow (Frontend -> API -> Service -> DB -> Redis -> WebSocket)

Example: create/update/delete task

1. Frontend calls REST endpoint via axios/fetch (`frontend/src/shared/api/api.ts`, feature service files).
2. FastAPI endpoint validates request and access (`backend/app/api/v1/endpoints/tasks.py` + deps).
3. Service layer executes business logic (`backend/app/service/task_service.py` and related services).
4. Repository layer executes SQLAlchemy queries (`backend/app/repository/task_repo.py`).
5. DB transaction is committed.
6. Realtime events queued in `db.info` are published after commit (`backend/app/service/realtime_service.py`).
7. Backend publishes to Redis pub/sub (`sophikon:realtime`), then active WebSocket sessions receive JSON events (`backend/app/core/websocket_manager.py`).
8. Frontend WebSocket hooks receive events and invalidate query caches (`frontend/src/features/projects/hooks/useProjectWebSocket.ts`).

## 2) AI Chat Flow (Frontend -> Backend SSE -> AI Service SSE -> Tools -> DB)

1. Frontend opens SSE chat stream (`POST /api/v1/projects/{project_id}/ai/chat`) and parses `data:` events (`frontend/src/features/ai/api/ai.service.ts`).
2. Backend endpoint authorizes and starts stream (`backend/app/api/v1/endpoints/ai.py`).
3. Backend creates/loads conversation and runs agent loop (`backend/app/service/ai_service.py`, `backend/app/service/agent/loop.py`).
4. Planner phase requests plan via ai-service (`planner.py` -> `_complete_from_service`).
5. On approval, executor performs iterative tool loop (`executor.py`):
   - calls ai-service `/v1/complete`
   - emits tool calls/results to frontend SSE
   - executes backend tools through service layer (`tool_registry.py`)
6. Tool actions mutate DB and may trigger realtime notifications (through normal service/realtime paths).
7. Conversation messages and usage are persisted in backend DB (`ai_message`, `ai_usage`, `ai_conversation` models).

## 3) Notification Flow (API/Celery -> DB -> Redis -> User WebSocket)

1. Notification rows are created by services/tasks (`backend/app/service/notification_service.py`, `backend/app/tasks/notification_tasks.py`, `backend/app/tasks/agent_monitor.py`).
2. Notification service queues user-scoped websocket events.
3. `commit_and_publish` publishes queued user events to Redis channel `sophikon:user_notifications`.
4. User notification websocket manager fan-outs to connected sockets (`backend/app/core/user_notification_websocket_manager.py`).
5. Frontend notification socket hook updates unread count and invalidates notification queries (`frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`).

## 4) Presence Flow (WebSocket Client -> Redis Hash + Pub/Sub -> Clients)

1. Frontend project page opens `/api/v1/ws/projects/{project_id}`.
2. Backend authenticates socket token/cookie/header (`backend/app/api/deps/ws.py`).
3. WebSocket manager stores connection presence in Redis hash `sophikon:presence:{project_id}` with TTL refresh.
4. Presence updates are published through Redis pub/sub and reflected to all relevant clients.
5. Frontend keeps per-project presence state in Zustand (`frontend/src/features/projects/store/websocket-store.ts`).

## 5) Scheduled Background Flow (Celery Beat -> Task -> DB/Redis/WebSocket)

Configured schedules (`backend/app/celery_app.py`):
- Daily deadline notification task (`notification_tasks.send_deadline_approaching_notifications`)
- Daily project health check (`agent_monitor.run_daily_project_health_check`)

Runtime behavior:
- Task reads project/task state from DB.
- Writes notifications/comments/conversations where needed.
- Publishes websocket updates through realtime publish pipeline.
