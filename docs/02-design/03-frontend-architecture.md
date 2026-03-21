# Frontend Architecture

**Version:** 1.0
**Date:** 2026-02-06

---

## Principles

- **Feature ownership** - all business UI and behavior lives under `features/{domain}`.
- **Server-state first** - backend data is managed through TanStack Query. Zustand is for UI/session/socket state only.
- **Transport abstraction** - standard REST/JSON API calls go through the shared Axios client.
- **Streaming exception** - AI streaming endpoints may use `fetch` with `ReadableStream` in feature service/transport code, never directly in UI components.
- **Realtime resilience** - WebSocket hooks handle reconnect with backoff and stop on terminal error codes.

---

## Application Shell

Provider tree (root):

1. `StrictMode`
2. `ErrorBoundary`
3. `QueryClientProvider`
4. `BrowserRouter`
5. `ThemeProvider` + `TooltipProvider`
6. `App` + global `Toaster`

Query client defaults: `staleTime` 5 minutes, `retry` 1, `refetchOnWindowFocus` false.

---

## Route Model

**Guest routes** (unauthenticated only): `/login`, `/register`

**Public routes** (any): `/verify-email`, `/forgot-password`, `/reset-password`

**Protected routes** (authenticated):

- Global: `/`, `/projects`, `/profile`, `/project-invitations/accept`
- Org-scoped: `/settings`, `/members`
- Project-scoped: `/projects/:projectId` -> `tasks`, `gantt`, `kanban`, `resources`, `utilization`, `calendar`, `reports`, `settings`

**Guards:**

- `ProtectedRoute` - blocks until auth init completes, redirects to `/login?next=...` when unauthenticated
- `GuestRoute` - redirects authenticated users to `/`
- `OrgGuard` - requires active org context before allowing org-scoped routes

---

## Session and Auth

- Auth state lives in `auth-store`, initialized from local storage and validated on mount via `/auth/me`
- Login/register updates store and local storage snapshot
- Logout clears backend session, React Query cache, and local auth snapshot
- On 401: single refresh attempt via `/auth/refresh`, then retry original request. Auth endpoints excluded from refresh loop.
- OAuth: browser redirect to backend OAuth entry URL with safe `next` parameter

---

## State Model

| Concern                                         | Tool                             |
| ----------------------------------------------- | -------------------------------- |
| Backend data (projects, tasks, resources, etc.) | TanStack Query                   |
| Auth/session                                    | Zustand (`auth-store`)           |
| Active organization                             | Zustand (`org-store`, persisted) |
| Project WebSocket state + presence              | Zustand (per-project)            |
| Notification WebSocket state                    | Zustand                          |
| AI panel state                                  | Zustand (per-project)            |

Rule: never put backend resource data in Zustand. Never put UI/socket state in Query cache.

---

## Realtime

Two WebSocket connections:

**User notifications** - mounted at app layout level, active when authenticated. Reconnects with backoff, stops on terminal auth error codes.

**Project realtime** - mounted at project layout level, one connection per active project. Subscribes to: `tasks`, `resources`, `members`, `activity`, `project`, `comments`. On project deletion: close socket, clear state, redirect to `/projects`. Reconnects with backoff, stops on terminal auth/permission error codes.

Both hooks invalidate relevant TanStack Query caches on incoming events.

---

## AI Workspace

- Project-scoped, rendered by project layout
- Desktop: docked resizable side panel. Mobile: drawer.
- Transport: streaming POST to chat endpoint, SSE-style `data:` event parsing
- Stream events: `start`, `chunk`, `reasoning`, `plan`, `plan_approved`, `tool_call`, `tool_result`, `approval_required`, `ui_action`, `done`, `error`
- Tool-result events invalidate task query caches
- Plan and tool approvals resolved via explicit approval endpoints

---

## Error and Loading Model

- `ErrorBoundary` at root catches unhandled render errors
- Route lazy loading wrapped in `Suspense` with page loader fallback
- Auth guards block rendering until session init completes
- Feature screens handle query loading/error/empty states locally
- Mutation and stream failures surface via toast notifications

---

## Dependency Rules

**Allowed:**

- `app` -> routing, feature entry points, shared layout
- `feature` -> own hooks, services, types + shared modules
- `shared/layout` -> feature public hooks/components for cross-cutting shell behavior

**Not allowed:**

- Feature UI calling backend directly without going through feature service + shared API client
- Cross-feature internal imports; cross-feature access must go through feature public API/barrel exports
- Global state stores replacing feature-scoped state + query cache

---

## Related Docs

- System context -> `01-architecture-overview.md`
- Backend layers -> `02-backend-architecture.md`
- Data movement -> `data-flow.md`
- Security -> `security-design.md`
- Deployment -> `deployment-topology.md`
- API contracts -> `api-specification.md`
