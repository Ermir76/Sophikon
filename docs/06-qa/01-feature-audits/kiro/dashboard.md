# Dashboard

Status:
Owner: `Kiro`
Severity summary: `P0: 0 | P1: 0 | P2: 0`

## Audit File

`docs/06-qa/01-feature-audits/kiro/dashboard.md`

## Feature Boundary

The global dashboard at `/` is the post-login landing page for an authenticated user with an active organization. It renders org-level KPI cards, an execution trend chart, a project health table, and a recent activity feed. Time window is controlled via URL search params (`dash_window`, `dash_start`, `dash_end`). Excluded: project-level dashboards under `/projects/:projectId`, org management, and the AI panel.

---

## Issues Found

| ID | Severity | Area | Problem | Expected | Evidence |
| --- | --- | --- | --- | --- | --- |

---

## Review Matrix

### Feature Boundary

| Item | State | Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `NOT CHECKED` | Route `/` → `DashboardPage` in `App.tsx`. Boundary is clear. |
| Out-of-scope adjacent behavior is defined | `NOT CHECKED` | Project-level dashboards are separate routes. |
| Feature start point is clear | `NOT CHECKED` | Post-login redirect to `/`. |
| Feature end point is clear | `NOT CHECKED` | Navigation to projects or settings via cards/sidebar. |

### Entry Points

| Item | State | Notes |
| --- | --- | --- |
| All routes and entry points listed | `NOT CHECKED` | `/` via `ProtectedRoute` → `AppLayout` → `DashboardPage`. Sidebar nav also links here. |
| App landing page after login | `NOT CHECKED` | KIRO-DASH-001: bootstrap race can show empty state instead of loading. |

### Happy Path

| Item | State | Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `NOT CHECKED` | With a valid `activeOrgId` and data, all widgets render correctly. |
| Success state is clear | `NOT CHECKED` | KPI cards, trend chart, health table, and activity feed all render. |
| Navigation links from dashboard land correctly | `NOT CHECKED` | KIRO-DASH-002: KPI drill-down links all point to the highest-risk project regardless of metric. |
| Refresh preserves correct state | `NOT CHECKED` | Time window stored in URL params via `useTimeWindowFilter`. Survives refresh. |

### Validation and Failure Paths

| Item | State | Notes |
| --- | --- | --- |
| API error state | `NOT CHECKED` | `isInsightsError` renders `QueryError` with retry. |
| Custom window without dates | `NOT CHECKED` | `isCustomInvalid` guard shows inline error. Backend also returns 422. |
| Empty / no-data state | `NOT CHECKED` | KIRO-DASH-001: genuine empty state and bootstrap gap are not distinguished. |
| Partial / delayed data | `NOT CHECKED` | `isFetching` opacity hint + "Refreshing..." text covers background refetch. |

### Empty, Loading, and Refresh States

| Item | State | Notes |
| --- | --- | --- |
| Page loader is shown during initial fetch | `NOT CHECKED` | `PageLoading` shown when `isOrgLoading \|\| (isInsightsLoading && !!activeOrgId && !insights)`. |
| Empty state is intentional and helpful | `NOT CHECKED` | KIRO-DASH-001: "Please select or create an organization" can appear spuriously during bootstrap. |
| Widget loading placeholders | `NOT CHECKED` | No skeleton placeholders for individual widgets; full-page loader only. |

### Permissions and Roles

| Item | State | Notes |
| --- | --- | --- |
| Auth required | `NOT CHECKED` | `ProtectedRoute` wraps the route. Unauthenticated users are redirected to `/login`. |
| Org membership enforced | `NOT CHECKED` | `get_org_access_or_404` checks `OrganizationMember` row; raises `PermissionDeniedError` if absent. |
| Role-sensitive content | `NOT CHECKED` | Dashboard is read-only for all org members. No role-gated actions present. |

### Correctness Checks

| Item | State | Notes |
| --- | --- | --- |
| Trend chart date labels | `NOT CHECKED` | KIRO-DASH-003: `new Date("YYYY-MM-DD")` parses as UTC midnight; negative-offset timezones render the previous day. |
| KPI calculations | `NOT CHECKED` | `_task_completion_metrics` and `_risk_score` logic is correct and covered by service tests. |
| Project health sorting | `NOT CHECKED` | Backend sorts by `risk_score` descending; frontend re-sorts locally by risk or completion. Both are correct. |
| Risk level thresholds | `NOT CHECKED` | `_risk_level`: ≥67 → high, ≥34 → medium, else low. Consistent with badge rendering. |
| Overdue logic | `NOT CHECKED` | `finish_date < today && percent_complete < 100`. Correct. Covered by unit tests. |
| Summary task exclusion | `NOT CHECKED` | `_leaf_tasks` filters `is_summary=True` before all metric calculations. Covered by nested-task test. |
| Window resolution | `NOT CHECKED` | `resolve_window` handles all presets and custom range. 422 on invalid custom. Covered by API test. |
| `date.today()` server timezone | `NOT CHECKED` | KIRO-DASH-006: fragile if server is not UTC. Low current risk. |

### Backend / Logic Trace

| Item | State | Notes |
| --- | --- | --- |
| API endpoint | `NOT CHECKED` | `GET /organizations/{org_id}/insights/dashboard` — correct auth, correct response model. |
| Auth chain | `NOT CHECKED` | `get_current_active_user` → `get_org_access_or_404` → membership check. Domain exceptions only, no raw `HTTPException`. |
| Service layer | `NOT CHECKED` | `get_org_dashboard_insights` — correct aggregation, correct layer direction. |
| Repository layer | `NOT CHECKED` | `insights_repo` uses `select()` style, `is_deleted` filters applied. |
| Schema / model constraints | `NOT CHECKED` | `DashboardInsightsResponse` validates all fields. `Field(ge=0, le=100)` on percentages and scores. |
| N+1 in overallocation loop | `NOT CHECKED` | KIRO-DASH-005: 2N DB queries per dashboard load. Acknowledged in code but unresolved. |

### Data / Time / State Integrity

| Item | State | Notes |
| --- | --- | --- |
| Cache invalidation / stale data | `NOT CHECKED` | `dashboardInsightsKeys.detail` includes org ID and all window params. No stale-data risk between filter changes. |
| Persistence after refresh | `NOT CHECKED` | URL search params preserve window selection. |
| Realtime / WebSocket | `NOT CHECKED` | Global dashboard has no WebSocket subscription. Project-level views do. This is a product gap, not a correctness bug. Acceptable for current scope. |

### UX and Visual Review

| Item | State | Notes |
| --- | --- | --- |
| Primary action is obvious | `NOT CHECKED` | Dashboard intent as overview is clear. |
| Labels are human-readable | `NOT CHECKED` | KPI labels and chart legends are clear. |
| Important content is visible | `NOT CHECKED` | KPI grid at top, trend and health below. |
| Activity feed is navigable | `NOT CHECKED` | KIRO-DASH-004: items are not clickable. Contradicts "navigation hub" promise. |
| Refresh indicator | `NOT CHECKED` | "Refreshing..." text with opacity-90 is minimal but functional. |
| First impression for demo | `NOT CHECKED` | KIRO-DASH-001 can show empty state on first load; KIRO-DASH-004 leaves activity feed as a dead end. |

### Responsive Review

| Item | State | Notes |
| --- | --- | --- |
| Desktop | `NOT CHECKED` | Grid layout scales correctly. |
| Mobile | `NOT CHECKED` | Not verified in this audit pass. |
| Card stacking and spacing | `NOT CHECKED` | `sm:grid-cols-2 xl:grid-cols-6` responsive grid is correct. |

### Test Coverage

| Item | State | Notes |
| --- | --- | --- |
| Backend API tests | `NOT CHECKED` | `test_insights.py`: 2 tests — happy path KPIs and custom-window 422. Pass. |
| Backend service tests | `NOT CHECKED` | `test_insights_service.py`: 6 tests — trend logic, project dashboard aggregation, nested task exclusion, critical path, costs, resources. Pass. |
| Frontend hook tests | `NOT CHECKED` | `useDashboardInsights.test.tsx`: 2 tests — fetch enabled/disabled. Pass. |
| `DashboardPage` component tests | `NOT CHECKED` | No page-level tests. Bootstrap race (KIRO-DASH-001), KPI link correctness (KIRO-DASH-002), and timezone rendering (KIRO-DASH-003) are all unprotected by automation. |
| `InsightsActivityCard` tests | `NOT CHECKED` | No tests. Clickability behavior (KIRO-DASH-004) is unprotected. |
| `InsightsTrendCard` tests | `NOT CHECKED` | No tests. Timezone tick formatter (KIRO-DASH-003) is unprotected. |

---

## Closure Gate

| Item | State | Notes |
| --- | --- | --- |
| Feature boundary is clear | `NOT CHECKED` | |
| Critical user promises are verified | `NOT CHECKED` | Navigation hub promise broken by non-clickable activity feed. |
| Happy path is reliable | `NOT CHECKED` | Works correctly when org is already resolved. |
| No open P0 issues remain | `NOT CHECKED` | |
| Correctness checks passed | `NOT CHECKED` | Trend chart timezone shift (KIRO-DASH-003). |
| Backend / logic trace leaves no unresolved trust-breaking risk | `NOT CHECKED` | N+1 is a perf concern, not a trust-breaking correctness issue. |
| Refresh / persistence / realtime behavior acceptable | `NOT CHECKED` | URL-param persistence works. No realtime requirement at this scope. |
| Role checks correct | `NOT CHECKED` | |
| Test gaps listed | `NOT CHECKED` | See Test Coverage section. |
| Re-review passed after fixes | `NOT CHECKED` | Fixes not yet applied. |
| Feature is safe to mark Closed | `NOT CHECKED` | **Audit Failed.** Four P1 issues remain open. |

---

## Summary

Current status: `Failed Audit`
Open issues: `P0: 0 | P1: 4 | P2: 2`
