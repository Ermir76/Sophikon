# Frontend Architecture

> **Created:** 2026-02-17
> **Pattern:** Feature-based (domain slices)
> **Rule:** Every new file must follow this structure. No exceptions.

---

## Directory Structure

```
src/
├── app/
│   ├── App.tsx
│   ├── App.test.tsx
│   ├── main.tsx
│   ├── routes.tsx
│   ├── NotFoundPage.tsx
│   └── routing/
│       ├── ProtectedRoute.tsx
│       ├── ProtectedRoute.test.tsx
│       ├── GuestRoute.tsx
│       └── OrgGuard.tsx
│
├── features/
│   ├── auth/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useAuth.test.tsx
│   │   ├── api/
│   │   │   └── auth.service.ts
│   │   ├── store/
│   │   │   ├── auth-store.ts
│   │   │   └── auth-store.test.ts
│   │   ├── lib/
│   │   │   └── auth.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── organizations/
│   │   ├── pages/
│   │   │   ├── OrgSettingsPage.tsx
│   │   │   └── OrgMembersPage.tsx
│   │   ├── components/
│   │   │   ├── OrgSwitcher.tsx
│   │   │   ├── CreateOrgDialog.tsx
│   │   │   ├── InviteMemberDialog.tsx
│   │   │   ├── MembersTable.tsx
│   │   │   └── MemberActions.tsx
│   │   ├── hooks/
│   │   │   ├── useOrganizations.ts
│   │   │   └── useMyOrgRole.ts
│   │   ├── api/
│   │   │   └── organization.service.ts
│   │   ├── store/
│   │   │   ├── org-store.ts
│   │   │   └── org-store.test.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── projects/
│   │   ├── pages/
│   │   │   ├── ProjectsPage.tsx
│   │   │   ├── ProjectOverviewPage.tsx
│   │   │   └── ProjectSettingsPage.tsx
│   │   ├── components/
│   │   │   ├── CreateProjectDialog.tsx
│   │   │   └── ProjectLayout.tsx
│   │   ├── hooks/
│   │   │   └── useProjects.ts
│   │   ├── api/
│   │   │   └── project.service.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── dashboard/
│   │   ├── pages/
│   │   │   └── DashboardPage.tsx
│   │   └── index.ts
│   │
│   ├── tasks/
│   │   ├── pages/
│   │   │   └── TasksPage.tsx
│   │   └── index.ts
│   │
│   ├── gantt/
│   │   ├── pages/
│   │   │   └── GanttPage.tsx
│   │   └── index.ts
│   │
│   ├── calendar/
│   │   ├── pages/
│   │   │   └── CalendarPage.tsx
│   │   └── index.ts
│   │
│   ├── resources/
│   │   ├── pages/
│   │   │   └── ResourcesPage.tsx
│   │   └── index.ts
│   │
│   └── reports/
│       ├── pages/
│       │   └── ReportsPage.tsx
│       └── index.ts
│
├── shared/
│   ├── ui/
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── AppLayout.tsx
│   │   ├── AppSidebar.tsx
│   │   ├── AppHeader.tsx
│   │   ├── AuthLayout.tsx
│   │   └── NavUser.tsx
│   ├── components/
│   │   ├── ErrorBoundary.tsx
│   │   ├── PageLoader.tsx
│   │   └── QueryError.tsx
│   ├── hooks/
│   │   └── use-mobile.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   ├── errors.ts
│   │   └── roles.ts
│   ├── api/
│   │   ├── api.ts
│   │   └── api.test.ts
│   └── types/
│       └── api.ts
│
├── config/
│   └── react-query.ts
│
└── test/
    └── setup.ts
```

---

## Rules

### 1. Organize by feature, not by file type

Each feature owns its pages, components, hooks, API layer, store, and types. Nothing leaks across features.

### 2. shared/ = truly shared

A file goes in `shared/` only if it is used by 2+ features. If it's specific to one feature, it stays in that feature's folder.

### 3. State near usage

- Zustand store per feature (inside `features/{name}/store/`)
- React Query hooks per feature (inside `features/{name}/hooks/`)
- No global state dump

### 4. Barrel exports

Each feature has an `index.ts` that re-exports its public API:

```ts
// features/organizations/index.ts
export * from "./hooks/useOrganizations";
export * from "./hooks/useMyOrgRole";
export * from "./components/OrgSwitcher";
```

Imports from outside the feature use the barrel:

```ts
import { useOrganizations } from "@/features/organizations";
```

### 5. Absolute imports only

```ts
// Good
import { Button } from "@/shared/ui/button";
import { useProjects } from "@/features/projects";

// Bad
import { Button } from "../../../shared/ui/button";
```

### 6. Naming conventions

| Type       | Convention                      | Example                   |
| ---------- | ------------------------------- | ------------------------- |
| Pages      | PascalCase + `Page` suffix      | `ProjectsPage.tsx`        |
| Components | PascalCase                      | `CreateOrgDialog.tsx`     |
| Hooks      | camelCase + `use` prefix        | `useProjects.ts`          |
| Services   | kebab-case + `.service` suffix  | `organization.service.ts` |
| Stores     | kebab-case + `-store` suffix    | `auth-store.ts`           |
| Types      | `types.ts` per feature          | `features/auth/types.ts`  |
| Tests      | co-located, same name + `.test` | `auth-store.test.ts`      |

---

## Migration Map

Current file location → target location.

| Current                                         | Target                                                               |
| ----------------------------------------------- | -------------------------------------------------------------------- |
| `main.tsx`                                      | `app/main.tsx`                                                       |
| `App.tsx`                                       | `app/App.tsx`                                                        |
| `components/ProtectedRoute.tsx`                 | `app/routing/ProtectedRoute.tsx`                                     |
| `components/GuestRoute.tsx`                     | `app/routing/GuestRoute.tsx`                                         |
| `components/OrgGuard.tsx`                       | `app/routing/OrgGuard.tsx`                                           |
| `components/ErrorBoundary.tsx`                  | `shared/components/ErrorBoundary.tsx`                                |
| `components/PageLoader.tsx`                     | `shared/components/PageLoader.tsx`                                   |
| `components/QueryError.tsx`                     | `shared/components/QueryError.tsx`                                   |
| `components/layout/AppLayout.tsx`               | `shared/layout/AppLayout.tsx`                                        |
| `components/layout/AppSidebar.tsx`              | `shared/layout/AppSidebar.tsx`                                       |
| `components/layout/AppHeader.tsx`               | `shared/layout/AppHeader.tsx`                                        |
| `components/layout/AuthLayout.tsx`              | `shared/layout/AuthLayout.tsx`                                       |
| `components/layout/NavUser.tsx`                 | `shared/layout/NavUser.tsx`                                          |
| `components/layout/OrgSwitcher.tsx`             | `features/organizations/components/OrgSwitcher.tsx`                  |
| `components/layout/ProjectLayout.tsx`           | `features/projects/components/ProjectLayout.tsx`                     |
| `components/ui/*`                               | `shared/ui/*` (no change)                                            |
| `pages/auth/LoginPage.tsx`                      | `features/auth/pages/LoginPage.tsx`                                  |
| `pages/auth/RegisterPage.tsx`                   | `features/auth/pages/RegisterPage.tsx`                               |
| `pages/DashboardPage.tsx`                       | `features/dashboard/pages/DashboardPage.tsx`                         |
| `pages/CreateOrganizationPage.tsx`              | **DELETE** → `features/organizations/components/CreateOrgDialog.tsx` |
| `pages/settings/OrgSettingsPage.tsx`            | `features/organizations/pages/OrgSettingsPage.tsx`                   |
| `pages/settings/OrgMembersPage.tsx`             | `features/organizations/pages/OrgMembersPage.tsx`                    |
| `pages/settings/members/InviteMemberDialog.tsx` | `features/organizations/components/InviteMemberDialog.tsx`           |
| `pages/settings/members/MembersTable.tsx`       | `features/organizations/components/MembersTable.tsx`                 |
| `pages/settings/members/MemberActions.tsx`      | `features/organizations/components/MemberActions.tsx`                |
| `pages/ProjectsPage.tsx`                        | `features/projects/pages/ProjectsPage.tsx`                           |
| `pages/ProjectOverviewPage.tsx`                 | `features/projects/pages/ProjectOverviewPage.tsx`                    |
| `pages/ProjectSettingsPage.tsx`                 | `features/projects/pages/ProjectSettingsPage.tsx`                    |
| `pages/projects/CreateProjectDialog.tsx`        | `features/projects/components/CreateProjectDialog.tsx`               |
| `pages/TasksPage.tsx`                           | `features/tasks/pages/TasksPage.tsx`                                 |
| `pages/GanttPage.tsx`                           | `features/gantt/pages/GanttPage.tsx`                                 |
| `pages/CalendarPage.tsx`                        | `features/calendar/pages/CalendarPage.tsx`                           |
| `pages/ResourcesPage.tsx`                       | `features/resources/pages/ResourcesPage.tsx`                         |
| `pages/ReportsPage.tsx`                         | `features/reports/pages/ReportsPage.tsx`                             |
| `pages/NotFoundPage.tsx`                        | `app/NotFoundPage.tsx`                                               |
| `hooks/useAuth.ts`                              | `features/auth/hooks/useAuth.ts`                                     |
| `hooks/useAuth.test.tsx`                        | `features/auth/hooks/useAuth.test.tsx`                               |
| `hooks/useHooks.test.tsx`                       | **SPLIT** per feature                                                |
| `hooks/useOrganizations.ts`                     | `features/organizations/hooks/useOrganizations.ts`                   |
| `hooks/useMyOrgRole.ts`                         | `features/organizations/hooks/useMyOrgRole.ts`                       |
| `hooks/useProjects.ts`                          | `features/projects/hooks/useProjects.ts`                             |
| `hooks/use-mobile.ts`                           | `shared/hooks/use-mobile.ts`                                         |
| `services/api.ts`                               | `shared/api/api.ts`                                                  |
| `services/api.test.ts`                          | `shared/api/api.test.ts`                                             |
| `services/auth.ts`                              | `features/auth/api/auth.service.ts`                                  |
| `services/organization.ts`                      | `features/organizations/api/organization.service.ts`                 |
| `services/project.ts`                           | `features/projects/api/project.service.ts`                           |
| `store/auth-store.ts`                           | `features/auth/store/auth-store.ts`                                  |
| `store/auth-store.test.ts`                      | `features/auth/store/auth-store.test.ts`                             |
| `store/org-store.ts`                            | `features/organizations/store/org-store.ts`                          |
| `store/org-store.test.ts`                       | `features/organizations/store/org-store.test.ts`                     |
| `lib/auth.ts`                                   | `features/auth/lib/auth.ts`                                          |
| `lib/errors.ts`                                 | `shared/lib/errors.ts`                                               |
| `lib/roles.ts`                                  | `shared/lib/roles.ts`                                                |
| `lib/utils.ts`                                  | `shared/lib/utils.ts`                                                |
| `lib/react-query.ts`                            | `config/react-query.ts`                                              |
| `types/api.ts`                                  | `shared/types/api.ts`                                                |
| `types/organization.ts`                         | `features/organizations/types.ts`                                    |
| `types/project.ts`                              | `features/projects/types.ts`                                         |
