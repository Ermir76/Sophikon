# Dashboard

Status: `Failed Audit`
Owner: `Kiro`
Severity summary: `P0: 0 | P1: 4 | P2: 2`

## Audit File

`docs/06-qa/01-feature-audits/kiro/dashboard.md`

## Feature Boundary

The global dashboard at `/` is the post-login landing page for an authenticated user with an active organization. It renders org-level KPI cards, an execution trend chart, a project health table, and a recent activity feed. Time window is controlled via URL search params (`dash_window`, `dash_start`, `dash_end`). Excluded: project-level dashboards under `/projects/:projectId`, org management, and the AI panel.

---

## Issues Found

| ID | Severity | Area | Problem | Expected | Evidence |
| --- | --- | --- | --- | --- | --- |
| KIRO-DASH-001 | P1 | Bootstrap / landing state | On first load after login, `activeOrgId` is `null` in Zustand (not yet hydrated from `localStorage` or not yet auto-selected). `useOrganization(null)` fires with `enabled: false`, so `isOrgLoading` is immediately `false`. The page falls through to the `!activeOrganization` branch and renders the "Please select or create an organization" empty state before `OrgSwitcher`'s `useEffect` has had a chance to call `setActiveOrg`. The empty state and the loading state are indistinguishable to the user. | The post-login landing page must distinguish a genuine no-org state from a bootstrap-in-progress state. A brief loading indicator should cover the window between mount and org resolution. | `DashboardPage.tsx` lines 50-65: loading guard only covers `isOrgLoading \|\| (isInsightsLoading && !!activeOrgId && !insights)`. `OrgSwitcher.tsx`: auto-select fires in a `useEffect` after render. `org-store.ts`: `persist` middleware hydrates synchronously from `localStorage` in most browsers, but the `useOrganizations` list fetch is async — if `activeOrgId` is null (new user, cleared storage, or first login), the gap is real. |
| KIRO-DASH-002 | P1 | KPI card navigation | `firstProjectId` is captured from `data?.project_health?.[0]?.project_id` — the first item in the backend-sorted (risk-score descending) list, before any local re-sort. Four KPI cards ("Task Completion", "Overdue Tasks", "Critical Tasks", "Overallocated Resources") all link to this single project. A user clicking "Task Completion" expects to land on the project driving that metric, not the highest-risk project. The link is misleading for every org with more than one project. | Each KPI card should either link to a filtered list view (e.g. `/projects?sort=completion`) or omit the drill-down rather than silently navigate to an unrelated project. | `DashboardPage.tsx` lines 88-90 and KPI card `to` props. `insights_service.py` `get_org_dashboard_insights` returns `project_health` sorted by `risk_score` descending before the frontend receives it. |
| KIRO-DASH-003 | P1 | Trend chart timezone | `tickFormatter` in `InsightsTrendCard` calls `new Date(v).toLocaleDateString(...)` on a plain `YYYY-MM-DD` string. `new Date("2026-04-02")` parses as `2026-04-02T00:00:00Z`. In any UTC-negative timezone (all US timezones, most of the Americas) this renders as the previous calendar day. A 30-day chart in `America/Los_Angeles` (UTC-7) shifts every label one day back. | Parse date-only strings without timezone coercion: `new Date(v + "T00:00:00")` or split the string manually. The backend `TrendPoint.date` is a `date` (no time component) and should be displayed as-is. | `insights-trend-card.tsx` `tickFormatter`. `insights.py` `TrendPoint` schema — `date` field, no timezone. Reproducible: `new Date("2026-04-02").toLocaleDateString("en-US", {timeZone: "America/Los_Angeles"})` → `"4/1/2026"`. |
| KIRO-DASH-004 | P1 | Recent Activity — no navigation | `InsightsActivityCard` renders each activity item as a plain `<li>` with no link or click handler. The backend returns `entity_type`, `entity_id`, and `project_id` on every item — enough to build a correct route for projects (`/projects/:id`), tasks (`/projects/:project_id/tasks`), and resources (`/projects/:project_id/resources`). The dashboard is described as a "navigation hub" in the feature boundary; a static activity feed contradicts that promise. | Activity items should be clickable and navigate to the relevant entity. | `insights-activity-card.tsx`: `<li>` has no `<Link>` or `onClick`. `insights.ts` `RecentActivityItem` type includes `entity_type`, `entity_id`, `project_id`. |
| KIRO-DASH-005 | P2 | N+1 query in project health loop | `get_org_dashboard_insights` calls `_project_overallocation_stats` once per project inside a `for` loop. Each call fires two async DB queries (`detect_over_allocations` + `get_active_resources_for_project`). For an org with N projects this is 2N extra round-trips on every dashboard load. The code has a comment acknowledging this. It is not a correctness bug but will degrade noticeably at scale. | Batch resource and assignment lookups with `project_id IN (...)` and compute over-allocation in a single pass. | `insights_service.py` `get_org_dashboard_insights` loop + `_project_overallocation_stats`. Comment: "Known perf tradeoff. N+1 pattern." |
| KIRO-DASH-006 | P2 | `date.today()` server-side timezone | `resolve_window` and `get_org_dashboard_insights` both call `date.today()` which returns the server's local date. If the server runs in UTC (standard Docker/cloud) this is consistent. If the server is ever deployed in a non-UTC timezone, "today" drifts relative to users. Low risk in practice but fragile. | Use `datetime.now(timezone.utc).date()` as the UTC anchor throughout. | `insights_service.py` `resolve_window` and `get_org_dashboard_insights`. |

---

## Review Matrix

### Feature Boundary

| Item | State | Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `PASS` | Route `/` → `DashboardPage` in `App.tsx`. Boundary is clear. |
| Out-of-scope adjacent behavior is defined | `PASS` | Project-level dashboards are separate routes. |
| Feature start point is clear | `PASS` | Post-login redirect to `/`. |
| Feature end point is clear | `PASS` | Navigation to projects or settings via cards/sidebar. |

### Entry Points

| Item | State | Notes |
| --- | --- | --- |
| All routes and entry points listed | `PASS` | `/` via `ProtectedRoute` → `AppLayout` → `DashboardPage`. Sidebar nav also links here. |
| App landing page after login | `FAIL` | KIRO-DASH-001: bootstrap race can show empty state instead of loading. |

### Happy Path

| Item | State | Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `PASS` | With a valid `activeOrgId` and data, all widgets render correctly. |
| Success state is clear | `PASS` | KPI cards, trend chart, health table, and activity feed all render. |
| Navigation links from dashboard land correctly | `FAIL` | KIRO-DASH-002: KPI drill-down links all point to the highest-risk project regardless of metric. |
| Refresh preserves correct state | `PASS` | Time window stored in URL params via `useTimeWindowFilter`. Survives refresh. |

### Validation and Failure Paths

| Item | State | Notes |
| --- | --- | --- |
| API error state | `PASS` | `isInsightsError` renders `QueryError` with retry. |
| Custom window without dates | `PASS` | `isCustomInvalid` guard shows inline error. Backend also returns 422. |
| Empty / no-data state | `FAIL` | KIRO-DASH-001: genuine empty state and bootstrap gap are not distinguished. |
| Partial / delayed data | `PASS` | `isFetching` opacity hint + "Refreshing..." text covers background refetch. |

### Empty, Loading, and Refresh States

| Item | State | Notes |
| --- | --- | --- |
| Page loader is shown during initial fetch | `PASS` | `PageLoading` shown when `isOrgLoading \|\| (isInsightsLoading && !!activeOrgId && !insights)`. |
| Empty state is intentional and helpful | `FAIL` | KIRO-DASH-001: "Please select or create an organization" can appear spuriously during bootstrap. |
| Widget loading placeholders | `NOT CHECKED` | No skeleton placeholders for individual widgets; full-page loader only. |

### Permissions and Roles

| Item | State | Notes |
| --- | --- | --- |
| Auth required | `PASS` | `ProtectedRoute` wraps the route. Unauthenticated users are redirected to `/login`. |
| Org membership enforced | `PASS` | `get_org_access_or_404` checks `OrganizationMember` row; raises `PermissionDeniedError` if absent. |
| Role-sensitive content | `PASS` | Dashboard is read-only for all org members. No role-gated actions present. |

### Correctness Checks

| Item | State | Notes |
| --- | --- | --- |
| Trend chart date labels | `FAIL` | KIRO-DASH-003: `new Date("YYYY-MM-DD")` parses as UTC midnight; negative-offset timezones render the previous day. |
| KPI calculations | `PASS` | `_task_completion_metrics` and `_risk_score` logic is correct and covered by service tests. |
| Project health sorting | `PASS` | Backend sorts by `risk_score` descending; frontend re-sorts locally by risk or completion. Both are correct. |
| Risk level thresholds | `PASS` | `_risk_level`: ≥67 → high, ≥34 → medium, else low. Consistent with badge rendering. |
| Overdue logic | `PASS` | `finish_date < today && percent_complete < 100`. Correct. Covered by unit tests. |
| Summary task exclusion | `PASS` | `_leaf_tasks` filters `is_summary=True` before all metric calculations. Covered by nested-task test. |
| Window resolution | `PASS` | `resolve_window` handles all presets and custom range. 422 on invalid custom. Covered by API test. |
| `date.today()` server timezone | `FAIL` | KIRO-DASH-006: fragile if server is not UTC. Low current risk. |

### Backend / Logic Trace

| Item | State | Notes |
| --- | --- | --- |
| API endpoint | `PASS` | `GET /organizations/{org_id}/insights/dashboard` — correct auth, correct response model. |
| Auth chain | `PASS` | `get_current_active_user` → `get_org_access_or_404` → membership check. Domain exceptions only, no raw `HTTPException`. |
| Service layer | `PASS` | `get_org_dashboard_insights` — correct aggregation, correct layer direction. |
| Repository layer | `PASS` | `insights_repo` uses `select()` style, `is_deleted` filters applied. |
| Schema / model constraints | `PASS` | `DashboardInsightsResponse` validates all fields. `Field(ge=0, le=100)` on percentages and scores. |
| N+1 in overallocation loop | `FAIL` | KIRO-DASH-005: 2N DB queries per dashboard load. Acknowledged in code but unresolved. |

### Data / Time / State Integrity

| Item | State | Notes |
| --- | --- | --- |
| Cache invalidation / stale data | `PASS` | `dashboardInsightsKeys.detail` includes org ID and all window params. No stale-data risk between filter changes. |
| Persistence after refresh | `PASS` | URL search params preserve window selection. |
| Realtime / WebSocket | `NOT CHECKED` | Global dashboard has no WebSocket subscription. Project-level views do. This is a product gap, not a correctness bug. Acceptable for current scope. |

### UX and Visual Review

| Item | State | Notes |
| --- | --- | --- |
| Primary action is obvious | `PASS` | Dashboard intent as overview is clear. |
| Labels are human-readable | `PASS` | KPI labels and chart legends are clear. |
| Important content is visible | `PASS` | KPI grid at top, trend and health below. |
| Activity feed is navigable | `FAIL` | KIRO-DASH-004: items are not clickable. Contradicts "navigation hub" promise. |
| Refresh indicator | `PASS` | "Refreshing..." text with opacity-90 is minimal but functional. |
| First impression for demo | `FAIL` | KIRO-DASH-001 can show empty state on first load; KIRO-DASH-004 leaves activity feed as a dead end. |

### Responsive Review

| Item | State | Notes |
| --- | --- | --- |
| Desktop | `PASS` | Grid layout scales correctly. |
| Mobile | `NOT CHECKED` | Not verified in this audit pass. |
| Card stacking and spacing | `PASS` | `sm:grid-cols-2 xl:grid-cols-6` responsive grid is correct. |

### Test Coverage

| Item | State | Notes |
| --- | --- | --- |
| Backend API tests | `PASS` | `test_insights.py`: 2 tests — happy path KPIs and custom-window 422. Pass. |
| Backend service tests | `PASS` | `test_insights_service.py`: 6 tests — trend logic, project dashboard aggregation, nested task exclusion, critical path, costs, resources. Pass. |
| Frontend hook tests | `PASS` | `useDashboardInsights.test.tsx`: 2 tests — fetch enabled/disabled. Pass. |
| `DashboardPage` component tests | `FAIL` | No page-level tests. Bootstrap race (KIRO-DASH-001), KPI link correctness (KIRO-DASH-002), and timezone rendering (KIRO-DASH-003) are all unprotected by automation. |
| `InsightsActivityCard` tests | `FAIL` | No tests. Clickability behavior (KIRO-DASH-004) is unprotected. |
| `InsightsTrendCard` tests | `FAIL` | No tests. Timezone tick formatter (KIRO-DASH-003) is unprotected. |

---

## Closure Gate

| Item | State | Notes |
| --- | --- | --- |
| Feature boundary is clear | `PASS` | |
| Critical user promises are verified | `FAIL` | Navigation hub promise broken by non-clickable activity feed. |
| Happy path is reliable | `PASS` | Works correctly when org is already resolved. |
| No open P0 issues remain | `PASS` | |
| Correctness checks passed | `FAIL` | Trend chart timezone shift (KIRO-DASH-003). |
| Backend / logic trace leaves no unresolved trust-breaking risk | `PASS` | N+1 is a perf concern, not a trust-breaking correctness issue. |
| Refresh / persistence / realtime behavior acceptable | `PASS` | URL-param persistence works. No realtime requirement at this scope. |
| Role checks correct | `PASS` | |
| Test gaps listed | `PASS` | See Test Coverage section. |
| Re-review passed after fixes | `NOT CHECKED` | Fixes not yet applied. |
| Feature is safe to mark Closed | `FAIL` | **Audit Failed.** Four P1 issues remain open. |

---

## Summary

Current status: `Failed Audit`
Open issues: `P0: 0 | P1: 4 | P2: 2`

Recommended fix order:
1. KIRO-DASH-001 — bootstrap loading guard (small, high impact on first impression)
2. KIRO-DASH-003 — timezone-safe date parsing in trend chart (one-liner fix)
3. KIRO-DASH-004 — clickable activity items (moderate effort, fulfills navigation hub promise)
4. KIRO-DASH-002 — KPI card link correctness (requires product decision on target route)
5. KIRO-DASH-005 — N+1 batch refactor (backend, defer until scale warrants it)
6. KIRO-DASH-006 — UTC anchor for `date.today()` (low risk, easy cleanup)
