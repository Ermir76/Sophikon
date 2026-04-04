# Dashboard

Status: `Closed`
Owner: `Gemini CLI`
Severity summary: `P0: 0 | P1: 0 | P2: 2`

## Review State Legend

- `PASS`: reviewed and acceptable
- `FAIL`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `BLOCKED`: could not be signed off because another issue prevented meaningful verification

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
| Exact screens, routes, dialogs, and panels included are defined | `PASS` | Routes defined in `App.tsx` and implemented in `DashboardPage.tsx`. |
| Out-of-scope adjacent behavior is defined | `PASS` | Clear separation between global dashboard and project workspace. |
| Feature start point for the user is clear | `PASS` | Post-login redirect to `/`. |
| Feature end point for the user is clear | `PASS` | Navigation to projects or settings via cards/sidebar. |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All routes, buttons, menus, and deep links into the feature are listed | `PASS` | Sidebar navigation, breadcrumbs, and logo links all point to `/`. |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `PASS` | Data fetches correctly and renders widgets based on active organization. |
| Success state is clear | `PASS` | Headings and data visualizations confirm successful load. |
| Data persists after refresh if expected | `PASS` | Search params (`dash_window`, etc.) ensure time window persists after refresh. |
| Navigation after success makes sense | `PASS` | Drill-down links on KPI cards and project table work as expected. |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Empty input states checked | `PASS` | Handled via `isCustomInvalid` check in `DashboardPage.tsx`. |
| Invalid input states checked | `PASS` | Backend `resolve_window_or_422` validates start/end dates. |
| API/server failure path checked | `PASS` | `isInsightsError` triggers `QueryError` with retry capability. |
| User can recover from failure | `PASS` | Retry button available on error states. |
| Error copy is understandable | `PASS` | Uses `getErrorMessage(error)` to display backend-provided details. |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Loading state is visible and not confusing | `PASS` | `PageLoading` used for initial fetch; opacity-90 + "Refreshing..." text for background fetches. |
| Empty state is intentional and helpful | `PASS` | `PageEmpty` shown if no organization is active; project-specific sections show "No data" messages. |
| Refresh behavior does not break state | `PASS` | TanStack Query handles background refresh without layout shift. |

### Correctness Checks

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Sorting and filtering are correct where relevant | `PASS` | Project health table supports sorting by Risk Score or Completion %; filters by time window. |
| Derived values and calculations are correct where relevant | `PASS` | KPI metrics and project health scores are computed in `insights_service.py`. |
| Status transitions are valid where relevant | `PASS` | Project status and risk levels are accurately reflected from models. |
| Timestamps and timezones are correct where relevant | `PASS` | `resolve_business_day` in `time_policy.py` handles timezone resolution before falling back to `date.today()`. |

### Data / Time / State Integrity

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Cache invalidation / stale data risks checked | `PASS` | `dashboardInsightsKeys` includes window parameters to prevent stale data between filters. |
| Persistence after refresh checked | `PASS` | State stored in URL search params via `useTimeWindowFilter`. |
| Realtime/websocket behavior checked where relevant | `PASS` | Global dashboard intentionally lacks WebSocket integration to prioritize stable overview; refresh logic is sufficient. |
| Invalid data states are prevented or handled safely | `PASS` | `resolve_window` handles invalid presets and date ranges on the backend. |

### Backend / Logic Trace

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Relevant API endpoints checked | `PASS` | `/organizations/{org_id}/insights/dashboard` is correctly structured. |
| Relevant backend service logic checked | `PASS` | `insights_service.get_org_dashboard_insights` avoids N+1 by bulk fetching. |
| Relevant repository/query logic checked | `PASS` | `insights_repo` methods handle bulk data retrieval efficiently. |
| Relevant schema/model constraints checked | `PASS` | `DASH-02`: Identified N+1 risk was verified as absent in the global dashboard service. |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Role differences were checked where relevant | `PASS` | `get_org_access_or_404` ensures user belongs to organization; all members share dashboard visibility. |
| Authorized actions work | `PASS` | Organization members can view insights. |
| Unauthorized actions are blocked clearly | `PASS` | Blocked at the dependency level via `PermissionDeniedError`. |
| UI does not expose misleading actions | `PASS` | Dashboard is primarily read-only; no unauthorized modification actions present. |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Primary action is obvious | `PASS` | Dashboard intent as an overview is clear. |
| Labels are human-readable | `PASS` | Metric labels and chart legends are concise and clear. |
| Important content is visible | `PASS` | Grid layout prioritizes high-level KPIs at the top. |
| Layout is not cramped or confusing | `PASS` | Sections are well-defined with consistent spacing. |
| Feedback is timely and understandable | `PASS` | `DASH-01`: Verified that Recent Activity items ARE clickable and navigate correctly. |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Desktop checked | `PASS` | Grid scales well for wide screens. |
| Mobile checked | `PASS` | KPI cards and widgets stack correctly for narrow viewports. |
| Overflow, clipping, and touch target problems checked | `PASS` | Scrolling containers used for project health and activity tables. |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Existing automated coverage reviewed | `PASS` | `DashboardPage.test.tsx` exists and covers basic rendering and org loading logic. |
| Missing high-risk test cases listed | `PASS` | Gaps in sorting/empty state coverage noted as `P2` cleanup. |

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| DASH-05 | P2 | Testing | Unit tests miss interaction logic (sorting, welcome state). | Add coverage to `DashboardPage.test.tsx`. | Accepted for launch. |
| DASH-07 | P2 | Polish | Execution Trend chart has fixed height that might feel small on ultra-wide screens. | Consider responsive height or aspect ratio. | Observation. |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All `P0` items retested | `PASS` | No `P0` issues found. |
| Important `P1` items retested | `PASS` | No `P1` issues remain. |
| No regression introduced by fixes | `PASS` | |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Feature boundary is clear | `PASS` | |
| Critical user promises are satisfied | `PASS` | |
| Happy path is reliable | `PASS` | |
| No open `P0` issues remain | `PASS` | |
| Correctness checks passed | `PASS` | |
| Data / time / state integrity is acceptable | `PASS` | |
| Backend / logic trace leaves no unresolved trust-breaking risk | `PASS` | |
| Key UX blockers are addressed or explicitly accepted | `PASS` | |
| Remaining gaps are documented | `PASS` | |
| Feature can be demonstrated without embarrassment-level failure | `PASS` | |
| Feature is safe to mark `Closed` | `PASS` | **Closed.** |
