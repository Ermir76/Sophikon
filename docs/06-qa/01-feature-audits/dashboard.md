# Dashboard

Status: `Failed Audit`
Owner: `wwwer`
Severity summary: `P0: 0 | P1: 3 | P2: 0`

## Scope

- `PASS` Global dashboard `/`
- `PASS` Summary cards, widgets, and navigation shortcuts
- `FAIL` Empty dashboard state

## Entry Points

- `FAIL` App landing page after login
- `PASS` Sidebar navigation to dashboard
- `NOT CHECKED` Logo/home navigation if present

## Happy Path

- `PASS` Dashboard loads without crash
- `PASS` Key stats/widgets render correctly
- `FAIL` Navigation links from dashboard land in correct place
- `PASS` Refresh preserves correct state

## Validation And Failure Paths

- `PASS` API error state checked
- `PASS` Empty/no-data state checked
- `FAIL` Partial data or delayed data does not break layout

## Empty, Loading, And Refresh States

- `PASS` Page loader is acceptable
- `FAIL` Empty state is intentional and helpful
- `NOT CHECKED` Widget loading placeholders do not feel broken

## Permissions And Roles

- `PASS` Role-sensitive content checked if applicable

## UX And Visual Review

- `FAIL` First impression is strong enough for demo use
- `PASS` Most important information is visually obvious
- `PASS` Cards/sections do not feel cluttered
- `PASS` Copy is human-readable

## Responsive Review

- `PASS` Desktop checked
- `NOT CHECKED` Mobile checked
- `PASS` Card stacking and spacing checked

## Test Coverage

- `PASS` Dashboard test coverage reviewed
- `PASS` Missing high-risk tests listed

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| DASH-001 | P1 | Landing / bootstrap state | The dashboard treats a missing active organization object as a true empty state immediately, even though org selection is populated asynchronously in the sidebar. On first load after login, or when org bootstrap is still warming up, users can see “Please select or create an organization” instead of a loading state. | The post-login landing page should distinguish loading/bootstrap from a genuine no-organization empty state. | Verified in `frontend/src/features/dashboard/pages/DashboardPage.tsx` and `frontend/src/features/organizations/components/OrgSwitcher.tsx`. This conflicts with the UX standard that every data view must handle loading, empty, error, and success states explicitly. |
| DASH-002 | P1 | Navigation shortcuts | Four KPI cards drill into `firstProjectId`, which is simply the first project in the risk-sorted `project_health` list. That means task/completion/resource shortcuts can send users to the wrong project instead of the one responsible for the metric. | Dashboard shortcut links should land on the correct destination for the metric the user clicked. | Verified in `frontend/src/features/dashboard/pages/DashboardPage.tsx` and backend risk ordering in `backend/app/service/insights_service.py`. |
| DASH-003 | P1 | Timezone correctness | The trend chart parses plain `YYYY-MM-DD` strings with `new Date(v).toLocaleDateString(...)`, which shifts dates backward in negative UTC offsets. Example: `2026-04-02` renders as `Apr 1` in `America/Los_Angeles`. | Trend labels should display the exact API day consistently across user timezones. | Verified in `frontend/src/shared/ui/insights-trend-card.tsx` with a concrete Node repro for a US timezone. |

## Re-Review

- `NOT CHECKED` Critical dashboard paths retested

## Exit Criteria

- `FAIL` Dashboard is safe as a post-login landing page
- `PASS` No open `P0` issues remain
- `PASS` Main value proposition is visible quickly

## Audit Notes

- Audit file used: `docs/06-qa/01-feature-audits/dashboard.md`
- Feature boundary: organization-level landing route `/` inside the protected app shell, including KPI cards, time-window filter, execution trend, project health table, recent activity, and dashboard shortcut navigation. Excludes project-level overview/dashboard routes under `/projects/:projectId`.
- Backend evidence: `uv run pytest tests/unit/api/v1/test_insights.py tests/unit/service/test_insights_service.py -q` passed with 9 tests.
- Frontend evidence: `npm run test -- src/features/dashboard/hooks/useDashboardInsights.test.tsx` passed with 2 tests.
- Coverage gap: no page-level `DashboardPage` tests currently protect landing-state behavior, KPI drill-down correctness, or timezone-safe chart labeling.
