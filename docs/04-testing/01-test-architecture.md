# Test Architecture

**Version:** 1.0
**Date:** 2026-03-20

---

## Test Pyramid

```
         ┌───────────────┐
         │     E2E       │  Full browser flows
         ├───────────────┤
         │  Integration  │  Real DB, real services
         ├───────────────┤
         │     Unit      │  Isolated, no I/O
         └───────────────┘
```

The base shall be wide. Unit tests shall dominate by count. Integration tests shall cover service composition and database behavior. E2E shall cover critical user paths only — not every feature.

---

## Backend Infrastructure

**Runner:** pytest with pytest-asyncio (auto mode).

**Database isolation:** Each test shall run inside a savepoint nested under a single outer transaction. The outer transaction shall roll back at session end. No truncation or per-test teardown is required. Tests shall always run against a real PostgreSQL instance — the database shall never be mocked.

**HTTP client:** httpx.AsyncClient via ASGITransport. No network hops. The full middleware stack shall be active.

**Auth:** Tests that require an authenticated session shall call the register and login endpoints in setup and carry the session cookie forward. No JWT forgery or auth bypass is permitted.

**External services:** Email, OAuth providers, and LLM providers shall be stubbed at the adapter boundary. The LLM Mock provider shall be used for AI-related tests. Everything below the adapter shall be real.

---

## Backend Test Layers

**Unit / api** — Tests shall call HTTP endpoints through the full request/response cycle. Validates request validation, auth middleware, response shape, and error codes.

**Unit / service** — Tests shall call service functions directly with a real async session. Validates business logic in isolation from HTTP concerns.

**Integration / flows** — Tests shall exercise multi-step user scenarios through the HTTP layer. Validates that composed operations produce correct DB state and that side effects (schedule recalculation, rollup propagation, notifications) trigger correctly.

---

## Backend File Organization

Test files shall mirror the source module structure. One source module shall map to one test file. Integration flow tests shall be grouped by the business flow they cover, not by the endpoint they call.

---

## Frontend Infrastructure

**Runner:** Vitest with jsdom environment.

**Component testing:** React Testing Library. Tests shall render components, interact via userEvent, and assert on DOM state. Snapshot tests shall not be used.

**API mocking:** Mock Service Worker (msw). API calls shall be intercepted at the network layer. Components shall use their real providers — no special test wrappers beyond what the app already uses.

**TanStack Query:** Tests shall use a QueryClientProvider configured with zero retries and no background refetch.

**File location:** Test files shall be co-located with the source file they cover, using the same name with a `.test.tsx` or `.test.ts` suffix.

---

## E2E Infrastructure

**Runner:** Playwright.

**Scope:** Critical user paths shall be covered — auth, core task management, Gantt interaction. Exhaustive E2E coverage is not the goal.

**State:** Each spec shall start unauthenticated. Login shall be part of the flow. No shared session state between specs is permitted.

---

## Running Tests

```bash
# Backend
cd backend && uv run pytest
uv run pytest tests/unit/ -q
uv run pytest tests/integration/ -q

# Frontend
cd frontend && npm test

# E2E
cd frontend && npm run test:e2e
```

---

## Related Docs

- Coverage targets and risk priority → `02-test-strategy.md`
