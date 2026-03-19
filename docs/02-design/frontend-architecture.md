# Frontend Architecture

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
│   │   │   ├── ProjectSettingsPage.tsx
│   │   │   └── ProjectInvitationAcceptPage.tsx
│   │   ├── components/
│   │   │   ├── CreateProjectDialog.tsx
│   │   │   ├── ProjectLayout.tsx
│   │   │   ├── ProjectMembersTab.tsx
│   │   │   └── ProjectActivityFeedCard.tsx
│   │   ├── hooks/
│   │   │   ├── useProjects.ts
│   │   │   ├── useProjectMembers.ts
│   │   │   └── useProjectActivity.ts
│   │   ├── api/
│   │   │   ├── project.service.ts
│   │   │   ├── project-members.service.ts
│   │   │   └── project-activity.service.ts
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
│   ├── kanban/
│   │   ├── pages/
│   │   │   └── KanbanPage.tsx
│   │   ├── components/
│   │   │   ├── KanbanBoard.tsx
│   │   │   ├── KanbanColumn.tsx
│   │   │   ├── KanbanColumnHeader.tsx
│   │   │   ├── KanbanCard.tsx
│   │   │   └── KanbanToolbar.tsx
│   │   ├── hooks/
│   │   │   └── useKanbanDrag.ts
│   │   ├── store/
│   │   │   └── kanban-store.ts
│   │   ├── types.ts
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
│   ├── reports/
│   │   ├── pages/
│   │   │   └── ReportsPage.tsx
│   │   └── index.ts
│   │
│   ├── notifications/
│   │   ├── hooks/
│   │   │   ├── useNotifications.ts
│   │   │   └── useNotificationWebSocket.ts
│   │   ├── api/
│   │   │   └── notification.service.ts
│   │   ├── store/
│   │   │   └── notification-websocket-store.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   └── ai/
│       ├── components/
│       │   ├── AiDockedPanel.tsx        ← main panel container
│       │   ├── PlanApprovalCard.tsx     ← shows agent plan, approve/redirect
│       │   ├── ReasoningStep.tsx        ← collapsible agent reasoning display
│       │   └── ToolCallRow.tsx          ← live tool call + result display
│       ├── hooks/
│       │   ├── useAi.ts                 ← chat stream, plan approval
│       │   └── useConversations.ts      ← load/resume past conversations
│       ├── api/
│       │   └── ai.service.ts
│       ├── store/
│       │   └── ai-panel-store.ts
│       ├── types.ts
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

## Visual Architecture Rules

1. `src/index.css` — design tokens, app-level visual defaults
2. `src/shared/ui/*` — base widget layer (shadcn foundation), controlled changes only
3. `src/shared/*` adapters — app-semantic wrappers, normalize drift from base layer
4. `src/features/**` — composition and state rendering only, no local design systems

Reference: `docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`
