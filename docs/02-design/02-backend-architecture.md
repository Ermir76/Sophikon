# Backend Architecture

Version: 1.0
Date: 2026-03-20

## Purpose

Define the detailed backend design for Sophikon V1: module boundaries, runtime flows, layer contracts, and operational patterns.

## Scope

In scope:
- FastAPI transport layers (REST, SSE, WebSocket)
- Business/service orchestration
- Persistence and query design
- Realtime event architecture
- AI integration boundary
- Background processing via Celery

Out of scope:
- Full endpoint contract details (see `api-specification.md`)
- Full DB schema details (see `database-schema.md`)
- Frontend architecture details

## Architectural Principles

- Separation of concerns: API, service, repository, and model layers have distinct ownership.
- Explicit boundaries: no direct layer skipping.
- Transaction integrity: persistent changes must commit before external event publication.
- Provider decoupling: AI provider specifics are isolated in ai-service.
- Stateless API scaling: Redis-backed fan-out and presence enable horizontal backend instances.

## Runtime Responsibilities

Backend responsibilities:
- Expose REST API endpoints for domain operations.
- Expose SSE streaming endpoints for AI interactions.
- Expose WebSocket endpoints for project realtime updates and user notifications.
- Execute business rules and orchestrate domain workflows.
- Persist domain state in PostgreSQL through SQLAlchemy.
- Publish realtime updates via Redis pub/sub after successful commit.
- Run scheduled/background jobs through Celery tasks.

AI service responsibilities:
- Accept normalized completion requests from backend.
- Handle provider-specific model communication.
- Stream completion events back to backend.

## Backend Module Map

| Module | Responsibility |
| --- | --- |
| `backend/app/main.py` | App bootstrap, middleware, router registration, exception handlers |
| `backend/app/api/v1/endpoints` | Transport layer handlers for REST/SSE/WS |
| `backend/app/api/deps` | Authentication, authorization, and access-context dependencies |
| `backend/app/service` | Use-case orchestration and business logic |
| `backend/app/service/agent` | PM agent loop, planning, execution, tool dispatch, streaming |
| `backend/app/repository` | SQLAlchemy query and persistence helpers |
| `backend/app/models` | ORM entities and database mappings |
| `backend/app/core` | Config, DB engine/session, security, rate limiting, storage, websocket managers |
| `backend/app/tasks` | Celery task implementations |
| `backend/app/celery_app.py` | Celery app and beat schedule configuration |

## Layer Contracts

## API Layer (`backend/app/api`)

Owns:
- Request/response contracts and transport semantics.
- Endpoint-level dependency wiring (auth/access checks).
- Status codes and API error shaping.

Must not:
- Implement core domain logic.
- Execute direct DB query logic outside sanctioned service/repository path.

## Service Layer (`backend/app/service`)

Owns:
- Business rules and multi-step use-case orchestration.
- Transaction flow (`flush`, `commit`, rollback strategy).
- Cross-domain orchestration and event enqueueing.

Must not:
- Depend on API-layer request/response schema objects.
- Embed HTTP/WebSocket protocol decisions.

## Repository Layer (`backend/app/repository`)

Owns:
- SQLAlchemy queries, filtering, joins, and persistence helpers.

Must not:
- Encode transport semantics.
- Implement business policy decisions.

## Model Layer (`backend/app/models`)

Owns:
- Domain entity structure and persistence mapping.
- Field-level constraints and enum-backed semantics.

## Core Layer (`backend/app/core`)

Owns:
- Runtime infrastructure and shared technical primitives:
  - configuration
  - database engine/session
  - auth crypto helpers
  - rate limit integration
  - websocket pub/sub managers
  - local media/attachment path safety

## Request Lifecycle

## REST Lifecycle

1. Endpoint validates request payload and access dependencies.
2. Service orchestrates use case and business rule checks.
3. Repository performs required persistence/query operations.
4. Service finalizes transaction and returns domain result.
5. Endpoint returns response model payload.

## SSE Lifecycle (AI Chat)

1. Client calls AI chat endpoint.
2. Backend creates/loads conversation context.
3. Agent loop runs planner and execution phases.
4. Backend calls ai-service for turn-level completion streaming.
5. Backend emits SSE events (`plan`, `tool_call`, `tool_result`, `chunk`, `done`, etc.).
6. Messages and usage data are persisted in backend DB.

## WebSocket Lifecycle (Project Realtime)

1. Client opens project socket.
2. Backend resolves auth/access context from token/cookie/header.
3. Socket session registers with websocket manager.
4. Presence state is maintained in Redis with TTL refresh.
5. Backend publishes project events through Redis pub/sub.
6. Subscribed client sockets receive filtered events.

## WebSocket Lifecycle (User Notifications)

1. Client opens user notification socket.
2. Backend authenticates user context.
3. Notification websocket manager tracks active user connections.
4. Notification events are published through Redis pub/sub.
5. User clients receive unread-count and notification update payloads.

## Transaction and Consistency Model

- Domain mutations occur inside service-layer transaction boundaries.
- Realtime publication is deferred until commit success.
- Event publication uses queued pending events in DB session context.
- On commit failure, pending events are cleared and not published.

Result:
- Avoids client-visible realtime events for rolled-back DB changes.

## Realtime Architecture

Channels:
- Project channel fan-out for tasks/resources/members/activity/project/comments
- User notification fan-out for notification updates

State:
- Presence records in Redis hash per project.
- Active socket connection registries in process memory.

Scaling:
- Redis pub/sub decouples event publication from single-process websocket state.

## Security and Access Integration

Authentication:
- Access token validation (JWT) and active-user checks.
- Cookie and bearer-token support for API and websocket flows.

Authorization:
- Project and organization role checks via dependency layer.
- Role-gated mutation endpoints for sensitive operations.

Abuse protection:
- Redis-backed rate limiting with endpoint-level overrides.

## AI Integration Boundary

Backend side:
- Owns agent loop, tool execution, approval workflow, conversation persistence.
- Owns all domain mutations initiated by AI tools.

AI service side:
- Owns provider communication and model-specific formatting.
- Does not execute domain tools.
- Does not own product domain DB access.

## Background Processing

Mechanism:
- Celery worker(s) with Redis broker/backend.

Scheduled tasks:
- Deadline-approaching notifications.
- Daily proactive project health check.

Task behavior:
- Execute business logic through service patterns.
- Persist results and publish notifications/realtime events through established pipeline.

## Error Handling Model

- App-specific exceptions are normalized into structured API error payloads.
- Unhandled exceptions are logged server-side and returned as sanitized internal errors.
- Socket protocol parsing errors return protocol-specific error payloads and terminal close behavior where required.

## Dependency Rules

Allowed:
- `api -> service`
- `service -> repository`
- `repository -> models`
- `service/agent -> service/*`
- `service/agent -> ai-service` (HTTP)

Not allowed:
- `api -> repository` directly
- `repository -> service`
- `service -> api/schema` coupling
- Domain logic inside transport-only layers

## Interfaces With Other Design Docs

- Top-level context: `architecture-overview.md`
- API contracts: `api-specification.md`
- Data model: `database-schema.md`
- Security model details: `security-design.md`
- Runtime movement details: `data-flow.md`
- Deployment model: `deployment-topology.md`
