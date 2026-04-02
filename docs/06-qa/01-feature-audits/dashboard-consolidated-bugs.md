# Consolidated Dashboard Audit Bugs

This document aggregates bugs reported across three separate dashboard audit files:
- `docs/06-qa/01-feature-audits/dashboard.md` (Owner: wwwer)
- `docs/06-qa/01-feature-audits/gemini/dashboard.md` (Owner: Gemini CLI)
- `docs/06-qa/01-feature-audits/kiro/dashboard.md` (Owner: Kiro)

---

## P1: Critical / High Priority

### 1. Bootstrap / Landing State Race Condition
- **IDs**: `DASH-001` (wwwer), `KIRO-DASH-001` (Kiro)
- **Problem**: On first load after login, or before `activeOrgId` is populated asynchronously, the dashboard immediately treats the missing active organization as a true empty state. It renders "Please select or create an organization" instead of a proper loading state.
- **Expected**: A brief loading indicator must cover the gap between component mount and organization resolution, distinguishing a genuine no-org state from an active bootstrap state.

### 2. KPI Card Navigation Leads to Incorrect Projects
- **IDs**: `DASH-002` (wwwer), `KIRO-DASH-002` (Kiro)
- **Problem**: The four KPI cards ("Task Completion", "Overdue Tasks", "Critical Tasks", "Overallocated Resources") all navigate to the `firstProjectId` (the highest-risk project) instead of the actual project(s) driving the respective metrics.
- **Expected**: KPI shortcut links should land on the correct destination or filtered view related to the metric clicked, or drill-downs should be omitted if no accurate view exists.

### 3. Trend Chart Timezone Shift Bug
- **IDs**: `DASH-003` (wwwer), `KIRO-DASH-003` (Kiro)
- **Problem**: The trend chart parses plain `YYYY-MM-DD` strings with `new Date(v).toLocaleDateString(...)`. For users in negative UTC offset timezones (e.g., US timezones), this implicitly casts to UTC midnight and renders as the previous calendar day.
- **Expected**: Parse date-only strings without timezone coercion (e.g., `new Date(v + "T00:00:00")`) to ensure the exact API day is displayed consistently across user timezones.

### 4. Recent Activity Feed Lacks Navigation Links
- **IDs**: `DASH-01` (Gemini), `KIRO-DASH-004` (Kiro)
- **Problem**: `InsightsActivityCard` renders activity list items as plain `<li>` tags without click handlers or `<Link>` wrappers. Despite the backend providing `entity_type`, `entity_id`, and `project_id`, users cannot navigate from the activity feed.
- **Expected**: Activity items must be functional links navigating to the relevant project, task, or resource page.

### 5. N+1 Performance Issue in Project Health Query
- **IDs**: `DASH-02` (Gemini), `KIRO-DASH-005` (Kiro)
- **Problem**: In `insights_service.py`, `get_org_dashboard_insights` calls `_project_overallocation_stats` for each project inside a `for` loop, causing 2N extra database queries on every dashboard load.
- **Expected**: Batch the resource and assignment lookups using an `IN` clause to compute over-allocation stats in a single pass.

### 6. `date.today()` Server-Side Timezone Risk
- **IDs**: `DASH-06` (Gemini), `KIRO-DASH-006` (Kiro)
- **Problem**: Time window resolution uses the server's local date (`date.today()`) instead of a consistent UTC anchor. If the server is running in a non-UTC timezone, date boundaries will be globally incorrect.
- **Expected**: Use `datetime.now(timezone.utc).date()` throughout as a safe UTC anchor.

### 7. Missing Realtime Updates for Global Dashboard
- **IDs**: `DASH-03` (Gemini)
- **Problem**: Unlike project-level dashboards, the global dashboard does not utilize WebSocket connections, missing out on real-time task and project change updates.
- **Expected**: Global dashboard should subscribe to relevant WebSockets for state consistency.

---

## P2: Medium / Low Priority

### 8. Insufficient/Basic Refresh Visual Indicator
- **IDs**: `DASH-04` (Gemini)
- **Problem**: Background data refreshes are indicated only by a basic "Refreshing..." text with reduced opacity, feeling unpolished compared to modern standards.
- **Expected**: Upgrade to a refined loading state such as an animated progress bar or skeleton placeholders.

### 9. Missing Automated Tests for Core Components
- **IDs**: `DASH-05` (Gemini), Implied in Kiro's Component Test Coverage list
- **Problem**: Crucial page-level tests and UI-rendering protections do not exist for `DashboardPage.tsx`, `InsightsActivityCard`, and `InsightsTrendCard`. This leaves behaviors like timezone formatting, links, and race conditions unprotected.
- **Expected**: Implement basic rendering and interaction tests for major dashboard UI components.
