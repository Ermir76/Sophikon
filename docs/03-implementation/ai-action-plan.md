# UI Integration MVP Plan (Strong-Foundation, AI-as-Brain)

## Document Metadata
- Version: 1.2.0
- Created: 2026-03-06
- Last Updated: 2026-03-06
- Status: Active Implementation Plan

## Summary
Implement the MVP as a layered system where AI is a standalone brain layer, not a frontend patch and not backend business logic.
Call flow will be:

`Frontend (embedded panel) -> Backend control plane (auth/rbac/audit) -> AI service (reasoning/orchestration) -> Backend domain services/data`

Scope for MVP AI UI remains: **Chat + Estimate + Suggestions** inside one embedded, docked, resizable side panel across all project subpages.

## Implementation Tracker (Checklist)
Legend: `[ ]` Not started, `[x]` Done

### Phase 1: Architecture and Contracts
- [x] Freeze AI boundary and ownership rules (frontend -> backend control plane -> ai-service -> backend domain services).
- [x] Define versioned shared contracts for chat, estimate, suggestions, and ui_context.
- [x] Define SSE chat event contract (`start`, `chunk`, `done`, `error`) and error envelope.
- [x] Add architecture tree update that includes top-level `ai-service/`.

### Phase 2: AI Service (Brain Layer)
- [x] Create top-level `ai-service/` structure (app entry, config, provider, orchestrator, prompts, tests).
- [x] Implement `POST /v1/brain/chat` with streaming output.
- [x] Implement `POST /v1/brain/estimate`.
- [x] Implement `POST /v1/brain/suggestions`.
- [x] Implement deterministic fallback behavior for provider/API failures.
- [ ] Add ai-service unit and contract tests.

### Phase 3: Backend Control Plane
- [x] Add backend AI router: `/api/v1/projects/{project_id}/ai/*`.
- [x] Implement backend -> ai-service client with service-to-service auth.
- [x] Enforce auth + RBAC + project isolation for all AI endpoints.
- [x] Persist AI conversation/messages/usage through existing AI models.
- [x] Forward chat SSE stream from ai-service to frontend in stable event order.
- [ ] Add backend endpoint tests for auth, RBAC, isolation, and streaming behavior.

### Phase 4: Frontend Embedded Panel
- [x] Create `frontend/src/features/ai/` module (components/hooks/api/store/types/index).
- [x] Build docked `AiDockedPanel` (tabs: Chat, Estimate, Suggestions).
- [x] Integrate panel in `ProjectLayout` with right-side resizable split.
- [x] Add sidebar entry `AI Assistant` to toggle panel without route change.
- [x] Keep panel available across all `/projects/:projectId/*` pages.
- [x] Add mobile fallback via sheet/drawer.
- [x] Wire estimate apply flow to existing task update endpoint.
- [x] Wire suggestion apply flow to existing task/dependency endpoints.

### Phase 5: Verification and Release Gate
- [ ] Contract conformance tests pass (backend <-> ai-service).
- [ ] Frontend unit/integration tests pass for panel behavior and SSE rendering.
- [ ] End-to-end smoke pass across project subpages.
- [ ] Reliability tests pass (ai-service down, timeout, malformed response).
- [ ] Update docs with final architecture tree, version bump, and completion status.

## Foundation Decisions (Locked)
1. AI is a separate top-level service (`/ai-service`), outside `backend/` and `frontend/`.
2. Frontend never calls AI service directly.
3. Backend remains control plane for auth, RBAC, tenant isolation, audit, and rate-limits.
4. AI service owns reasoning/orchestration/prompt execution; backend owns domain truth and mutations.
5. Existing public frontend-facing AI endpoints stay project-scoped under backend:
`POST /api/v1/projects/{project_id}/ai/chat` (SSE), `POST /api/v1/projects/{project_id}/ai/estimate`, `GET /api/v1/projects/{project_id}/ai/suggestions`.
6. AI mutation proposals (estimate apply / suggestion apply) execute through existing backend domain endpoints with normal role checks; no direct AI-to-DB writes.

## Implementation Changes
1. Repository structure:
Add top-level `ai-service/` with its own app entry, config, provider layer, orchestration layer, prompt templates, and tests; add service in Docker compose for local integration.
2. AI service (brain layer):
Implement internal endpoints:
- `POST /v1/brain/chat` (streaming chunks/events),
- `POST /v1/brain/estimate`,
- `POST /v1/brain/suggestions`.
Implement orchestration:
- intent handling,
- context assembly request contract,
- provider abstraction,
- prompt versioning,
- deterministic fallback responses,
- structured error codes.
3. Backend control plane:
Add AI endpoint router in backend API v1 and keep it as the only frontend-visible AI surface.
Backend responsibilities:
- authenticate user,
- verify project membership/role,
- resolve project context envelope,
- call AI service with service credentials,
- persist conversation/messages/usage via existing models,
- stream chat SSE back to frontend unchanged in event order.
Add internal service-to-service auth (signed token or shared secret) for backend -> AI service calls.
4. Contract layer (decision-complete):
Define versioned schemas shared by backend and AI service:
- `ChatRequest`, `ChatEvent(start|chunk|done|error)`,
- `EstimateRequest`, `EstimateResponse`,
- `Suggestion`, `SuggestionListResponse`,
- `UiContext(current_view, selected_task_id?, selected_task_ids?)`.
Freeze these contracts before coding UI.
5. Frontend embedded AI panel:
Create `features/ai` module with:
- `AiDockedPanel` (single hub with tabs Chat/Estimate/Suggestions),
- data hooks/service for backend AI endpoints,
- panel store state (open/closed, width, active tab, per-project conversation id).
Integrate panel into project shell using resizable split in `ProjectLayout` (main content + right dock panel).
Add project sidebar entry `AI Assistant` to toggle panel open/close without route change.
Panel is available across all `/projects/:projectId/*` pages.
Mobile fallback uses sheet/drawer (non-resizable).
6. UI behavior (locked):
- Chat tab: project-aware streaming messages; preserves conversation per project.
- Estimate tab: estimate selected task(s) and allow apply recommended duration via existing task update endpoint.
- Suggestions tab: show suggestion cards; apply supported actions via existing dependency/task endpoints.
- No separate AI route/page in MVP; panel is the canonical surface.

## Public Interfaces / Types
1. Backend public APIs (frontend-facing):
`POST /api/v1/projects/{id}/ai/chat`, `POST /api/v1/projects/{id}/ai/estimate`, `GET /api/v1/projects/{id}/ai/suggestions`.
2. AI service internal APIs (backend-facing):
`POST /v1/brain/chat`, `POST /v1/brain/estimate`, `POST /v1/brain/suggestions`.
3. Mirrored schema set (see `issues/open_issues/04-ai-contracts.md` for contract duplication backlog):
`chat`, `estimate`, `suggestions`, `ui_context`, standardized error envelope, SSE event schema.
4. Frontend feature module API:
`features/ai/index.ts` exports panel component, hooks, and types only (no cross-feature private imports).

## Test Plan and Acceptance Gates
1. Contract gate:
Schema conformance tests between backend and AI service (request/response + SSE event sequence).
2. Security gate:
RBAC and tenant-isolation tests for all AI endpoints (no cross-project leakage, no unauthorized mutation apply).
3. Integration gate:
Backend<->AI service integration tests (timeouts, retries, error propagation, streaming continuity).
4. Frontend gate:
Unit/integration tests for panel toggle, resize behavior, cross-page persistence in project scope, SSE rendering, estimate apply flow, suggestion apply flow.
5. E2E gate:
From each major project subpage (overview/tasks/gantt/resources), open sidebar AI panel, chat, estimate, apply one result, fetch suggestion, apply one action, and verify domain state updates correctly.
6. Reliability gate:
Basic resilience tests (AI service unavailable, partial stream failure, malformed AI response) with graceful UI + backend fallback errors.

## Assumptions and Defaults
1. MVP means fewer features, not weaker architecture: advanced planner/risk/optimizer remain out of scope.
2. Backend remains source of truth for project/task/resource data and existing AI persistence models.
3. AI service may keep ephemeral cache, but not authoritative domain storage.
4. Prompt and model selection are config-driven and versioned from day one.
5. Architecture docs are updated as part of this work: add explicit AI-layer tree and ownership rules so structure cannot be "lost" again.
