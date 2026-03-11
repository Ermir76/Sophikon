# Frontend

## Overview

React 19 single-page application built with Vite, TypeScript 5.9, and Tailwind CSS 4.1. The UI uses **shadcn/ui** as the component foundation with a custom design token system supporting light + dark themes.

## Architecture Pattern: Feature-Sliced

The frontend is organized by **feature domain**, not by file type. Each feature is a self-contained module:

```
features/{name}/
├── pages/          # Route-level components (default exports)
├── components/     # Feature-specific UI components (named exports)
├── hooks/          # React Query hooks, custom hooks
├── api/            # API service layer (*.service.ts)
├── store/          # Zustand store (*-store.ts)
├── types.ts        # Feature-specific TypeScript types
└── index.ts        # Barrel exports (public API)
```

### 11 Feature Modules

| Feature          | Key Pages/Components                                         |
| ---------------- | ------------------------------------------------------------ |
| `auth`           | LoginPage, RegisterPage, auth store, JWT management          |
| `organizations`  | OrgSettingsPage, OrgMembersPage, OrgSwitcher, CreateOrgDialog |
| `projects`       | ProjectsPage, ProjectOverviewPage, ProjectLayout, invite flow |
| `dashboard`      | DashboardPage                                                |
| `tasks`          | TasksPage (spreadsheet-like table, inline editing)           |
| `gantt`          | GanttPage (custom canvas renderer)                           |
| `calendar`       | CalendarPage                                                 |
| `resources`      | ResourcesPage (sheet, utilization view)                      |
| `reports`        | ReportsPage                                                  |
| `notifications`  | Inbox, WebSocket badge, notification settings                |
| `ai`             | AiDockedPanel (chat), estimation, suggestions                |

### Shared Layer

`shared/` contains only code used by **2+ features**:

| Directory    | Contents                                          |
| ------------ | ------------------------------------------------- |
| `ui/`        | shadcn/ui components (Button, Card, Dialog, etc.) |
| `layout/`    | AppLayout, AppSidebar, AppHeader, AuthLayout      |
| `components/`| ErrorBoundary, PageLoader, QueryError             |
| `hooks/`     | use-mobile                                        |
| `api/`       | Axios client wrapper (`api.ts`)                   |
| `lib/`       | utils, errors (`getErrorMessage`), roles          |
| `types/`     | Shared API types                                  |

## State Management

| Type           | Technology      | Location                | Use Case                              |
| -------------- | --------------- | ----------------------- | ------------------------------------- |
| Server state   | TanStack Query  | `features/*/hooks/`     | API data fetching, caching, mutations |
| Client state   | Zustand          | `features/*/store/`    | Auth token, selected org, AI panel    |
| UI state       | React useState  | Component-local          | Form inputs, modals, transient UI     |

**Rule:** No global state dump. Each feature owns its own store.

## Routing

Uses **React Router 7** with nested routes:

```
/login, /register          → GuestRoute (auth layout)
/app                       → ProtectedRoute → OrgGuard → AppLayout
  /dashboard               → DashboardPage
  /projects                → ProjectsPage
  /projects/:id            → ProjectLayout (nested)
    /overview              → ProjectOverviewPage
    /tasks                 → TasksPage
    /gantt                 → GanttPage
    /calendar              → CalendarPage
    /resources             → ResourcesPage
    /reports               → ReportsPage
    /settings              → ProjectSettingsPage
  /settings/organization   → OrgSettingsPage
  /settings/members        → OrgMembersPage
```

**Guards:**
- `ProtectedRoute` — redirects to `/login` if not authenticated
- `GuestRoute` — redirects to `/app/dashboard` if already authenticated
- `OrgGuard` — ensures user has a selected organization

## Styling System

Strict visual hierarchy (defined in `FRONTEND_STYLING_CONSTITUTION.md`):

| Layer               | Owner                    | Allowed                               | Forbidden                      |
| ------------------- | ------------------------ | ------------------------------------- | ------------------------------ |
| `index.css`         | Design tokens            | CSS variables (light + dark themes)   | Component styles               |
| `shared/ui/*`       | Base widget layer        | Component visuals (shadcn modified)    | Ad-hoc overrides               |
| `features/**`       | Composition              | Layout, composition, state rendering   | Private design systems, glow effects |

**Token-driven colors:** `bg-background`, `text-foreground`, `border-border`
**shadcn variants:** `variant="outline"`, `size="sm"`
**Forbidden:** ad-hoc global hooks, glassmorphism/glow, one-off magic classes, duplicated color logic

## Naming Conventions

| Type       | Convention                      | Example                   |
| ---------- | ------------------------------- | ------------------------- |
| Pages      | PascalCase + `Page` suffix      | `ProjectsPage.tsx`        |
| Components | PascalCase                      | `CreateOrgDialog.tsx`     |
| Hooks      | camelCase + `use` prefix        | `useProjects.ts`          |
| Services   | kebab-case + `.service` suffix  | `organization.service.ts` |
| Stores     | kebab-case + `-store` suffix    | `auth-store.ts`           |
| Types      | `types.ts` per feature          | `features/auth/types.ts`  |
| Tests      | co-located, same name + `.test` | `auth-store.test.ts`      |

## Import Rules

- **Absolute imports only:** `@/shared/ui/button`, never `../../../shared/ui/button`
- **Barrel imports for features:** `import { useProjects } from "@/features/projects"`
- **Pages use default exports**, components use named exports
- **API client:** `shared/api/api.ts` — use `api.get/post/put/delete`, not raw axios
- **Error handling:** `getErrorMessage(error)` from `shared/lib/errors.ts`

## Testing

| Type        | Tool        | Location                        |
| ----------- | ----------- | ------------------------------- |
| Unit tests  | Vitest      | Co-located (`*.test.ts`)        |
| E2E tests   | Playwright  | `frontend/tests/`              |

---

*Evidence: [`docs/02-design/frontend-architecture.md`](../docs/02-design/frontend-architecture.md), [`docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`](../docs/02-design/FRONTEND_STYLING_CONSTITUTION.md), [`CLAUDE.md`](../CLAUDE.md)*
