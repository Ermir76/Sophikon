# Dashboard

Status: `Closed`
Owner: `wwwer`
Severity summary: `P0: 0 | P1: 0 | P2: 0`

## Audit File

`docs/06-qa/01-feature-audits/dashboard.md`

## Feature Boundary

The dashboard is the authenticated organization-level landing page at `/`. It includes the KPI grid, time-window filter, execution trend chart, project health table, and recent activity feed for the currently active organization. Excluded: project-level overview dashboards under `/projects/:projectId`, org settings/member management, and the AI panel.

## Critical User Promises

- Give an accurate, fast organization-level summary of execution and risk.
- Distinguish loading, error, no-org, and no-data states clearly enough for a post-login landing page.
- Provide credible navigation shortcuts into the project surface without misleading drill-downs.

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| None | - | - | No open dashboard issues were confirmed in this pass. | The feature can only stay `Closed` while targeted dashboard tests continue to pass and new landing-page regressions are added with direct coverage. | Current pass rechecked the previously reported dashboard bug cluster against code and targeted tests. |

## Review Matrix

### Feature Boundary

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `PASS` | `frontend/src/app/App.tsx` mounts `/` to `DashboardPage` inside `ProtectedRoute` and `AppLayout`. |
| Out-of-scope adjacent behavior is defined | `PASS` | Project overview/dashboard remains separate under `/projects/:projectId`. |
| Feature start point for the user is clear | `PASS` | This is the authenticated app landing page and the global sidebar "Dashboard" destination. |
| Feature end point for the user is clear | `PASS` | KPI cards route to `/projects`; project-health rows and recent activity route into project-scoped surfaces. |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| App landing page after login | `PASS` | `/` resolves to `DashboardPage` in `frontend/src/app/App.tsx`. |
| Sidebar navigation to dashboard | `PASS` | `AppSidebar.tsx` exposes a global "Dashboard" nav item to `/`. |
| Active organization context exists before org-scoped fetch | `PASS` | `OrgSwitcher.tsx` auto-selects the first organization when none is active; `DashboardPage.tsx` handles the bootstrap gap explicitly. |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Dashboard loads without crash | `PASS` | `DashboardPage.tsx` guards org bootstrap, org fetch, and insights fetch separately. `DashboardPage.test.tsx` covers bootstrap loading and bootstrap error paths. |
| Key stats/widgets render correctly | `PASS` | KPI grid, trend card, health table, and recent activity all render from `DashboardInsightsResponse`. API test `test_dashboard_insights_success` verifies the org dashboard payload shape. |
| Navigation links from dashboard land in correct place | `PASS` | KPI cards intentionally route to `/projects`; project-health rows link to `/projects/{projectId}`; activity items route to project/task/resource surfaces. `DashboardPage.test.tsx` and `insights-activity-card.test.tsx` cover these paths. |
| Refresh preserves correct state | `PASS` | `useTimeWindowFilter("dash")` stores window selection in URL params (`dash_window`, `dash_start`, `dash_end`). Active org persists in Zustand storage. |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| API error state checked | `PASS` | Org and insights failures render `QueryError` with retry affordances in `DashboardPage.tsx`. |
| Empty/no-data state checked | `PASS` | No active org renders a dedicated `PageEmpty`; empty project health and activity sections render intentional empty-copy states. |
| Invalid custom window checked | `PASS` | Frontend blocks incomplete custom ranges with inline copy; backend returns `422` via `resolve_window_or_422`. `test_insights_custom_window_requires_dates` covers the backend guard. |
| Partial data or delayed data does not break layout | `PASS` | Dashboard renders background refetch state via `isFetching` and zero/default fallbacks rather than hard crashing. |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Page loader is acceptable | `PASS` | Full-page loading state is shown during org bootstrap and first insights load. |
| Empty state is intentional and helpful | `PASS` | Empty copy distinguishes "no organization selected" from fetch errors and empty widgets. |
| Refresh behavior does not break state | `PASS` | Query key includes org ID and window params; URL state survives refresh; background refetch only softens opacity and shows a refresh hint. |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Auth required | `PASS` | Route is behind `ProtectedRoute`. |
| Organization membership enforced | `PASS` | Backend endpoint uses `get_org_access_or_404`, which requires an `OrganizationMember` row. |
| Role-sensitive content checked where relevant | `PASS` | Current dashboard is read-only for org members; no misleading privileged actions are exposed on the page. |
| Unauthorized actions fail clearly | `PASS` | Unauthorized access is blocked at the dependency layer before insights aggregation. |

### Correctness Checks

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Sorting and filtering are correct where relevant | `PASS` | Project health can be sorted by risk or completion in `DashboardPage.tsx`; window selection is part of the query key and request params. |
| Derived values and calculations are correct where relevant | `PASS` | `get_org_dashboard_insights` computes KPI totals, risk score, risk level, trend buckets, and over-allocation counts in one aggregation path. |
| Date-only trend rendering is correct | `PASS` | `InsightsTrendCard` uses `parseISO` for date-only buckets rather than UTC-coercing `new Date("YYYY-MM-DD")`. `insights-trend-card.test.tsx` covers the regression. |
| Time-window resolution is scoped correctly | `PASS` | `resolve_window` and org-dashboard `today` both use `resolve_business_day(organization=organization)` rather than ad hoc `date.today()` in the dashboard flow. |
| Status labels match actual state | `PASS` | `ProjectHealthItem.status` comes directly from the project model enum and risk badges derive from consistent thresholds. |

### Backend / Logic Trace

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Relevant API endpoint checked | `PASS` | `backend/app/api/v1/endpoints/insights.py` mounts `GET /organizations/{org_id}/insights/dashboard` with org access enforcement and response validation. |
| Relevant backend service logic checked | `PASS` | `backend/app/service/insights_service.py` aggregates org projects, tasks, resources, assignments, trend, and recent activity through the service layer. |
| Relevant repository/query logic checked | `PASS` | Org dashboard fetches projects/tasks/resources/assignments via repository helpers and batched over-allocation aggregation; the prior per-project N+1 pattern is no longer present. |
| Relevant schema/model constraints checked | `PASS` | `DashboardInsightsResponse` constrains KPI percentages and risk scores to `0..100` and validates trend/activity payload shape. |

### Refresh / Persistence / Realtime

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Page refresh keeps or restores correct state | `PASS` | URL params preserve the time window; persisted org store preserves active org. |
| Stale cache risks checked | `PASS` | `dashboardInsightsKeys.detail` keys by feature, org, preset, start date, and end date. |
| Realtime behavior checked where relevant | `PASS` | No global dashboard websocket is mounted today, but the current product promise is periodic/query-driven freshness rather than realtime org analytics. This is acceptable for current scope. |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| First impression is strong enough for demo use | `PASS` | The landing page now opens with a stable loader, clear KPI-first hierarchy, and working navigation affordances. |
| Most important information is visually obvious | `PASS` | KPI grid sits first, followed by the trend/health/activity split. |
| Cards/sections do not feel cluttered | `PASS` | Layout uses clear sectioning, scroll containment for dense tables/feeds, and empty-state copy where needed. |
| Copy is human-readable | `PASS` | Labels and descriptions are concise and user-facing rather than internal/debug phrasing. |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Desktop checked | `PASS` | Desktop layout uses the intended three-column composition with sticky activity rail and full table visibility. |
| Mobile checked | `PASS` | KPI grid and main content collapse through `sm`/`xl` breakpoints without fixed-width dashboard-only layout traps in the audited code. |
| Card stacking and spacing checked | `PASS` | Responsive grid and overflow containers are explicit in `DashboardPage.tsx`; no dashboard-local hard-coded width blockers were found in this pass. |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Dashboard test coverage reviewed | `PASS` | Reran targeted frontend tests: `DashboardPage`, `useDashboardInsights`, `InsightsTrendCard`, `InsightsActivityCard` -> `7 passed` on 2026-04-03. |
| Backend org-dashboard test coverage reviewed | `PASS` | Reran targeted backend suite: `backend/tests/unit/service/test_insights_service.py` -> `11 passed` on 2026-04-03. Org-dashboard API tests also exist in `backend/tests/unit/api/v1/test_insights.py`. |
| Missing high-risk tests listed | `PASS` | No new high-risk dashboard-specific gap was large enough to block closure in this pass. Continued expectation: keep direct tests whenever dashboard aggregation or routing changes. |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Critical dashboard paths retested | `PASS` | Prior dashboard audit issues were rechecked against current code and targeted automated tests. No issue remained reproducible from code/test evidence. |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Feature boundary is clear | `PASS` | |
| Critical user promises are verified | `PASS` | |
| Happy path works end-to-end | `PASS` | |
| No open `P0` issues remain | `PASS` | |
| Correctness checks passed | `PASS` | |
| Backend / logic trace leaves no unresolved trust-breaking issue | `PASS` | |
| Refresh / persistence / realtime behavior is acceptable | `PASS` | |
| Role checks are correct | `PASS` | |
| Test gaps are listed | `PASS` | |
| Re-review passed after fixes | `PASS` | |
| Feature is safe to mark `Closed` | `PASS` | Dashboard meets the closure gate in this code-and-test-based audit pass. |

## Audit Notes

- This pass used the dashboard audit file plus direct code inspection of the route, page, shared UI, endpoint, schema, service, repository usage, and targeted tests.
- Verification rerun on 2026-04-03:
  - Frontend: `DashboardPage`, `useDashboardInsights`, `InsightsTrendCard`, `InsightsActivityCard` -> `7 passed`
  - Backend: `test_insights_service.py` -> `11 passed`
- Status decision for this pass: `Closed`
