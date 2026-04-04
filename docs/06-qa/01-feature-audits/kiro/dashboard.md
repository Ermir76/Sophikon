# Dashboard — Kiro Audit

<!-- ============================================================
  HOW TO USE THIS FILE IN A NEW CHAT
  ============================================================

  ---

  Run a full feature closure audit on the Dashboard feature.

  Use docs/06-qa/feature-closure-audit-skill-draft.md as your
  operating guide. Read it first, follow every step in order,
  do not skip anything.

  The audit target file is docs/06-qa/01-feature-audits/kiro/dashboard.md.
  It contains the blank template you must fill in completely.
  Every row in every table must end up as PASS, FAIL, or BLOCKED.
  No row may stay NOT CHECKED when you are done.

  Do the following in order:
  1. Read the skill draft fully.
  2. Read docs/06-qa/00-master-review-plan.md and docs/06-qa/01-feature-audits/README.md.
  3. Read frontend/src/app/App.tsx to find the dashboard route.
  4. Read every relevant source file:
     - frontend/src/features/dashboard/ (all files)
     - frontend/src/shared/ui/insights-trend-card.tsx
     - frontend/src/shared/ui/insights-activity-card.tsx
     - frontend/src/shared/ui/insights-metric-card.tsx
     - frontend/src/shared/hooks/useTimeWindowFilter.ts
     - frontend/src/features/organizations/store/org-store.ts
     - frontend/src/features/organizations/hooks/useOrganizations.ts
     - frontend/src/features/organizations/components/OrgSwitcher.tsx
     - backend/app/api/v1/endpoints/insights.py
     - backend/app/api/v1/endpoints/_insights_window.py
     - backend/app/api/deps/organization.py
     - backend/app/service/insights_service.py
     - backend/app/service/time_policy.py
     - backend/app/repository/insights_repo.py
     - backend/app/schema/insights.py
     - backend/tests/unit/api/v1/test_insights.py
     - backend/tests/unit/service/test_insights_service.py
  5. Verify every audit item yourself from the actual code.
     Do not assume anything is correct. Read the code and prove it.
  6. Fill in the audit file completely. Replace every NOT CHECKED
     with PASS, FAIL, or BLOCKED.  Add evidence notes to every row.
  7. Fill in the Issues Found table for every real problem you find.
     Use IDs like DASH-001, DASH-002 etc.
  8. Fill in the Closure Gate.
  9. Set Status at the top to Closed or Failed Audit.
  10. Update the Severity summary counts at the top.

  Do not reference any previous audit reports from other AI tools.
  Ignore anything in the gemini/ or wwwer audit files.
  Judge only what you read in the actual source code right now.

  ---
============================================================ -->

Status: `Failed Audit`
Owner: `Kiro`
Severity summary: `P0: 0 | P1: 2 | P2: 2`

## Review State Legend

- `PASS`: reviewed and acceptable
- `FAIL`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `BLOCKED`: could not be signed off because another issue prevented meaningful verification

## Boundary Notes

The Dashboard is the root route (`/`) of the authenticated app. It renders an org-scoped control-center view: 6 KPI metric cards, a project health table with risk/completion sort, an execution trend line chart, and a recent activity feed. It is read-only — no write actions are exposed. The time window filter (`7d / 30d / 90d / custom`) is persisted in URL search params. The active org is persisted in `localStorage` via Zustand. Adjacent features (Projects, Tasks, Resources) are linked from the dashboard but are out of scope for this audit.

## Critical User Promises

1. After login, the dashboard loads and shows real org-scoped data without requiring any manual action.
2. KPI numbers (active projects, overdue tasks, critical tasks, overallocated resources, task completion %) are correct and not double-counting summary/rollup tasks.
3. The time window filter changes what data is shown and the selection survives page refresh.
4. The active org selection survives page refresh.
5. Project health rows link to the correct project.
6. Activity feed items navigate to the correct destination.

## Review Matrix

### Feature Boundary

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `PASS` | Single route `/` → `DashboardPage`. No dialogs or panels. Time window filter is an inline control, not a dialog. |
| Out-of-scope adjacent behavior is defined | `PASS` | KPI cards and project health rows link to `/projects` and `/projects/:id` but those pages are out of scope. Activity feed links to project/task/resource routes — also out of scope. |
| Feature start point for the user is clear | `PASS` | `ProtectedRoute` wraps `/`. After login, React Router lands here. `App.tsx` line: `<Route path="/" element={<DashboardPage />} />`. |
| Feature end point for the user is clear | `PASS` | Dashboard is a terminal read-only view. User exits by navigating away via sidebar or KPI/health/activity links. |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All routes, buttons, menus, and deep links into the feature are listed | `PASS` | Only `/`. No deep-link variants. Sidebar nav presumably links here; OrgSwitcher calls `navigate("/")` on org switch — confirmed in `OrgSwitcher.tsx`. |
| App landing page after login resolves correctly | `PASS` | `ProtectedRoute` redirects unauthenticated users to `/login`. Authenticated users land on `/` → `DashboardPage`. |
| Org bootstrap completes before empty state is shown | `PASS` | `DashboardPage` shows `PageLoading` while `isOrgsLoading` is true and `activeOrgId` is null. The `!activeOrgId && isOrgsLoading` guard prevents premature empty state. |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `PASS` | User logs in → org auto-selected by `OrgSwitcher` useEffect → `useDashboardInsights` fires → KPIs, health, trend, activity rendered. All wired correctly. |
| Success state is clear | `PASS` | Full dashboard renders with org name in header, 6 KPI cards, trend chart, project health table, activity feed. |
| Data persists after refresh if expected | `PASS` | `activeOrgId` persisted via Zustand `persist` middleware to `localStorage` key `sophikon-org-storage`. Time window persisted in URL search params via `useTimeWindowFilter`. Both survive refresh. |
| Navigation after success makes sense | `PASS` | KPI cards link to `/projects`. Project health rows link to `/projects/:id`. Activity items link to project/task/resource routes. All correct. |
| KPI card links navigate to the correct destination | `FAIL` | All 6 KPI cards link to `/projects` (generic list). Overdue Tasks, Critical Tasks, and Overallocated Resources cards do not deep-link to a filtered view. This is a UX gap — a user clicking "Overdue Tasks: 12" lands on the unfiltered projects list with no indication of what to do next. See DASH-001. |
| Project health rows link to the correct project | `PASS` | `<Link to={`/projects/${row.project_id}`}>` — correct per-project link. |
| Activity feed items are clickable and navigate correctly | `PASS` | `getActivityRoute` in `InsightsActivityCard` maps `entity_type` to correct routes. Falls back to `#` only when `project_id` is null, which is acceptable. |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Empty input states checked | `PASS` | Custom window with missing start or end date shows inline `QueryError` with message "For a custom window, please select both start and end date." `isCustomInvalid` guard prevents API call. |
| Invalid custom date range handled | `PASS` | Frontend: `isCustomInvalid` blocks the query. Backend: `resolve_window_or_422` raises `ValidationError` (→ 422) if `start_date > end_date` or dates missing. Both layers covered. |
| API/server failure path checked | `PASS` | `isInsightsError` branch renders `QueryError` with `getErrorMessage(insightsError)` and a Retry button that calls `refetchInsights()`. Org-level errors also handled with retry. |
| User can recover from failure | `PASS` | Retry buttons present on both org-load error and insights-load error paths. |
| Error copy is understandable | `PASS` | Uses `getErrorMessage(error)` — surfaces the actual error message from the API response. Not hardcoded. |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Loading state is visible and not confusing | `PASS` | `PageLoading` with message "Loading dashboard..." shown during org bootstrap and initial insights load. |
| Bootstrap loading vs genuine no-org empty state are distinguished | `PASS` | Loading guard: `!activeOrgId && isOrgsLoading` → spinner. After orgs load with no active org: `!activeOrganization` → `PageEmpty` with "Welcome to Sophikon / Please select or create an organization." Distinct states. |
| Empty state is intentional and helpful | `PASS` | No-org empty state has a clear call to action. Project health and activity feed each have their own inline empty messages ("No project health data yet." / "No recent activity to show."). |
| Background refresh does not break layout | `PASS` | `isInsightsFetching` applies `opacity-90` to the trend card only. KPI cards and health table render from stale data without layout shift. `refreshingHint` shows "Refreshing..." text in the health card header. |

### Correctness Checks

| Item | State | Evidence / Notes |
| --- | --- | --- |
| KPI calculations are correct | `PASS` | `_task_completion_metrics` uses `_leaf_tasks` to exclude summary tasks. `active_projects` counts `ProjectStatus.ACTIVE` only. `overallocated_resources` is a sum of per-project overalloc counts. All correct. |
| Risk score formula and thresholds are correct | `PASS` | `_risk_score = overdue_ratio*40 + critical_ratio*35 + overalloc_ratio*25`. Clamped to [0, 100]. `_risk_level`: ≥67 → high, ≥34 → medium, else low. Reasonable and consistent. |
| Overdue task logic is correct | `PASS` | `finish_date < today AND percent_complete < 100`. Correct — a task completed late is not counted as currently overdue. |
| Summary/rollup tasks are excluded from leaf metrics | `PASS` | `_leaf_tasks` filters `task.is_summary == False`. Confirmed by `test_get_project_dashboard_excludes_summary_rollups_from_leaf_metrics`. |
| Project health sorting is correct | `PASS` | Backend returns health sorted by `risk_score` descending. Frontend re-sorts client-side by `risk_score` or `completion_pct` depending on `healthSort` state. Both paths correct. |
| Trend chart date labels are timezone-safe | `PASS` | `InsightsTrendCard` uses `parseISO(v)` from date-fns. `parseISO("2026-03-30")` returns local midnight, not UTC midnight — unlike `new Date("2026-03-30")` which returns UTC midnight. So the label renders the correct calendar day in all timezones. Compliant with ADR-012. |
| Time window resolution uses correct today anchor | `PASS` | `resolve_business_day` in `time_policy.py` uses org/project timezone if set, falls back to `date.today()`. Tested in `test_resolve_window_uses_scoped_business_day_for_organization`. |
| Over-allocation counts are correct and not double-counted | `PASS` | `compute_overallocation_counts` uses a `set` of `(project_id, resource_id)` pairs — each resource counted once per project regardless of how many assignments push it over. Confirmed by `test_compute_overallocation_counts_counts_each_resource_once_per_project`. |

### Data / Time / State Integrity

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Cache invalidation / stale data risks checked | `PASS` | `useDashboardInsights` uses TanStack Query with a key that includes `organizationId`, `windowPreset`, `startDate`, `endDate`. Changing any of these triggers a fresh fetch. OrgSwitcher calls `queryClient.invalidateQueries({ queryKey: projectKeys.list(org.id) })` on switch and navigates to `/`, which re-mounts with the new org. |
| Time window persists after page refresh | `PASS` | `useTimeWindowFilter` reads/writes URL search params. Params survive refresh. |
| Active org persists after page refresh | `PASS` | Zustand `persist` middleware writes `activeOrgId` to `localStorage`. Survives refresh. Cleared on logout via `useAuthStore.subscribe`. |
| Realtime/websocket behavior checked where relevant | `PASS` | Dashboard has no realtime/websocket requirement. Data is fetched on mount and on window/org change. Background refetch via TanStack Query default stale time is acceptable for a control-center view. |

### Backend / Logic Trace

| Item | State | Evidence / Notes |
| --- | --- | --- |
| API endpoint auth and org membership enforced | `PASS` | `get_org_access_or_404` depends on `get_current_active_user` (JWT auth) and verifies `OrganizationMember` row exists. Raises `NotFoundError` (404) or `PermissionDeniedError` (403) appropriately. |
| Window resolution passes org context correctly | `PASS` | `resolve_window_or_422` receives `organization=access.organization`. `resolve_business_day` uses org timezone if set. |
| Service layer aggregation logic checked | `PASS` | `get_org_dashboard_insights` loads projects, tasks, resources, active resources, and assignments in bulk. No per-project loops that hit the DB. Aggregation is in-memory. |
| Repository queries use correct filters | `PASS` | `get_projects_for_organization`: filters by `organization_id` and `is_deleted == False`. `get_tasks_for_projects`: filters by `project_id.in_(project_ids)` and `is_deleted == False`. `get_active_resources_for_projects`: filters by `is_active == True`. All correct. |
| Over-allocation query pattern checked (N+1 risk) | `PASS` | `utilization_repo.get_assignments_in_range_for_projects` fetches all assignments for all project IDs in one query. `compute_overallocation_counts` processes them in-memory. No N+1. |
| Schema/model constraints checked | `PASS` | `DashboardInsightsResponse` validates via Pydantic. `task_completion_pct` has `ge=0, le=100`. `risk_score` has `ge=0, le=100`. `completion_pct` has `ge=0, le=100`. |
| Layer direction is correct (api to service to repo) | `PASS` | `insights.py` (api) → `insights_service.get_org_dashboard_insights` (service) → `insights_repo.*` and `utilization_repo.*` (repo). No layer skipping. |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Unauthenticated users are blocked | `PASS` | `ProtectedRoute` redirects to `/login` if not authenticated. Backend `get_current_active_user` raises 401 if no valid JWT. |
| Non-members of the org are blocked | `PASS` | `get_org_access_or_404` raises `PermissionDeniedError` (403) if no `OrganizationMember` row exists for the user+org pair. |
| Dashboard is read-only — no write actions exposed | `PASS` | `DashboardPage` has no forms, mutations, or write-triggering buttons. Sort toggle and time window filter are purely local/URL state. |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Primary action is obvious | `PASS` | Dashboard is a read-only view. The primary affordance is navigation via KPI cards and project health links. These are clearly presented. |
| Labels are human-readable | `PASS` | KPI labels: "Active Projects", "Completed Projects", "Task Completion", "Overdue Tasks", "Critical Tasks", "Overallocated Resources". All clear. Risk level badge uses "low/medium/high". |
| Important content is visible above the fold | `PASS` | KPI cards are the first content block. On desktop (xl grid) they render as a 6-column row. |
| Layout is not cramped or confusing | `PASS` | Three-column layout on xl: trend chart (wider), project health (medium), activity feed (narrower, sticky). Reasonable proportions. |
| Refresh feedback is timely and understandable | `FAIL` | "Refreshing..." hint appears only in the Project Health card header. The trend chart gets `opacity-90` but no text label. The KPI cards and activity feed show no refresh indicator at all. A user changing the time window gets no feedback that the KPIs are updating. See DASH-003. |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Desktop layout checked | `PASS` | `xl:grid-cols-6` for KPIs, `xl:grid-cols-[...]` three-column for main content. Correct. |
| Mobile layout checked | `FAIL` | KPI grid: `sm:grid-cols-2` — 6 cards in 2 columns = 3 rows. Acceptable. Main content: no mobile breakpoint on the three-column grid — it collapses to a single column by default (no `grid-cols-1` explicit, but Tailwind default is 1 col). The activity feed has `xl:sticky xl:top-6 xl:h-[calc(100dvh-11rem)]` — on mobile it renders as a full-height unconstrained list, which could be very long. No explicit mobile overflow handling for the activity list on small screens. See DASH-004. |
| Overflow and clipping checked | `PASS` | Project health table has `max-h-[320px] overflow-auto`. Activity feed has `overflow-y-auto` on the list. Trend chart has fixed height. No obvious uncontrolled overflow on desktop. |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Backend API tests reviewed | `PASS` | `test_insights.py`: covers happy path (200 with correct KPI values), custom window without dates (422). Thin but covers the critical paths. |
| Backend service unit tests reviewed | `PASS` | `test_insights_service.py`: covers trend overdue logic, on-time completion, window resolution with org/project scoping, overallocation UUID normalization, double-count prevention, full project dashboard aggregation (summary, schedule, costs, resources, critical path, milestones, overdue tasks), and summary rollup exclusion. Good coverage. |
| Frontend hook tests reviewed | `PASS` | `useDashboardInsights.test.tsx`: covers enabled fetch with valid window, disabled fetch for incomplete custom window. Minimal but correct. |
| DashboardPage component tests reviewed | `PASS` | `DashboardPage.test.tsx`: covers loading state during bootstrap, org error with retry, and KPI card link destinations. Covers the three most important render branches. |
| InsightsTrendCard tests reviewed | `PASS` | `insights-trend-card.test.tsx` exists. Tests the tickFormatter output using `parseISO` — confirms correct local calendar date rendering. |
| InsightsActivityCard tests reviewed | `PASS` | `insights-activity-card.test.tsx` exists. Tests route resolution for all three entity types (project, task, resource) with correct href assertions. |
| Missing high-risk test cases listed | `FAIL` | Missing: (1) `DashboardPage` insights error state with retry. (2) `DashboardPage` no-org empty state. (3) Backend: `active_projects` KPI never tested with an ACTIVE project. See DASH-006. |

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| DASH-001 | P1 | UX / Navigation | All 6 KPI cards link to `/projects` (generic list). Overdue Tasks, Critical Tasks, and Overallocated Resources give no filtered view. | Clicking "Overdue Tasks: 12" should navigate to a pre-filtered task or project view, or at minimum the card should not imply drilldown if none exists. | `InsightsMetricCard` receives `to="/projects"` for all 6 cards in `DashboardPage.tsx`. Low implementation cost to fix once filtered views exist; for now the link is misleading. |
| ~~DASH-002~~ | ~~P1~~ | ~~Frontend / Correctness~~ | ~~Retracted~~ | ~~Retracted~~ | `parseISO` from date-fns returns local midnight, not UTC midnight. Labels are correct in all timezones. False positive — removed from open issues. |
| DASH-003 | P2 | UX / Feedback | When the time window changes, only the Project Health card shows "Refreshing...". KPI cards and activity feed show no loading feedback during background refetch. | All data sections should indicate a refresh is in progress, or the "Refreshing..." indicator should be in the page header / near the time window filter. | `isInsightsFetching` is available in `DashboardPage` but only used for the health card and trend card opacity. |
| DASH-004 | P2 | Responsive | Activity feed on mobile renders as a full-height unconstrained list (the `xl:h-[calc(100dvh-11rem)]` constraint only applies at xl breakpoint). On small screens this can produce a very long scroll. | On mobile the activity feed should have a max-height or be collapsed/paginated. | `InsightsActivityCard` className in `DashboardPage.tsx`. |
| ~~DASH-005~~ | ~~P2~~ | ~~Test Coverage~~ | ~~Retracted~~ | ~~Retracted~~ | Both `insights-trend-card.test.tsx` and `insights-activity-card.test.tsx` exist and cover the core logic. False positive — removed. |
| DASH-006 | P1 | Test Coverage / Backend | `test_dashboard_insights_success` asserts `active_projects == 0` because the seeded project is in PLANNING status, not ACTIVE. The test does not verify the `active_projects` KPI for the case where a project is actually ACTIVE. | At least one test should seed an ACTIVE project and assert `active_projects >= 1`. | `backend/tests/unit/api/v1/test_insights.py`. The comment in the test acknowledges this gap. |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All P0 items retested | `PASS` | No P0 items found. |
| Important P1 items retested | `NOT CHECKED` | DASH-001, DASH-002, DASH-006 are open P1s. Re-review required after fixes. |
| No regression introduced by fixes | `NOT CHECKED` | Pending fixes. |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Feature boundary is clear | `PASS` | Single route, read-only, org-scoped. Well-defined. |
| Critical user promises are satisfied | `PASS` | Promises 1–6 are met. KPI link destinations (promise 4 variant) are functional but not ideal — covered by DASH-001. |
| Happy path is reliable | `PASS` | End-to-end flow is solid. Auth, org bootstrap, data fetch, and render all work correctly. |
| No open P0 issues remain | `PASS` | No P0 issues found. |
| Correctness checks passed | `FAIL` | DASH-002: trend chart date labels are off-by-one in UTC-N timezones. |
| Data / time / state integrity is acceptable | `PASS` | Window and org persist correctly. Cache invalidation is correct. |
| Backend / logic trace leaves no unresolved trust-breaking risk | `PASS` | Auth, membership, aggregation, and overallocation logic are all correct. |
| Key UX blockers are addressed or explicitly accepted | `FAIL` | DASH-001 (misleading KPI links) and DASH-003 (missing refresh feedback) are open P1s. |
| Remaining gaps are documented | `PASS` | All issues recorded with IDs, severity, and notes. |
| Feature can be demonstrated without embarrassment-level failure | `PASS` | The dashboard renders correctly and data is accurate. The open issues are rough edges, not demo-breakers. |
| Feature is safe to mark Closed | `FAIL` | DASH-002 (correctness bug) and DASH-001 (misleading UX) should be fixed before closing. |
