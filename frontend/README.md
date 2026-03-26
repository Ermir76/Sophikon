# Sophikon Frontend

React 19 SPA built with Vite and TypeScript.

## Structure

```
src/
  app/              App entry, routing (ProtectedRoute, GuestRoute, OrgGuard)
  features/         Feature modules:
    auth/             Login, register, email verification, auth store
    dashboard/        Dashboard page
    organizations/    Org CRUD, org switcher, members
    projects/         Project CRUD, project layout
    tasks/            Task management
    gantt/            Gantt chart
    calendar/         Calendar view
    resources/        Resource management
    reports/          Reports
  shared/
    api/              Axios instance with refresh token interceptor
    components/       Shared UI components (ErrorBoundary, PageLoader, etc.)
    hooks/            Custom hooks
    layout/           AppLayout, AppHeader, AppSidebar
    ui/               Base widget foundation layer (controlled)
    lib/              Utility functions
  config/           React Query client config
```

## Visual Governance

Visual ownership is enforced in this order:

1. `src/index.css` for tokens and global visual defaults
2. `src/shared/ui/*` for base widget visuals (controlled foundation layer)
3. `src/shared/*` adapters/primitives for app-semantic wrappers
4. `src/features/**` for composition only (no private design systems)

Authoritative docs:

- `docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`
- `docs/02-design/frontend-architecture.md`
- `docs/03-implementation/ui-ux-recovery-tracker.md`

## Setup

> For full step-by-step instructions including backend and Docker setup, see the [root README](../README.md).

```bash
npm install
npm run dev       # starts Vite dev server at http://localhost:5173
```

The Vite dev server proxies `/api` requests to `localhost:8000` (backend). No frontend `.env` file is needed for local development — the defaults work out of the box.

## Scripts

| Command            | Description                   |
| ------------------ | ----------------------------- |
| `npm run dev`      | Start dev server              |
| `npm run build`    | Type-check + production build |
| `npm run lint`     | ESLint                        |
| `npm run format`   | Prettier                      |
| `npm test`         | Vitest (unit tests)           |
| `npm run test:e2e` | Playwright (E2E tests)        |

## Testing

Unit tests (`src/`) and E2E tests (`tests/e2e/`) are separate test suites with different runners:

- **`npm test`** — runs Vitest unit tests in jsdom (files under `src/`)
- **`npm run test:e2e`** — runs Playwright browser tests (files under `tests/e2e/`)

They do not interfere with each other — Vitest is configured to exclude `tests/e2e/`.

## Key Libraries

- **React Router v7** — client-side routing
- **TanStack Query** — server state management + caching
- **Zustand** — client state (auth store, org store)
- **React Hook Form + Zod** — form handling + validation
- **shadcn/ui + Tailwind CSS v4** — component library + styling
- **Axios** — HTTP client with cookie-based auth
