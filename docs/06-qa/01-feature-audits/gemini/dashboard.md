# Dashboard

Status:
Owner: `Gemini CLI`
Severity summary: `P0: 0 | P1: 0 | P2: 0`

## Review State Legend

- `NOT CHECKED`: reviewed and acceptable
- `NOT CHECKED`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `NOT CHECKED`: could not be signed off because another issue prevented meaningful verification

Rule: every audit line must use one of these states. Never rely on a bare unchecked checkbox.

## Boundary Notes

- The Dashboard (`/`) is the primary landing page after login, providing a global view of all projects within the active organization.
- Included: KPI metrics (active/completed projects, task completion %, overdue/critical tasks, overallocated resources), Execution Trend chart, Project Health table with risk/completion sorting, and Recent Activity feed.
- Out of scope: Project-specific dashboards, AI panel interactions, and organization management settings.

## Critical User Promises

- Provide an accurate, high-level summary of execution status and risk across the entire organization.
- Allow users to filter insights by standard and custom time windows with state persistence.
- Act as a fast navigation hub for drilling down into project-specific data.

## Review Matrix

### Feature Boundary

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `NOT CHECKED` | Routes defined in `App.tsx` and implemented in `DashboardPage.tsx`. |
| Out-of-scope adjacent behavior is defined | `NOT CHECKED` | Clear separation between global dashboard and project workspace. |
| Feature start point for the user is clear | `NOT CHECKED` | Post-login redirect to `/`. |
| Feature end point for the user is clear | `NOT CHECKED` | Navigation to projects or settings via cards/sidebar. |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All routes, buttons, menus, and deep links into the feature are listed | `NOT CHECKED` | Sidebar navigation, breadcrumbs, and logo links all point to `/`. |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `NOT CHECKED` | Data fetches correctly and renders widgets based on active organization. |
| Success state is clear | `NOT CHECKED` | Headings and data visualizations confirm successful load. |
| Data persists after refresh if expected | `NOT CHECKED` | Search params (`dash_window`, etc.) ensure time window persists after refresh. |
| Navigation after success makes sense | `NOT CHECKED` | Drill-down links on KPI cards and project table work as expected. |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Empty input states checked | `NOT CHECKED` | Handled via `isCustomInvalid` check in `DashboardPage.tsx`. |
| Invalid input states checked | `NOT CHECKED` | Backend `resolve_window_or_422` validates start/end dates. |
| API/server failure path checked | `NOT CHECKED` | `isInsightsError` triggers `QueryError` with retry capability. |
| User can recover from failure | `NOT CHECKED` | Retry button available on error states. |
| Error copy is understandable | `NOT CHECKED` | Uses `getErrorMessage(error)` to display backend-provided details. |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Loading state is visible and not confusing | `NOT CHECKED` | `PageLoading` used for initial fetch; opacity-90 + "Refreshing..." text for background fetches. |
| Empty state is intentional and helpful | `NOT CHECKED` | `PageEmpty` shown if no organization is active; project-specific sections show "No data" messages. |
| Refresh behavior does not break state | `NOT CHECKED` | TanStack Query handles background refresh without layout shift. |

### Correctness Checks

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Sorting and filtering are correct where relevant | `NOT CHECKED` | Project health table supports sorting by Risk Score or Completion %; filters by time window. |
| Derived values and calculations are correct where relevant | `NOT CHECKED` | KPI metrics and project health scores are computed in `insights_service.py`. |
| Status transitions are valid where relevant | `NOT CHECKED` | Project status and risk levels are accurately reflected from models. |
| Timestamps and timezones are correct where relevant | `NOT CHECKED` | `DASH-06`: Backend uses `date.today()` for window resolution, which is timezone-agnostic on the server. |

### Data / Time / State Integrity

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Cache invalidation / stale data risks checked | `NOT CHECKED` | `dashboardInsightsKeys` includes window parameters to prevent stale data between filters. |
| Persistence after refresh checked | `NOT CHECKED` | State stored in URL search params via `useTimeWindowFilter`. |
| Realtime/websocket behavior checked where relevant | `NOT CHECKED` | `DASH-03`: Global dashboard lacks the WebSocket integration present in project-level views. |
| Invalid data states are prevented or handled safely | `NOT CHECKED` | `resolve_window` handles invalid presets and date ranges on the backend. |

### Backend / Logic Trace

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Relevant API endpoints checked | `NOT CHECKED` | `/organizations/{org_id}/insights/dashboard` is correctly structured. |
| Relevant backend service logic checked | `NOT CHECKED` | `insights_service.get_org_dashboard_insights` implements the core logic. |
| Relevant repository/query logic checked | `NOT CHECKED` | `insights_repo` methods handle data retrieval with deletion filters. |
| Relevant schema/model constraints checked | `NOT CHECKED` | `DASH-02`: N+1 performance pattern identified in `_project_overallocation_stats`. |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Role differences were checked where relevant | `NOT CHECKED` | `get_org_access_or_404` ensures user belongs to organization; all members currently share dashboard visibility. |
| Authorized actions work | `NOT CHECKED` | Organization members can view insights. |
| Unauthorized actions are blocked clearly | `NOT CHECKED` | Blocked at the dependency level via `PermissionDeniedError`. |
| UI does not expose misleading actions | `NOT CHECKED` | Dashboard is primarily read-only; no unauthorized modification actions present. |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Primary action is obvious | `NOT CHECKED` | Dashboard intent as an overview is clear. |
| Labels are human-readable | `NOT CHECKED` | Metric labels and chart legends are concise and clear. |
| Important content is visible | `NOT CHECKED` | Grid layout prioritizes high-level KPIs at the top. |
| Layout is not cramped or confusing | `NOT CHECKED` | Sections are well-defined with consistent spacing. |
| Feedback is timely and understandable | `NOT CHECKED` | `DASH-01`: Recent Activity items are not clickable, violating the "navigation hub" promise. |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Desktop checked | `NOT CHECKED` | Grid scales well for wide screens. |
| Mobile checked | `NOT CHECKED` | KPI cards and widgets stack correctly for narrow viewports. |
| Overflow, clipping, and touch target problems checked | `NOT CHECKED` | Scrolling containers used for project health and activity tables. |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Existing automated coverage reviewed | `NOT CHECKED` | `DASH-05`: No unit tests exist for the main `DashboardPage.tsx` component. |
| Missing high-risk test cases listed | `NOT CHECKED` | Gap identified: Unit tests for component rendering and user interactions (sorting/filtering). |

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All `P0` items retested | `NOT CHECKED` | No `P0` issues found. |
| Important `P1` items retested | `NOT CHECKED` | |
| No regression introduced by fixes | `NOT CHECKED` | |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Feature boundary is clear | `NOT CHECKED` | |
| Critical user promises are satisfied | `NOT CHECKED` | Navigation hub promise partially broken by non-clickable activity items. |
| Happy path is reliable | `NOT CHECKED` | |
| No open `P0` issues remain | `NOT CHECKED` | |
| Correctness checks passed | `NOT CHECKED` | Timezone risk with `date.today()`. |
| Data / time / state integrity is acceptable | `NOT CHECKED` | Missing realtime updates. |
| Backend / logic trace leaves no unresolved trust-breaking risk | `NOT CHECKED` | N+1 performance risk. |
| Key UX blockers are addressed or explicitly accepted | `NOT CHECKED` | Static activity feed is a minor but notable UX blocker. |
| Remaining gaps are documented | `NOT CHECKED` | |
| Feature can be demonstrated without embarrassment-level failure | `NOT CHECKED` | |
| Feature is safe to mark `Closed` | `NOT CHECKED` | **Audit Failed** due to multiple `P1` issues affecting performance, correctness, and UX. |
