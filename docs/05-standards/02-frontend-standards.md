# Frontend Standards

Version: 1.0
Date: 2026-03-20

## Purpose

Define mandatory frontend engineering standards for architecture, state, transport, realtime, and maintainability.

## Non-Negotiable Rules

1. Organize by feature under `frontend/src/features/{domain}`.
2. Server state uses TanStack Query; UI/session/socket state uses Zustand.
3. Standard API calls use shared Axios client (`shared/api/api.ts`).
4. Streaming exception: AI stream transport may use `fetch` with readable streams in service code.
5. Route access must use guard components (`ProtectedRoute`, `GuestRoute`, `OrgGuard`).

## Feature Structure Standards

- Each feature should own:
- pages/components
- hooks
- api service layer
- store (if needed)
- types
- Public feature surface should be exported through feature index/barrel files.
- Cross-feature internal imports are forbidden; use public feature API or shared modules.

## State and Data Standards

- Query keys must be namespaced by feature.
- Mutations must invalidate/update relevant query keys.
- Avoid duplicating backend resource state in Zustand stores.
- Persist only stable client context where needed (example: active organization).

## Realtime Standards

- Notification websocket is app-scope and auth-aware.
- Project websocket is project-scope with channel subscription and reconnect strategy.
- Realtime event handling must keep cache invalidation deterministic and scoped.

## Styling and UI Standards

- Shared foundation components (`shared/ui/*`) are controlled surfaces.
- Feature-level local design systems are not allowed.
- Prefer semantic tokens and shared variants over one-off values.
- Styling ownership hierarchy must stay:
- tokens/global styles
- shared UI primitives
- shared adapters/layout shells
- feature composition

## Reliability and UX Safety Standards

- All route-level lazy boundaries must have loading fallback.
- Error states and empty states must be explicit on feature pages.
- Critical async actions must surface user feedback (toast/banner/state).
- Mobile and desktop behavior must both be validated for changed screens.

## Definition of Done (Frontend Change)

- Feature boundary rules followed.
- Query/store usage follows standards.
- Transport and auth/session behavior validated.
- Relevant component/hook/store tests updated.
- Styling constitution rules respected.
- Traceability and relevant docs updated.
