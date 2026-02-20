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
    ui/               shadcn/ui components
    lib/              Utility functions
  config/           React Query client config
```

## Setup

```bash
npm install
npm run dev       # starts Vite dev server at http://localhost:5173
```

The Vite dev server proxies `/api` requests to `localhost:8000` (backend).

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start dev server |
| `npm run build` | Type-check + production build |
| `npm run lint` | ESLint |
| `npm run format` | Prettier |
| `npm test` | Vitest (unit tests) |
| `npm run test:e2e` | Playwright (E2E tests) |

## Key Libraries

- **React Router v7** — client-side routing
- **TanStack Query** — server state management + caching
- **Zustand** — client state (auth store, org store)
- **React Hook Form + Zod** — form handling + validation
- **shadcn/ui + Tailwind CSS v4** — component library + styling
- **Axios** — HTTP client with cookie-based auth
