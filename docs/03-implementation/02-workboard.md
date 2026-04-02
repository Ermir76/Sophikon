# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S18
**Dates:** 2026-04-03 -> TBD
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.
Guardrail: never delete previous sprint mini-task sections; keep historical sprint blocks intact and append/move only the active sprint block.

---

## Active Items - S18

### DASH-01 — Dashboard bootstrap race — loading vs empty-org indistinguishable

Status: `PENDING`

- [ ] In `DashboardPage.tsx`, import `useOrganizations` from `@/features/organizations` and call it to get `isLoading: isOrgsLoading`
- [ ] Extend the existing loading guard (line 58) to also cover bootstrap: when `!activeOrgId && isOrgsLoading`, show `PageLoading` instead of falling through to the `!activeOrganization` empty-state branch
- [ ] Add focused `DashboardPage` test: mock `useOrganizations` as loading + `activeOrgId` null → assert `PageLoading` renders, not `PageEmpty`

#### Notes

- Files: `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- Root cause: `org-store` hydrates `activeOrgId` from `localStorage` synchronously, but `useOrganizations` list fetch is async. When `activeOrgId` is null (new user, cleared storage, first login), `OrgSwitcher`'s auto-select `useEffect` hasn't fired yet. The page falls through to `!activeOrganization` and renders the empty state.
- The fix must not break the genuine no-org state — only cover the bootstrap gap while orgs are still loading.

### DASH-03 — Dashboard trend chart timezone shift

Status: `PENDING`

- [ ] In `insights-trend-card.tsx` line 48, add the `parseISO` import from `date-fns`, and change `new Date(v)` to `parseISO(v)` in the XAxis `tickFormatter` so plain `YYYY-MM-DD` strings are correctly parsed as local midnight.
- [ ] Add `InsightsTrendCard` unit test: pass a `YYYY-MM-DD` date string, assert formatted label matches that exact calendar day regardless of runtime timezone

#### Notes

- Files: `frontend/src/shared/ui/insights-trend-card.tsx`
- Root cause: `new Date("2026-04-02")` parses as `2026-04-02T00:00:00Z` (UTC). In `America/Los_Angeles` (UTC-7), `toLocaleDateString()` renders this as `Apr 1`. Using `parseISO` correctly treats the string as a timezone-independent local midnight.
- Backend `TrendPoint.date` is a `date` field with no time component — the frontend must display it as-is.

### DASH-06 — Dashboard `date.today()` uses server-local timezone instead of UTC

Status: `PENDING`

- [ ] In `insights_service.py`, add `timezone` to the existing `from datetime import ...` line
- [ ] Replace `today = date.today()` with `today = datetime.now(timezone.utc).date()` at lines 42, 383, and 494
- [ ] Verify existing backend insight tests still pass (`uv run pytest tests/unit/api/v1/test_insights.py tests/unit/service/test_insights_service.py -q`)

#### Notes

- Files: `backend/app/service/insights_service.py`
- Root cause: `date.today()` returns the server's local date. If the server runs in a non-UTC timezone, "today" drifts relative to users. Standard Docker/cloud runs UTC so current risk is low, but this is a fragile assumption.
- No DB/schema changes. Pure service-layer cleanup.

### DASH-04 — Dashboard activity feed not clickable

Status: `PENDING`

- [ ] In `insights-activity-card.tsx`, add `import { Link } from "react-router";`
- [ ] Add a route-builder helper inside the component: `project` → `/projects/${project_id}`, `task` → `/projects/${project_id}/tasks`, `resource` → `/projects/${project_id}/resources`; fallback to `#` if `project_id` is null
- [ ] Wrap each `<li>` inner content in a `<Link to={route}>` with `className="block"` so the entire card area is clickable
- [ ] Add `InsightsActivityCard` unit test: render with sample `task`, `project`, and `resource` items → assert each renders a link with the correct `href`

#### Notes

- Files: `frontend/src/shared/ui/insights-activity-card.tsx`
- The `RecentActivityItem` type already includes `entity_type`, `entity_id`, and `project_id` — all the data needed to build routes.
- For `task` entities, linking to the project's task list is the correct scope since there is no direct `/tasks/:taskId` route in the app.
- This component lives in `shared/ui/` because it is used by both the org dashboard and the project dashboard.

### DASH-05 — Dashboard N+1 in overallocation stats

Status: `PENDING`

- [ ] Add `get_active_resources_for_projects(db, *, project_ids: list[UUID]) -> list[Resource]` to `insights_repo.py` — uses `Resource.project_id.in_(project_ids)` + `Resource.is_active == True`
- [ ] Add `get_assignments_in_range_for_projects(db, *, project_ids: list[UUID], start_date, end_date) -> list[Assignment]` to `utilization_repo.py` — bulk variant of existing `get_assignments_in_range`
- [ ] Add `compute_overallocation_counts(resources: list[Resource], assignments: list[Assignment], start_date, end_date) -> dict[UUID, int]` as a pure function in `insights_service.py` — groups resources and assignments by `project_id`, computes per-project overallocated resource count in-memory without DB calls
- [ ] Rewire the `for project in projects` loop in `get_org_dashboard_insights` to: (1) fetch all resources via `get_active_resources_for_projects`, (2) fetch all assignments via `get_assignments_in_range_for_projects`, (3) call `compute_overallocation_counts` once, (4) look up per-project count from the returned dict
- [ ] Remove the per-project `_project_overallocation_stats` call from the loop (the function itself stays for project-level dashboard use)
- [ ] Verify existing backend insight + utilization tests still pass
- [ ] Add a test case: org with 3 projects returns correct per-project overallocation counts from the batched path

#### Notes

- Files: `backend/app/repository/insights_repo.py`, `backend/app/repository/utilization_repo.py`, `backend/app/service/insights_service.py`
- The existing `_project_overallocation_stats` calls `utilization_service.detect_over_allocations` + `insights_repo.get_active_resources_for_project` per project — 2N queries. The batch approach reduces this to 2 queries total.
- `_project_overallocation_stats` is still used by `get_project_dashboard` (single project) — do not delete it.

### DASH-02 — Dashboard KPI cards drill into wrong project

Status: `PENDING`

#### Design Decisions (locked)

**Decision:** Option (a) — KPI cards link to `/projects` (org-level project list). The four metric KPI cards ("Task Completion", "Overdue Tasks", "Critical Tasks", "Overallocated Resources") are org-level aggregates; linking to a single project is incorrect. The project list is the correct drill-down scope until per-metric filtered views exist.

- [ ] In `DashboardPage.tsx`, change "Task Completion" card `to` from `firstProjectId ? \`/projects/${firstProjectId}/tasks\` : "/projects"` to `"/projects"`
- [ ] Change "Overdue Tasks" card `to` to `"/projects"`
- [ ] Change "Critical Tasks" card `to` to `"/projects"`
- [ ] Change "Overallocated Resources" card `to` from `firstProjectId ? \`/projects/${firstProjectId}/utilization\` : "/projects"` to `"/projects"`
- [ ] Remove the `firstProjectId` variable (line 97) since it is no longer used
- [ ] Add focused `DashboardPage` test: assert all 4 metric KPI cards render links pointing to `/projects`, not to a specific project ID

#### Notes

- Files: `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- The "Active Projects" and "Completed Projects" cards already link to `/projects` — this change makes all 6 KPI cards consistent.
- Future enhancement: add query-param filters to `/projects` page (e.g. `?sort=completion`, `?filter=overdue`) so KPI cards can deep-link to a meaningful filtered view.

---

## Active Items - S17

### QA-01 - Carry-forward manual verification sweep

Status: `DONE`

- [ ] Verify `FIX-20`: browser check for close/reopen behavior across session-only vs persistent login
- [ ] Verify `FIX-18`: run `EXPLAIN ANALYZE` and confirm the task search query uses the GIN index
- [ ] Verify `FIX-19`: search results refresh correctly after task create/update/delete
- [ ] Verify `AGT-08`: `search_tasks` hit with `is_summary: true` followed by `get_tasks(parent_task_id=...)` returns direct children only
- [ ] Verify `AGT-07`: streaming still works end-to-end for Anthropic, OpenAI, and Gemini after prompt-cache wiring

#### Pending

- Every verification result must be recorded as `PASS`, `FAIL`, or converted into a new follow-up issue
- After the result is recorded here, do not reopen the old S16 checkbox for the same work

### AUTH-01 - Unverified user enforcement after verification expiry (#48)

Status: `PENDING`

- [x] Lock policy: immediate verification email on registration, reminder emails at 6 hours and 12 hours, 24-hour grace period from `user.created_at`, then hard auth/session block if `email_verified` is still false
- [x] Define the recovery contract for blocked users: resend verification action plus clear blocked-state messaging instead of a generic logged-out failure
- [x] Add a single backend policy helper for "verification required after grace period" so login, refresh, and protected-route auth checks use the same rule
- [x] Enforce the policy in `login_user` so expired unverified users cannot start a new session
- [x] Enforce the policy in `refresh_tokens` so expired unverified users cannot silently extend an old session
- [x] Enforce the policy in the protected auth dependency used by `/auth/me` and the rest of the protected API
- [x] Replace reminder-only UX with blocked-state recovery messaging on auth entry/recovery screens while keeping the in-app banner for pre-expiry reminder state as non-dismissible or snoozable, not permanently dismissible
- [x] Add focused backend tests for grace-period vs expired behavior across login, refresh, `/auth/me`, and a representative protected endpoint
- [x] Add focused frontend tests for blocked-session recovery and resend messaging
- [x] Record outcome against issue `#48`: targeted backend/frontend auth-policy coverage passed; broader auth slice still contains an unrelated flaky oauth-state baseline test outside this feature scope

#### Notes

- Source issue: `issues/open_issues/48-unverified-users-have-no-enforcement-after-link-expiry.md`
- Priority: P0 / Highest priority
- Design decision locked on branch `auth-01-unverified-policy`: immediate verification email, reminder emails at 6h and 12h, hard backend block after the 24-hour grace period, not partial per-action restriction
- Current backend gap: registration/login mint normal sessions, `get_current_active_user` checks `is_active` only, and frontend enforcement is limited to `EmailVerificationBanner`
- Recommended backend touch points: `backend/app/service/auth_service.py`, `backend/app/api/deps/auth.py`, `backend/app/api/v1/endpoints/auth.py`
- Recommended background-task touch points: reminder-email scheduling in the existing Celery path so 6h/12h nudges are handled server-side, not by frontend polling
- Recommended frontend touch points: `frontend/src/features/auth/pages/LoginPage.tsx`, `frontend/src/features/auth/pages/VerifyEmailPage.tsx`, `frontend/src/features/auth/components/EmailVerificationBanner.tsx`, auth-store/bootstrap handling if blocked state needs a distinct redirect
- Schema assumption for design: no DB migration required if the grace period is derived from existing `user.created_at`; revisit only if admin override/state needs emerge
- Build status: backend policy enforcement, reminder scheduling, public resend flow, and frontend blocked/snooze UX are implemented on branch `auth-01-unverified-policy`; focused backend/frontend auth-policy tests are in place and passing, with one unrelated flaky oauth-state baseline test still present in the broader auth slice

---

## Active Items - S16

### FIX-20 — Auth remember-me and verification recovery hardening

Status: `DONE`

- [x] Wire `Keep me logged in` to real login form state and request payload
- [x] Preserve session-only vs persistent cookie policy across `/auth/login` and `/auth/refresh`
- [x] Persist remember-me choice on refresh-token records with migration support
- [x] Add focused backend coverage for login and refresh cookie persistence behavior
- [x] Add focused frontend coverage for login remember-me submission and verify-email resend recovery feedback
- [x] Manual verification in browser across close/reopen flow moved to `S17 / QA-01`

#### Notes

- Files: `backend/app/api/v1/endpoints/auth.py`, `backend/app/service/auth_service.py`, `backend/app/models/refresh_token.py`, `backend/alembic/versions/b4d5e6f7a8c9_add_refresh_token_persistence_flag.py`, `backend/tests/unit/api/v1/test_auth.py`, `frontend/src/features/auth/pages/LoginPage.tsx`, `frontend/src/features/auth/pages/VerifyEmailPage.tsx`
- Review gate: `PASS` via `/rr` after backend-review, frontend-review, pydantic-audit, and consistency-review
- Decision: session persistence is now an explicit server-side policy carried by the refresh-token row instead of an implicit cookie-only behavior

### FIX-18 — GIN index mismatch

Status: `DONE`

- [x] Change tsvector expression in `task_repo.py` from `concat_ws()` to `coalesce() || coalesce()` matching the migration index
- [x] Verify with EXPLAIN ANALYZE that the index is used (manual) moved to `S17 / QA-01`

### FIX-19 — Search cache invalidation

Status: `DONE`

- [x] Add `taskKeys.searches()` invalidation to all 9 mutation `onSuccess` callbacks in `useTasks.ts`
- [x] Verify search results refresh after task create/update/delete (manual) moved to `S17 / QA-01`

### AGT-08 — Agent subtask drill-down

Status: `DONE`

#### Design Decisions (locked)

**Problem:** Agent has no efficient way to go downward in the task tree. `search_tasks` doesn't return `is_summary`, and `get_tasks` has no parent filter — agent must load all tasks and reason over `parent_task_id` fields.

**Changes — all in `backend/app/service/agent/tool_registry.py`:**

1. **`get_tasks` schema** — add optional `parent_task_id` string param with description: "If provided, return only direct children of this task. Use to drill into a summary task's subtasks."
2. **`get_tasks` execution** — when `parent_task_id` is provided, add `Task.parent_task_id == parent_task_id` filter to the DB query (not client-side filtering).
3. **`get_tasks` description** — update to: "Get tasks for the project. Pass parent_task_id to get only direct children of a summary task — use this to drill into subtasks efficiently instead of loading the full project. Returns WBS codes, dates, progress, hierarchy."
4. **`search_tasks` response** — add `"is_summary": task.is_summary` to each result dict.

**No DB/schema/migration changes.** `parent_task_id` and `is_summary` already exist on Task model.

#### Checklist

- [x] Add `parent_task_id` optional filter param to `get_tasks` tool schema
- [x] Add `parent_task_id` filter in `get_tasks` execution block
- [x] Update `get_tasks` tool description to document drill-down pattern
- [x] Add `is_summary` field to `search_tasks` response payload
- [x] Verify: search "Phase 1" shows `is_summary: true`, then `get_tasks(parent_task_id=...)` returns children only (manual) moved to `S17 / QA-01`

### AGT-07 — Prompt caching last-mile

Status: `DONE`

#### Design Decisions (locked)

**Problem:** `prompt_cache` metadata flows from backend agent layer to ai-service HTTP boundary, but `brain_service.py` drops it before calling providers. No provider applies caching.

**Changes:**

1. **`ai-service/app/service/brain_service.py`** — add `prompt_cache=request.prompt_cache` kwarg to all 3 provider calls (Anthropic, OpenAI, Gemini).
2. **`ai-service/app/service/providers/anthropic_provider.py`** — accept `prompt_cache: dict | None = None`. When not None, convert `system` from plain string to content block list: `[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]`. When None, keep plain string (no breaking change).
3. **`ai-service/app/service/providers/openai_provider.py`** — accept `prompt_cache: dict | None = None`. No-op: OpenAI caching is automatic for prompts >= 1024 tokens. Param accepted for contract consistency.
4. **`ai-service/app/service/providers/gemini_provider.py`** — accept `prompt_cache: dict | None = None`. No-op: Gemini caching requires separate `cachedContent.create` call with 32K+ token minimum (our prompts are below). Param accepted for forward-compatibility.
5. **`ai-service/tests/test_brain_service.py`** — flip assertion from `assert "prompt_cache" not in kwargs` to `assert kwargs.get("prompt_cache") is not None`.

**No schema changes.** `PromptCacheMetadata` and `CompleteRequest.prompt_cache` already exist.

#### Checklist

- [x] Forward `prompt_cache` param from `brain_service.py` to all 3 provider calls
- [x] Anthropic provider: accept param, wrap system prompt in content block with `cache_control` when present
- [x] OpenAI provider: accept param (no-op, automatic caching)
- [x] Gemini provider: accept param (no-op, forward-compatibility)
- [x] Update `test_brain_service.py` assertion to verify passthrough
- [x] Verify streaming still works end-to-end for all 3 providers (manual) moved to `S17 / QA-01`

---

## Active Items - S15

### UX-08 - Settings consolidation

Status: `DONE`

#### Design Decisions (locked — do not deviate without approval)

**File structure**
```
frontend/src/features/settings/
  index.ts
  pages/
    SettingsPage.tsx
  components/
    SettingsLayout.tsx
    SettingsAnchorNav.tsx
    sections/
      ProfileSection.tsx
      SecuritySection.tsx
      NotificationsSection.tsx
      AiPreferencesSection.tsx
      GeneralSection.tsx
      MembersSection.tsx
      BillingSection.tsx
  hooks/
    useActiveSection.ts
```

**Component tree**
- `AppLayout` (unchanged) wraps `/settings` route
- `SettingsPage` → `SettingsLayout` (2-col: anchor nav + scrollable content)
- `SettingsAnchorNav` in left col; section components in right col wrapped in `<div ref>`
- App sidebar is already the left column from `AppLayout` — `SettingsLayout` does NOT add a third sidebar

**Component interfaces**
- `SettingsLayout`: props `anchorNav: React.ReactNode`, `children: React.ReactNode`. Desktop: side-by-side. Mobile `< 768px`: anchor nav becomes sticky horizontal pill bar above content.
- `SettingsAnchorNav`: props `activeSection: string`, `onSectionClick: (id: string) => void`, `isAdminOrOwner: boolean`. Hides General + Members when `!isAdminOrOwner`.
- All section components: **zero props**. Each owns its hooks and mutations internally. `GeneralSection` and `MembersSection` read `activeOrgId` from `useOrgStore` internally — render graceful empty state when null (handles both no-org and org-switcher mid-session).

**Ref pattern in SettingsPage**
- `SettingsPage` creates a `ref` per section via `useRef<HTMLDivElement>()`.
- Refs are attached to wrapper `<div>` elements in `SettingsPage`, NOT passed as props into section components.
- `useActiveSection(refs, sectionOrder)` returns the currently visible `activeSection` string via `IntersectionObserver` (threshold 0.3, fallback to first section).

**`useActiveSection` hook signature**
```ts
function useActiveSection(
  refs: Record<string, React.RefObject<HTMLDivElement>>,
  sectionOrder: string[]
): string
```

**State ownership**
- `activeSection` string: `SettingsPage` (via `useActiveSection`)
- Profile/avatar mutations: `ProfileSection` internal (existing `useUpdateProfile`, `useUploadAvatar`, `useDeleteAvatar`)
- Password form: `SecuritySection` internal (existing `useChangePassword`)
- AI prefs draft + pending toggle: `AiPreferencesSection` internal (existing `useAiPreferences`, `useUpdateAiPreferences`)
- Notification toggles: `NotificationsSection` internal (`useNotificationSettings`, `useUpdateNotificationSettings` from `@/features/notifications`)
- Org general form + delete: `GeneralSection` internal (existing `useOrganization`, `useUpdateOrganization`, `useDeleteOrganization`)
- Members + invite + role + remove dialogs: `MembersSection` internal (existing hooks + local dialog state)
- No new Zustand stores. No new API calls.

**Notification fields** — 4 toggles from `NotificationSettings`:
`email_task_assigned`, `email_mentioned`, `email_deadline_approaching`, `push_enabled`.
Each fires `useUpdateNotificationSettings` individually on toggle change (same pattern as AI toggles).

**NavUser footer redesign**
- Add `<Link to="/settings">` Settings button (with ⚙ icon) stacked above the avatar `DropdownMenuTrigger`
- Remove "Profile" `DropdownMenuItem`
- Remove "Settings" `DropdownMenuItem`
- Dropdown retains: Theme group (Light/Dark/System) + Log out only

**AppSidebar changes**
- Remove `{ title: "Members", url: "/members", icon: Users }` from `globalNavItems`
- Remove `{ title: "Settings", url: "/settings", icon: Settings }` from `globalNavItems`
- Add `defaultOpen={false}` to `<Sidebar>` (or equivalent prop per shadcn sidebar API)

**Wireframe reference**: `settings-layout-wireframe.excalidraw` in repo root — 3 breakpoints: wide ≥1024px, medium 768–1023px, mobile <768px.

#### Mini-tasks

**Design phase**
- [x] Define `features/settings/` file structure and barrel exports
- [x] Define `SettingsAnchorNav` component contract: active section state management, scroll-to-section wiring, IntersectionObserver hook interface
- [x] Define prop interfaces for each section component

**New feature folder + layout**
- [x] Create `features/settings/` folder: `SettingsPage`, 3-column layout wrapper, `SettingsAnchorNav` component
- [x] `SettingsAnchorNav`: sections Profile, Security, Notifications, AI Preferences, General, Members, Billing; General + Members hidden for non-admin/non-owner roles
- [x] Mobile: anchor nav becomes sticky horizontal pill bar at `< 768px`
- [x] `IntersectionObserver` active-section tracking + smooth scroll-to-section on anchor nav click

**Profile section** (extracted from ProfilePage tab 1)
- [x] Merged avatar + profile form in one card; AlertDialog for avatar removal; upload/delete flows unchanged (2MB, png/jpeg/webp, toasts + inline errors)
- [x] Remove disabled-save helper text while preserving dirty/pending button state

**Security section** (extracted from ProfilePage tab 2)
- [x] Change password with live 4-item checklist (length, uppercase, number, special char)
- [x] Inline Account Recovery link below Change Password submit (demoted from standalone card)

**AI Preferences section** (extracted from ProfilePage tab 3)
- [x] Toggle table with Tool / Auto-approve column header row
- [x] Separator + subheading groups (remove bordered containers)

**Notifications section** (new)
- [x] Email notification toggles using `useNotificationSettings` / `useUpdateNotificationSettings`

**General section** (extracted from OrgSettingsPage)
- [x] Org name/slug/description form; render graceful empty state when `activeOrgId` is null

**Members section** (extracted from OrgMembersPage)
- [x] Member list + role management + invite flow; render graceful empty state when `activeOrgId` is null

**Billing section**
- [x] Placeholder card (coming soon)

**Route + nav wiring**
- [x] `App.tsx`: `/settings` to global scope (remove OrgGuard), `/profile` -> `<Navigate to="/settings">`, `/members` -> `<Navigate to="/settings">`
- [x] `App.tsx`: remove lazy imports for ProfilePage, OrgSettingsPage, OrgMembersPage
- [x] `NavUser`: add Settings button (direct link to `/settings`) above avatar row; slim dropdown to Theme + Logout only; remove Profile item
- [x] `AppSidebar`: remove Members and Settings from `globalNavItems`; set `defaultOpen={false}`
- [x] `AppHeader`: update "Manage notification settings" link to `/settings`

**Cleanup**
- [x] Grep confirms no remaining consumers of `/profile` or `/members` beyond already-touched files
- [x] Delete `ProfilePage.tsx` and `ProfilePage.test.tsx` after content extracted
- [x] Delete `OrgSettingsPage.tsx`, `OrgSettingsPage.test.tsx`, `OrgMembersPage.tsx`, `OrgMembersPage.test.tsx` after content extracted and role guards replicated
- [x] Remove `ProfilePage`, `OrgSettingsPage`, `OrgMembersPage` exports from feature barrels (`features/auth/index.ts`, `features/organizations/index.ts`)

**Tests**
- [x] `AppHeader.test.tsx`: update `/profile` assertion to `/settings`
- [x] Write `SettingsPage` focused tests: anchor nav rendering, section visibility, notifications toggles, org sections conditional on `activeOrgId`

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Frontend-only; no backend endpoints or schema changes.
  - Reuse existing feature hooks and `shared/ui` primitives only.
  - OrgGuard replaced by per-section conditional rendering (also handles org switcher mid-session).
  - Wireframe: `settings-layout-wireframe.excalidraw` in repo root (3 breakpoints: wide ≥1024px, medium 768–1023px, mobile <768px) — primary layout reference for build.

---

## Previous Sprint Items - S14
### AGT-05 Ã¢â‚¬â€ Task search rewrite: DB-level search for UI + agent

Status: `DONE`

#### Mini-tasks

- [x] Add task search endpoint `GET /projects/{project_id}/tasks/search`
- [x] Enforce non-empty trimmed `q`; return `400 VALIDATION_ERROR` for empty `q`
- [x] Support `status` filter with model-level enum values only (`BACKLOG|TODO|IN_PROGRESS|IN_REVIEW|DONE`)
- [x] Support `overdue_only` and `include_parents` query params
- [x] Implement repository full-text query (name + notes) with result limit
- [x] Add migration/index for search performance (GIN on task search vector expression)
- [x] Add service-layer `search_tasks` function and keep layer direction `api -> service -> repository`
- [x] Rewire agent `search_tasks` tool to call DB-level search path (remove in-memory 250-task filtering)
- [x] Frontend: add task search API client + hook + debounced query usage in Tasks view
- [x] Keep explicit loading/empty/error states for search UI

#### QA Coverage

- [x] Backend API integration tests for `/tasks/search` happy + bad paths (`q` trim validation, status filter, include_parents)
- [x] Backend agent tool tests for `search_tasks` schema and invalid filter handling
- [x] Frontend hook tests for `useTaskSearch` enabled/disabled behavior
- [x] Frontend page tests for search mode rendering and empty/error behavior
- [x] Run targeted backend + frontend test commands and record result

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - v1 search is limit-only (no offset/cursor pagination and no total count return)
  - No fallback mode for empty query Ã¢â‚¬â€ this endpoint is search-only by contract
  - QA rerun passed after repository search-expression fix (`backend` + `frontend` targeted suites green; gate `GO`).

---

### AGT-06 Ã¢â‚¬â€ Agent foundation: prompt versioning + tool catalog + prompt caching hooks

Status: `DONE`

#### Mini-tasks

- [x] Introduce versioned prompt module with `PROMPT_VERSION = "1"`
- [x] Persist/log prompt version with each conversation run for traceability
- [x] Refactor planner/executor to share the same tool catalog source
- [x] Add optional prompt-caching metadata in backend `AICompleteRequest`
- [x] Add matching optional prompt-caching metadata in ai-service `CompleteRequest`
- [x] Keep metadata backward-compatible when provider ignores caching hints
- [x] Add a concise baked domain-knowledge section to system prompt (without loading full project dump)
- [x] Verify existing plan/execute/approval flow remains unchanged

#### QA Follow-up Mini-tasks

- [x] Fix backend agent tests broken by prompt refactor (`history.build_system_prompt` removal)
- [x] Update loop/history test mocks for new `set_prompt_metadata` path
- [x] Re-run targeted backend suites: planner/executor/loop/history/ai_service
- [x] Fix ai-service contract test run-path/import issue and re-run `tests/test_contracts.py`
- [x] Re-run ai-service `tests/test_brain_service.py` + `tests/test_contracts.py` and record final QA gate
#### Notes

- Dependencies: AGT-05 recommended first (search quality impacts agent usefulness immediately)
- Blockers: provider-specific cache support may be partial
- Decisions:
  - Foundation work in this sprint is contract + wiring; deep provider optimization is follow-up
  - QA gate `GO`: `backend/tests/unit/service/test_agent_executor.py`, `backend/tests/unit/service/test_agent_history.py`, `backend/tests/unit/service/test_agent_loop.py`, `ai-service/tests/test_brain_service.py`, and `ai-service/tests/test_contracts.py` passed.

---

## Previous Sprint Items Ã¢â‚¬â€ S13

### UX-06 Ã¢â‚¬â€ AI panel styling & layout redesign

Status: `DONE`

#### Mini-tasks

- [x] Message bubbles redesign Ã¢â‚¬â€ user messages: right-aligned `bg-muted`, no role label; AI messages: left-aligned, no background, small Bot icon prefix, no role label
- [x] ToolCallRow restyle Ã¢â‚¬â€ running: muted line + spinner; done: muted line + checkmark, no colored box/border; error/denied: `text-destructive` line; tight stacking like a log
- [x] Status banners Ã¢â‚¬â€ replace `bg-amber-50`/`bg-blue-50` hardcoded stripes with `bg-muted` + differentiating icon (AlertTriangle for interrupted, Clock for awaiting approval)
- [x] Suggestion severity Ã¢â‚¬â€ replace `text-amber-500`/`text-emerald-500` with Badge variants (`destructive` for HIGH, `secondary` for MEDIUM, `outline` for LOW)
- [x] PlanApprovalCard Ã¢â‚¬â€ `bg-card/80` Ã¢â€ â€™ `bg-card`, clean border, no opacity hacks
- [x] ReasoningStep Ã¢â‚¬â€ `bg-muted/30` Ã¢â€ â€™ `bg-muted`
- [x] Input area Ã¢â‚¬â€ remove `text-[11px]` arbitrary sizes on selects/hints, let design system defaults apply
- [x] Overall panel Ã¢â‚¬â€ ensure `bg-background` base, no ad-hoc color overrides remaining
- [x] ToolCallRow code block Ã¢â‚¬â€ replace `bg-black/5 dark:bg-white/5` with `bg-muted`

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Pure styling change Ã¢â‚¬â€ no state/logic changes
  - Reference: `docs/02-design/adr/ADR-010-unified-floating-task-detail-panel.md`

---

### UX-07 Ã¢â‚¬â€ Unified floating TaskDetailPanel across all views (ADR-010)

Status: `DONE`

#### Mini-tasks

- [x] TasksPage state split Ã¢â‚¬â€ add `detailTaskId` state, rewire `<TaskDetailPanel>` to use it with `floating`, keep `selectedTaskId` for row highlight only
- [x] Task table double-click Ã¢â‚¬â€ add `onDoubleClick` handler on `SortableTableRow` that calls `onViewDetails(taskId)`, which now maps to `setDetailTaskId`
- [x] Kanban store update Ã¢â‚¬â€ add `detailTaskId`, `setDetailTaskId`, `clearDetailTaskId` to `kanban-store.ts` (not persisted)
- [x] KanbanPage state split Ã¢â‚¬â€ wire `detailTaskId` from store to `<TaskDetailPanel floating>`, keep `selectedTaskId` for card highlight
- [x] Kanban card double-click Ã¢â‚¬â€ single click selects (highlight), double-click opens detail panel
- [x] Keep alternative openers Ã¢â‚¬â€ kebab menu "View Details" and context menu still call `setDetailTaskId`
- [x] Update tests Ã¢â‚¬â€ adjust test assertions for TasksPage, KanbanPage, and kanban-store to match new state split

#### Notes

- Dependencies: UX-06 (styling should land first to avoid merge conflicts in same files)
- Blockers: -
- Decisions:
  - GanttPage already uses the target pattern Ã¢â‚¬â€ no changes needed there
  - TaskDetailPanel component already supports `floating` prop Ã¢â‚¬â€ no changes needed there
  - Final interaction contract: single click selects/highlights, double-click opens floating detail panel; explicit "View Details" actions remain valid openers
  - Reference: `docs/02-design/adr/ADR-010-unified-floating-task-detail-panel.md`

---

## Previous Sprint Items Ã¢â‚¬â€ S12

### AGT-01 Ã¢â‚¬â€ Agent policy engine: centralized permission and role check before every tool execution

Status: `DONE`

#### Mini-tasks

- [x] Define `ToolPolicy` enum (`allow`, `allow_with_approval`, `deny`) and `PolicyDecision` dataclass
- [x] Create `agent/policy.py` with `check_tool_policy(tool_name, tool_input, ctx) Ã¢â€ â€™ PolicyDecision`
- [x] Implement action allowlist check Ã¢â‚¬â€ reject unknown tool names
- [x] Implement role check Ã¢â‚¬â€ map project role (viewer/member/manager/owner) to allowed tool tiers (read/write/destructive/UI)
- [x] Implement scope check Ã¢â‚¬â€ validate entity IDs in `tool_input` belong to `ctx.project_id` (task/dependency/assignment/resource IDs)
- [x] Add `role_name` to `AgentContext` and pass it from AI endpoint `ProjectAccess` when building the context
- [x] Wire `check_tool_policy` into `executor.py` before tool execution and before destructive approval branching
- [x] On `deny` Ã¢â€ â€™ return explicit tool-result error to the LLM (no execution)
- [x] On `allow_with_approval` Ã¢â€ â€™ reuse existing `_wait_for_tool_approval` mechanism
- [x] Add default policy config (viewer=read+UI only, member=read+write+UI, manager/owner=all)
- [x] Tests: viewer blocked from write tools, member allowed writes, deny on unknown tool, scope violation returns deny, destructive tools still require per-action approval

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Policy is implemented as a pure service-layer decision function and keeps destructive approval as a second gate.
  - Scope validation is object-level and project-scoped for task/dependency/resource/assignment references.

---

### AGT-02 Ã¢â‚¬â€ Agent kill switch: per-project and per-org flag to disable agent execution

Status: `DONE`

#### Mini-tasks

- [x] Add `agent_enabled` boolean to project settings JSON schema (default: true when missing)
- [x] Add `agent_enabled` boolean to organization settings JSON schema (default: true when missing)
- [x] Check both flags at `prepare_chat_stream` entry Ã¢â‚¬â€ reject with clear `InvalidOperationError` if either is false
- [x] Org-level false overrides project-level true (org wins)
- [x] Apply same kill-switch guard in proactive agent monitor flow before analysis execution
- [x] Frontend: add "AI Agent" toggle in project settings page
- [x] Frontend: when agent is disabled, show disabled AI panel state with explanation and block chat input/actions
- [x] Frontend transport: surface backend `error.message` for non-OK AI chat responses instead of status-only errors
- [x] Tests: chat rejected when project flag false, chat rejected when org flag false, chat works when both true, proactive monitor skips disabled projects
- [x] Tests: proactive monitor imports public `agent.utils` API (`read_user_ai_preferences`, `resolve_effective_provider_model`) and still resolves provider/model + API key correctly

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Kill switch stays in JSON settings (no migration/column changes).
  - Defaults are permissive when keys are missing (`true`) for backward compatibility.

---

## Previous Sprint Items Ã¢â‚¬â€ S10

### UX-01 Ã¢â‚¬â€ Invitation flow blockers + recovery

Status: `DONE`

#### Mini-tasks

- [x] Fix invalid invitation dead-end copy and add explicit "Back to dashboard" recovery CTA
- [x] Update invitation page loading state with spinner + `aria-live="polite"` and user-facing wording
- [x] Add invitation-page error `role="alert"` and vertically center invitation card states
- [x] Replace misleading review-mode "Back" behavior with actual back navigation or explicit "Cancel"
- [x] Add focused tests for invalid token/missing payload/review-mode navigation states

#### Notes

- Dependencies: FIX-14
- Blockers: -
- Decisions: Keep invitation token contract unchanged; this sprint is UX-only unless a blocker appears.

---

### UX-02 Ã¢â‚¬â€ Notification center IA + accessibility baseline

Status: `DONE`

#### Mini-tasks

- [x] Move notification settings controls out of bell dropdown into dedicated settings destination
- [x] Add explicit notification settings entry-point link from the dropdown
- [x] Normalize bell and notification action hit targets to mobile-safe minimums
- [x] Add screen-reader labels for unread counts and per-notification read actions
- [x] Rename ambiguous copy ("Read", "Review", websocket status labels) to user-facing language

#### Notes

- Dependencies: UX-01
- Blockers: Destination route for notification settings if `/settings/notifications` is not ready
- Decisions: Keep notification feed focused on triage actions only.

---

### UX-03 Ã¢â‚¬â€ Membership actions safety + copy clarity

Status: `DONE`

#### Mini-tasks

- [x] Add role-change confirmation or undo affordance before finalizing member role mutations
- [x] Improve member-removal confirmation title to include affected member name
- [x] Remove or rewrite decorative/unclear labels (for example "Access list")
- [x] Add accessible header labeling for actions column in members table
- [x] Verify role/action buttons keep consistent min sizes and copy semantics

#### Notes

- Dependencies: FIX-08
- Blockers: -
- Decisions: Prefer undo flow where fast/low-risk; use confirm dialog for destructive actions.

---

### UX-04 Ã¢â‚¬â€ Profile settings usability batch

Status: `DONE`

#### Mini-tasks

- [x] Disable profile save button when form is pristine, with clear state cue
- [x] Show password requirements before submit; align validation message wording
- [x] Add avatar update success feedback and avatar delete confirmation
- [x] Group AI tool toggles by intent with section labels
- [x] Replace technical wording (for example "Locale") with user-facing labels

#### Notes

- Dependencies: FIX-04, FIX-05
- Blockers: -
- Decisions: Keep this batch in existing profile page architecture; no route split in this sprint.

---

### FIX-17 Ã¢â‚¬â€ AI service mock-provider tests fail in live mode (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_estimate_for_project_with_mock_provider`
- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_suggestions_for_project_with_mock_provider`
- [x] Verify all 17 ai_service tests pass without live AI service

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fake payloads match `AIEstimateItem` and `AISuggestionItem` schemas exactly; same pattern as existing mocked tests.

---

### UX-05 Ã¢â‚¬â€ Visual consistency polish pass (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Normalize non-standard tiny text values to design-scale tokens
- [x] Unify spacing rhythm in profile/member pages
- [x] Rationalize badge/stat opacity and color usage
- [x] Ensure notification dropdown width is responsive on narrow screens

#### Notes

- Dependencies: UX-01, UX-02, UX-03, UX-04
- Blockers: -
- Decisions: Pull in only after committed items pass review.

---

## Previous Sprint Items Ã¢â‚¬â€ S09

### FIX-14 Ã¢â‚¬â€ Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line Ã¢â‚¬â€ keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page Ã¢â‚¬â€ review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page Ã¢â‚¬â€ auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page Ã¢â‚¬â€ fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page Ã¢â‚¬â€ after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 Ã¢â‚¬â€ route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 Ã¢â‚¬â€ Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 Ã¢â‚¬â€ Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S10
**Dates:** 2026-03-26 -> 2026-03-28
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S10

### UX-01 Ã¢â‚¬â€ Invitation flow blockers + recovery

Status: `DONE`

#### Mini-tasks

- [x] Fix invalid invitation dead-end copy and add explicit "Back to dashboard" recovery CTA
- [x] Update invitation page loading state with spinner + `aria-live="polite"` and user-facing wording
- [x] Add invitation-page error `role="alert"` and vertically center invitation card states
- [x] Replace misleading review-mode "Back" behavior with actual back navigation or explicit "Cancel"
- [x] Add focused tests for invalid token/missing payload/review-mode navigation states

#### Notes

- Dependencies: FIX-14
- Blockers: -
- Decisions: Keep invitation token contract unchanged; this sprint is UX-only unless a blocker appears.

---

### UX-02 Ã¢â‚¬â€ Notification center IA + accessibility baseline

Status: `DONE`

#### Mini-tasks

- [x] Move notification settings controls out of bell dropdown into dedicated settings destination
- [x] Add explicit notification settings entry-point link from the dropdown
- [x] Normalize bell and notification action hit targets to mobile-safe minimums
- [x] Add screen-reader labels for unread counts and per-notification read actions
- [x] Rename ambiguous copy ("Read", "Review", websocket status labels) to user-facing language

#### Notes

- Dependencies: UX-01
- Blockers: Destination route for notification settings if `/settings/notifications` is not ready
- Decisions: Keep notification feed focused on triage actions only.

---

### UX-03 Ã¢â‚¬â€ Membership actions safety + copy clarity

Status: `DONE`

#### Mini-tasks

- [x] Add role-change confirmation or undo affordance before finalizing member role mutations
- [x] Improve member-removal confirmation title to include affected member name
- [x] Remove or rewrite decorative/unclear labels (for example "Access list")
- [x] Add accessible header labeling for actions column in members table
- [x] Verify role/action buttons keep consistent min sizes and copy semantics

#### Notes

- Dependencies: FIX-08
- Blockers: -
- Decisions: Prefer undo flow where fast/low-risk; use confirm dialog for destructive actions.

---

### UX-04 Ã¢â‚¬â€ Profile settings usability batch

Status: `DONE`

#### Mini-tasks

- [x] Disable profile save button when form is pristine, with clear state cue
- [x] Show password requirements before submit; align validation message wording
- [x] Add avatar update success feedback and avatar delete confirmation
- [x] Group AI tool toggles by intent with section labels
- [x] Replace technical wording (for example "Locale") with user-facing labels

#### Notes

- Dependencies: FIX-04, FIX-05
- Blockers: -
- Decisions: Keep this batch in existing profile page architecture; no route split in this sprint.

---

### FIX-17 Ã¢â‚¬â€ AI service mock-provider tests fail in live mode (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_estimate_for_project_with_mock_provider`
- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_suggestions_for_project_with_mock_provider`
- [x] Verify all 17 ai_service tests pass without live AI service

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fake payloads match `AIEstimateItem` and `AISuggestionItem` schemas exactly; same pattern as existing mocked tests.

---

### UX-05 Ã¢â‚¬â€ Visual consistency polish pass (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Normalize non-standard tiny text values to design-scale tokens
- [x] Unify spacing rhythm in profile/member pages
- [x] Rationalize badge/stat opacity and color usage
- [x] Ensure notification dropdown width is responsive on narrow screens

#### Notes

- Dependencies: UX-01, UX-02, UX-03, UX-04
- Blockers: -
- Decisions: Pull in only after committed items pass review.

---

## Previous Sprint Items Ã¢â‚¬â€ S09

### FIX-14 Ã¢â‚¬â€ Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line Ã¢â‚¬â€ keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page Ã¢â‚¬â€ review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page Ã¢â‚¬â€ auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page Ã¢â‚¬â€ fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page Ã¢â‚¬â€ after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 Ã¢â‚¬â€ route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 Ã¢â‚¬â€ Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 Ã¢â‚¬â€ Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S09
**Dates:** 2026-03-25 -> 2026-03-25
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S09

### FIX-14 Ã¢â‚¬â€ Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line Ã¢â‚¬â€ keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page Ã¢â‚¬â€ review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page Ã¢â‚¬â€ auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page Ã¢â‚¬â€ fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page Ã¢â‚¬â€ after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 Ã¢â‚¬â€ route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 Ã¢â‚¬â€ Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 Ã¢â‚¬â€ Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S08
**Dates:** 2026-03-25 -> 2026-03-25
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S07
**Dates:** 2026-03-24 -> 2026-03-24
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S12
**Dates:** TBD
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S12

### AGT-01 Ã¢â‚¬â€ Agent policy engine: centralized permission and role check before every tool execution

Status: `DONE`

#### Mini-tasks

- [x] Define `ToolPolicy` enum (`allow`, `allow_with_approval`, `deny`) and `PolicyDecision` dataclass
- [x] Create `agent/policy.py` with `check_tool_policy(tool_name, tool_input, ctx) Ã¢â€ â€™ PolicyDecision`
- [x] Implement action allowlist check Ã¢â‚¬â€ reject unknown tool names
- [x] Implement role check Ã¢â‚¬â€ map project role (viewer/member/manager/owner) to allowed tool tiers (read/write/destructive/UI)
- [x] Implement scope check Ã¢â‚¬â€ validate entity IDs in `tool_input` belong to `ctx.project_id` (task/dependency/assignment/resource IDs)
- [x] Add `role_name` to `AgentContext` and pass it from AI endpoint `ProjectAccess` when building the context
- [x] Wire `check_tool_policy` into `executor.py` before tool execution and before destructive approval branching
- [x] On `deny` Ã¢â€ â€™ return explicit tool-result error to the LLM (no execution)
- [x] On `allow_with_approval` Ã¢â€ â€™ reuse existing `_wait_for_tool_approval` mechanism
- [x] Add default policy config (viewer=read+UI only, member=read+write+UI, manager/owner=all)
- [x] Tests: viewer blocked from write tools, member allowed writes, deny on unknown tool, scope violation returns deny, destructive tools still require per-action approval

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Policy is implemented as a pure service-layer decision function and keeps destructive approval as a second gate.
  - Scope validation is object-level and project-scoped for task/dependency/resource/assignment references.

---

### AGT-02 Ã¢â‚¬â€ Agent kill switch: per-project and per-org flag to disable agent execution

Status: `DONE`

#### Mini-tasks

- [x] Add `agent_enabled` boolean to project settings JSON schema (default: true when missing)
- [x] Add `agent_enabled` boolean to organization settings JSON schema (default: true when missing)
- [x] Check both flags at `prepare_chat_stream` entry Ã¢â‚¬â€ reject with clear `InvalidOperationError` if either is false
- [x] Org-level false overrides project-level true (org wins)
- [x] Apply same kill-switch guard in proactive agent monitor flow before analysis execution
- [x] Frontend: add "AI Agent" toggle in project settings page
- [x] Frontend: when agent is disabled, show disabled AI panel state with explanation and block chat input/actions
- [x] Frontend transport: surface backend `error.message` for non-OK AI chat responses instead of status-only errors
- [x] Tests: chat rejected when project flag false, chat rejected when org flag false, chat works when both true, proactive monitor skips disabled projects
- [x] Tests: proactive monitor imports public `agent.utils` API (`read_user_ai_preferences`, `resolve_effective_provider_model`) and still resolves provider/model + API key correctly

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Kill switch stays in JSON settings (no migration/column changes).
  - Defaults are permissive when keys are missing (`true`) for backward compatibility.

---

## Previous Sprint Items Ã¢â‚¬â€ S10

### UX-01 Ã¢â‚¬â€ Invitation flow blockers + recovery

Status: `DONE`

#### Mini-tasks

- [x] Fix invalid invitation dead-end copy and add explicit "Back to dashboard" recovery CTA
- [x] Update invitation page loading state with spinner + `aria-live="polite"` and user-facing wording
- [x] Add invitation-page error `role="alert"` and vertically center invitation card states
- [x] Replace misleading review-mode "Back" behavior with actual back navigation or explicit "Cancel"
- [x] Add focused tests for invalid token/missing payload/review-mode navigation states

#### Notes

- Dependencies: FIX-14
- Blockers: -
- Decisions: Keep invitation token contract unchanged; this sprint is UX-only unless a blocker appears.

---

### UX-02 Ã¢â‚¬â€ Notification center IA + accessibility baseline

Status: `DONE`

#### Mini-tasks

- [x] Move notification settings controls out of bell dropdown into dedicated settings destination
- [x] Add explicit notification settings entry-point link from the dropdown
- [x] Normalize bell and notification action hit targets to mobile-safe minimums
- [x] Add screen-reader labels for unread counts and per-notification read actions
- [x] Rename ambiguous copy ("Read", "Review", websocket status labels) to user-facing language

#### Notes

- Dependencies: UX-01
- Blockers: Destination route for notification settings if `/settings/notifications` is not ready
- Decisions: Keep notification feed focused on triage actions only.

---

### UX-03 Ã¢â‚¬â€ Membership actions safety + copy clarity

Status: `DONE`

#### Mini-tasks

- [x] Add role-change confirmation or undo affordance before finalizing member role mutations
- [x] Improve member-removal confirmation title to include affected member name
- [x] Remove or rewrite decorative/unclear labels (for example "Access list")
- [x] Add accessible header labeling for actions column in members table
- [x] Verify role/action buttons keep consistent min sizes and copy semantics

#### Notes

- Dependencies: FIX-08
- Blockers: -
- Decisions: Prefer undo flow where fast/low-risk; use confirm dialog for destructive actions.

---

### UX-04 Ã¢â‚¬â€ Profile settings usability batch

Status: `DONE`

#### Mini-tasks

- [x] Disable profile save button when form is pristine, with clear state cue
- [x] Show password requirements before submit; align validation message wording
- [x] Add avatar update success feedback and avatar delete confirmation
- [x] Group AI tool toggles by intent with section labels
- [x] Replace technical wording (for example "Locale") with user-facing labels

#### Notes

- Dependencies: FIX-04, FIX-05
- Blockers: -
- Decisions: Keep this batch in existing profile page architecture; no route split in this sprint.

---

### FIX-17 Ã¢â‚¬â€ AI service mock-provider tests fail in live mode (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_estimate_for_project_with_mock_provider`
- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_suggestions_for_project_with_mock_provider`
- [x] Verify all 17 ai_service tests pass without live AI service

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fake payloads match `AIEstimateItem` and `AISuggestionItem` schemas exactly; same pattern as existing mocked tests.

---

### UX-05 Ã¢â‚¬â€ Visual consistency polish pass (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Normalize non-standard tiny text values to design-scale tokens
- [x] Unify spacing rhythm in profile/member pages
- [x] Rationalize badge/stat opacity and color usage
- [x] Ensure notification dropdown width is responsive on narrow screens

#### Notes

- Dependencies: UX-01, UX-02, UX-03, UX-04
- Blockers: -
- Decisions: Pull in only after committed items pass review.

---

## Previous Sprint Items Ã¢â‚¬â€ S09

### FIX-14 Ã¢â‚¬â€ Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line Ã¢â‚¬â€ keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page Ã¢â‚¬â€ review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page Ã¢â‚¬â€ auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page Ã¢â‚¬â€ fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page Ã¢â‚¬â€ after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 Ã¢â‚¬â€ route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 Ã¢â‚¬â€ Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 Ã¢â‚¬â€ Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S11
**Dates:** 2026-03-27 -> 2026-03-29
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S11

### FEAT-01 Ã¢â‚¬â€ Percent-driven status: derive task status from percent_complete with configurable review threshold

Status: `DONE`

#### Mini-tasks

- [x] Add `status_thresholds` schema to project settings (default: `{ "IN_PROGRESS": 1, "IN_REVIEW": 80, "DONE": 100 }`)
- [x] Write `derive_status_from_percent(percent_complete, thresholds, current_status)` utility in `task_service.py` Ã¢â‚¬â€ returns derived `TaskStatus`; preserves BACKLOGÃ¢â€ â€TODO when percent is 0
- [x] Wire derivation into `update_task()` Ã¢â‚¬â€ after `setattr` loop, auto-set `status` when `percent_complete` is in the patch
- [x] Wire reverse: when `status` is in the patch (kanban drag), auto-set `percent_complete` to column entry value (TODOÃ¢â€ â€™0, IN_PROGRESSÃ¢â€ â€™1, IN_REVIEWÃ¢â€ â€™threshold, DONEÃ¢â€ â€™100)
- [x] Add Alembic migration to backfill existing tasks: derive status from current percent_complete using default thresholds
- [x] Frontend: update `useKanbanDrag` to send `percent_complete` alongside `status` (or let backend derive)
- [x] Frontend: add review threshold setting to project settings UI (input with default 80%)
- [x] Frontend: expose `status_thresholds` in project settings API call and store
- [x] Tests: backend unit tests for `derive_status_from_percent` Ã¢â‚¬â€ all threshold boundaries, BACKLOGÃ¢â€ â€TODO edge case, reverse direction
- [x] Tests: frontend test for kanban drag setting percent, project settings threshold UI

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - BACKLOGÃ¢â€ â€TODO is manual-only (both are 0% Ã¢â‚¬â€ the difference is intent, not progress)
  - Once percent > 0, status auto-jumps to IN_PROGRESS regardless of prior BACKLOG/TODO
  - If percent drops back to 0, status returns to TODO (not BACKLOG Ã¢â‚¬â€ task was acknowledged)
  - Kanban drag to a column sets percent to that column's entry threshold
  - Default thresholds: IN_PROGRESS=1%, IN_REVIEW=80%, DONE=100%

---

### FEAT-02 Ã¢â‚¬â€ Percent-driven status: summary task status auto-derived from rolled-up percent

Status: `DONE`

#### Mini-tasks

- [x] Wire `derive_status_from_percent` into `recalculate_summary()` Ã¢â‚¬â€ after computing rolled-up percent via `apply_summary_rollup`, derive and set status
- [x] Load project `status_thresholds` in `recalculate_summary()` and apply to rollup
- [x] Tests: summary task status transitions when children reach threshold boundaries
- [x] Tests: summary task status resets to TODO when children cleared

#### Notes

- Dependencies: FEAT-01
- Blockers: -
- Decisions:
  - Summary tasks never have manually-set status Ã¢â‚¬â€ always derived from rolled-up percent
  - Uses same project-level thresholds as leaf tasks

---

## Draft Items Ã¢â‚¬â€ S12 (Agent Platform Hardening)

### AGT-01 Ã¢â‚¬â€ Agent policy engine: centralized permission and role check before every tool execution

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Define `ToolPolicy` enum (`allow`, `allow_with_approval`, `deny`) and `PolicyDecision` dataclass
- [ ] Create `agent/policy.py` with `check_tool_policy(tool_name, tool_input, ctx) Ã¢â€ â€™ PolicyDecision`
- [ ] Implement action allowlist check Ã¢â‚¬â€ reject unknown tool names
- [ ] Implement role check Ã¢â‚¬â€ map project role (viewer/member/manager/owner) to allowed tool tiers (read/write/destructive/UI)
- [ ] Implement scope check Ã¢â‚¬â€ validate all entity IDs in `tool_input` belong to `ctx.project_id`
- [ ] Wire `check_tool_policy` into `executor.py` before every `execute_tool` call (line 200)
- [ ] On `deny` Ã¢â€ â€™ return error result to LLM ("Permission denied: viewers cannot create tasks")
- [ ] On `allow_with_approval` Ã¢â€ â€™ reuse existing `_wait_for_tool_approval` mechanism
- [ ] Add default policy config (viewer=read+UI only, member=read+write+UI, manager/owner=all)
- [ ] Tests: viewer blocked from write tools, member allowed writes, deny on unknown tool, scope violation returns deny, destructive still requires per-action approval

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Policy is a pure in-memory function Ã¢â‚¬â€ no DB query per tool call (role comes from ctx)
  - Policy is additive to endpoint-level RBAC, not a replacement
  - Default policy is hardcoded; project-level policy customization is future work
  - Scope check validates task_id/dependency_id belong to ctx.project_id by querying existing repo functions

---

### AGT-02 Ã¢â‚¬â€ Agent kill switch: per-project and per-org flag to disable agent execution

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Add `agent_enabled` boolean to project settings JSON schema (default: true)
- [ ] Add `agent_enabled` boolean to organization settings JSON schema (default: true)
- [ ] Check both flags at `prepare_chat_stream` entry Ã¢â‚¬â€ reject with clear `InvalidOperationError` if either is false
- [ ] Org-level false overrides project-level true (org wins)
- [ ] Frontend: add "AI Agent" toggle in project settings page
- [ ] Frontend: when agent is disabled, show disabled state on AI panel entry point with explanation
- [ ] Tests: chat rejected when project flag false, chat rejected when org flag false, chat works when both true

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Kill switch is a project.settings / organization.settings JSON field, not a DB column Ã¢â‚¬â€ no migration needed
  - Check happens once at stream entry, not per-tool (no performance impact)
  - Proactive agent (`agent_monitor.py`) must also check the flag before running health checks

---

### AGT-03 Ã¢â‚¬â€ Agent post-condition verification (Stretch)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Define verification contract: `verify_tool_result(tool_name, tool_input, result, ctx) Ã¢â€ â€™ VerifyOutcome`
- [ ] Implement verifiers for write tools: create_task (ID exists + name matches), update_task (fields match patch), delete_task (is_deleted=true), add_dependency (exists), assign_resource (exists)
- [ ] Skip verification for read and UI tools
- [ ] Wire into executor after `execute_tool` Ã¢â‚¬â€ on mismatch: log warning, return error to LLM, allow 1 retry
- [ ] Tests: successful verification passes through, mismatch triggers retry, second mismatch stops with error

#### Notes

- Dependencies: AGT-01 (policy engine should be in place first)
- Blockers: -
- Decisions:
  - Verification re-queries the DB to confirm the mutation landed Ã¢â‚¬â€ adds one query per write tool
  - Max 1 retry per tool call to prevent loops
  - Verification failures are logged but don't crash the agent run Ã¢â‚¬â€ LLM gets error and can adapt

---

### AGT-04 Ã¢â‚¬â€ Agent UI actions: implement frontend handlers (Stretch)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `highlight_tasks`: receive task IDs from `ui_action` event, update a shared store (or kanban/gantt store) with highlighted IDs, render visual highlight on matching cards/bars
- [ ] `open_task`: receive task ID, open TaskDetailPanel in current view context (kanban or tasks page)
- [ ] `filter_view`: receive filter params (status, assignee, priority), apply to current view's filter state
- [ ] Clear highlights/filters when AI panel closes or new conversation starts
- [ ] Tests: highlight renders on kanban card, open_task opens detail panel, filter applies to task list

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - UI actions modify existing view stores Ã¢â‚¬â€ no new routes or pages
  - highlight_tasks uses a transient `highlightedTaskIds` set in shared state
  - filter_view maps AI filter params to existing filter state shapes per view

---

## Previous Sprint Items Ã¢â‚¬â€ S10

### UX-01 Ã¢â‚¬â€ Invitation flow blockers + recovery

Status: `DONE`

#### Mini-tasks

- [x] Fix invalid invitation dead-end copy and add explicit "Back to dashboard" recovery CTA
- [x] Update invitation page loading state with spinner + `aria-live="polite"` and user-facing wording
- [x] Add invitation-page error `role="alert"` and vertically center invitation card states
- [x] Replace misleading review-mode "Back" behavior with actual back navigation or explicit "Cancel"
- [x] Add focused tests for invalid token/missing payload/review-mode navigation states

#### Notes

- Dependencies: FIX-14
- Blockers: -
- Decisions: Keep invitation token contract unchanged; this sprint is UX-only unless a blocker appears.

---

### UX-02 Ã¢â‚¬â€ Notification center IA + accessibility baseline

Status: `DONE`

#### Mini-tasks

- [x] Move notification settings controls out of bell dropdown into dedicated settings destination
- [x] Add explicit notification settings entry-point link from the dropdown
- [x] Normalize bell and notification action hit targets to mobile-safe minimums
- [x] Add screen-reader labels for unread counts and per-notification read actions
- [x] Rename ambiguous copy ("Read", "Review", websocket status labels) to user-facing language

#### Notes

- Dependencies: UX-01
- Blockers: Destination route for notification settings if `/settings/notifications` is not ready
- Decisions: Keep notification feed focused on triage actions only.

---

### UX-03 Ã¢â‚¬â€ Membership actions safety + copy clarity

Status: `DONE`

#### Mini-tasks

- [x] Add role-change confirmation or undo affordance before finalizing member role mutations
- [x] Improve member-removal confirmation title to include affected member name
- [x] Remove or rewrite decorative/unclear labels (for example "Access list")
- [x] Add accessible header labeling for actions column in members table
- [x] Verify role/action buttons keep consistent min sizes and copy semantics

#### Notes

- Dependencies: FIX-08
- Blockers: -
- Decisions: Prefer undo flow where fast/low-risk; use confirm dialog for destructive actions.

---

### UX-04 Ã¢â‚¬â€ Profile settings usability batch

Status: `DONE`

#### Mini-tasks

- [x] Disable profile save button when form is pristine, with clear state cue
- [x] Show password requirements before submit; align validation message wording
- [x] Add avatar update success feedback and avatar delete confirmation
- [x] Group AI tool toggles by intent with section labels
- [x] Replace technical wording (for example "Locale") with user-facing labels

#### Notes

- Dependencies: FIX-04, FIX-05
- Blockers: -
- Decisions: Keep this batch in existing profile page architecture; no route split in this sprint.

---

### FIX-17 Ã¢â‚¬â€ AI service mock-provider tests fail in live mode (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_estimate_for_project_with_mock_provider`
- [x] Add `fake_complete` monkeypatch for `_complete_from_service` in `test_suggestions_for_project_with_mock_provider`
- [x] Verify all 17 ai_service tests pass without live AI service

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fake payloads match `AIEstimateItem` and `AISuggestionItem` schemas exactly; same pattern as existing mocked tests.

---

### UX-05 Ã¢â‚¬â€ Visual consistency polish pass (Stretch)

Status: `DONE`

#### Mini-tasks

- [x] Normalize non-standard tiny text values to design-scale tokens
- [x] Unify spacing rhythm in profile/member pages
- [x] Rationalize badge/stat opacity and color usage
- [x] Ensure notification dropdown width is responsive on narrow screens

#### Notes

- Dependencies: UX-01, UX-02, UX-03, UX-04
- Blockers: -
- Decisions: Pull in only after committed items pass review.

---

## Previous Sprint Items Ã¢â‚¬â€ S09

### FIX-14 Ã¢â‚¬â€ Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line Ã¢â‚¬â€ keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page Ã¢â‚¬â€ review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page Ã¢â‚¬â€ auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page Ã¢â‚¬â€ fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page Ã¢â‚¬â€ after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 Ã¢â‚¬â€ route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 Ã¢â‚¬â€ Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 Ã¢â‚¬â€ Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items Ã¢â‚¬â€ S08

### FIX-09 Ã¢â‚¬â€ Finalize Vite WS proxy fix (#39)

Status: `DONE`

#### Mini-tasks

- [x] Verify `ws: true` is present in `frontend/vite.config.ts` proxy for `/api`
- [x] Keep the verified proxy change in the working tree for the current sprint fix pass
- [x] Cover the downstream WebSocket behavior with focused frontend websocket-hook tests

#### Notes

- File: `frontend/vite.config.ts`
- Already applied in working tree before this sprint execution; verified and retained
- This unblocks all realtime features (notifications push, presence, live updates)

---

### FIX-10 Ã¢â‚¬â€ Project invite accept page stuck on "Accepting invitation..." (#35)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the accept page was relying on transient mutation state and could get stuck after the backend returned success
- [x] Make the accept page render from resolved invitation result state instead of the raw mutation status flags
- [x] Preserve a single in-flight accept request/result per token so the page survives dev remounts and renders the "Open Project" success state
- [x] Keep the success card after acceptance; on `Go to Project`, resolve the invited project's organization, switch the active org context, and navigate into the project
- [x] Route bell notifications for existing org-member invites into the same acceptance page by invitation id
- [x] Verify the flow with focused frontend coverage for success, error, and missing-token paths

#### Notes

- Files: `frontend/src/features/projects/pages/ProjectInvitationAcceptPage.tsx`, `frontend/src/features/projects/hooks/useProjectMembers.ts`, `frontend/src/features/projects/api/project-members.service.ts`
- Files also touched for the notification-backed path: `backend/app/service/project_member_service.py`, `backend/app/repository/project_member_repo.py`, `backend/app/schema/project_member.py`, `frontend/src/shared/layout/AppHeader.tsx`
- Backend accept endpoint: `POST /api/v1/projects/members/invitations/accept` now accepts either `token` or `invitation_id`
- Existing organization members get both the email invite and a user-scoped `invitation_received` bell notification; users outside the org still get email only

---

### FIX-11 Ã¢â‚¬â€ Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` Ã¢â‚¬â€ find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 Ã¢â‚¬â€ Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically Ã¢â‚¬â€ don't mask other errors

---

### FIX-13 Ã¢â‚¬â€ WebSocket hooks unstable effect dependencies (#40)

Status: `DONE`

#### Mini-tasks

- [x] In `useProjectWebSocket.ts`, move store actions plus `navigate`/`queryClient` access behind refs
- [x] Remove unstable non-input references from the effect dependency array so the hook only reconnects when project/auth inputs actually change
- [x] Apply the same stabilization pattern to `useNotificationWebSocket.ts`
- [x] Verify the stable-connection behavior with focused rerender coverage for both websocket hooks

#### Notes

- Files: `frontend/src/features/projects/hooks/useProjectWebSocket.ts`, `frontend/src/features/notifications/hooks/useNotificationWebSocket.ts`
- The pattern: `const setStatusRef = useRef(setStatus); setStatusRef.current = setStatus;` then use `setStatusRef.current(...)` inside the effect
- Also move `navigate` and `queryClient` into refs if they appear in deps and cause re-runs

---

## Previous Sprint Items Ã¢â‚¬â€ S07

### FIX-01 Ã¢â‚¬â€ Avatar upload crashes with raw Pydantic error (#27)

Status: `DONE`

#### Mini-tasks

- [x] Find the avatar upload mutation error handler in `ProfilePage.tsx`
- [x] Fix avatar upload transport so the frontend sends real `multipart/form-data`
- [x] Wrap upload failure with `getErrorMessage()` and show via `toast.error()`
- [x] Ensure returned avatar media URLs resolve in local dev and render in both profile and sidebar UI

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/shared/api/api.ts`, `frontend/vite.config.ts`, `frontend/src/shared/layout/NavUser.tsx`
- The error object `{type, loc, msg, input}` is a raw Pydantic 422 response being rendered as a React child
- Root cause was broader than the original crash: the shared API client was forcing `application/json` on `FormData`, Vite was not proxying `/media`, and the sidebar user menu never rendered `AvatarImage`

---

### FIX-02 Ã¢â‚¬â€ Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete Ã¢â‚¬â€ confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug Ã¢â‚¬â€ succeeds

#### Notes

- Model: `backend/app/models/organization.py` Ã¢â‚¬â€ `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` Ã¢â‚¬â€ `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 Ã¢â‚¬â€ Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org Ã¢â€ â€™ app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 Ã¢â‚¬â€ Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 Ã¢â‚¬â€ AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S06
**Dates:** 2026-04-08 -> 2026-04-21
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S06

### KB-09 Ã¢â‚¬â€ Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar Ã¢â‚¬â€ triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` Ã¢â‚¬â€ use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card Ã¢â‚¬â€ clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes Ã¢â‚¬â€ `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types Ã¢â‚¬â€ `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls Ã¢â‚¬â€ `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component Ã¢â‚¬â€ LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S05
**Dates:** 2026-03-24 -> 2026-04-07
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S05

### KB-02 Ã¢â‚¬â€ Kanban: Card Reordering Within Column (FR-KB-009)

Status: `DONE`

#### Mini-tasks

- [x] Verify current ordering source of truth (task order/index field + API shape) for kanban view
- [x] Define reorder behavior boundaries (within-column reorder only; status changes handled separately)
- [x] Implement drag/drop reorder interactions within a column
- [x] Persist reordered positions to backend and add optimistic rollback on failure
- [x] Ensure reload preserves the same order and does not regress existing status drag behavior
- [x] Add tests for reorder success + failure rollback

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Reuse existing task reorder contract if it can represent kanban order cleanly
  - Avoid introducing one-off ordering abstractions used only by kanban
  - Restrict reorder to cards in the same `parent_task_id` group to avoid implicit hierarchy changes

---

### KB-04 Ã¢â‚¬â€ Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

Status: `DONE`

#### Mini-tasks

- [x] Define lane mode model (`none`/`assignee`/`priority`) and where it lives (kanban store + persisted preference)
- [x] Add toolbar control to switch lane mode
- [x] Render per-column swimlane groups with stable lane ordering and clear headers
- [x] Handle unassigned/unknown bucket explicitly for assignee mode
- [x] Ensure drag/drop still works across lanes and within a lane
- [x] Add tests for lane grouping + drag behavior under lane modes

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep first implementation client-side using already fetched task fields
  - Do not introduce backend grouping endpoints unless profiling proves necessary
  - Persist lane mode per project in `useKanbanStore` (`laneModeByProject`) via local storage
  - Assignee lane uses a deterministic primary assignee (lexicographically smallest name/id); no assignee goes to an explicit `Unassigned` lane
  - Keep one sortable context per column so existing drag/drop behavior remains valid with lane rendering enabled

---

### KB-05 Ã¢â‚¬â€ Kanban: Keyboard Shortcuts (FR-KB-012)

Status: `DONE`

#### Mini-tasks

- [x] Define shortcut map for MVP (`n` quick-add, arrow navigation between cards, Enter to open detail)
- [x] Implement board-focus and roving-focus model for card navigation
- [x] Implement quick-add shortcut targeting the currently focused column
- [x] Guard shortcuts when text inputs or editors are focused
- [x] Add visible shortcut hints in board UI/help tooltip
- [x] Add tests for keyboard navigation and quick-add behaviors

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - Shortcuts are active only when kanban board has focus context
  - Browser/reserved combos are out of scope for this sprint
  - `n` targets the focused card's column; when no card is focused, fallback target is `BACKLOG`
  - Enter opens the currently roving-focused card detail and is ignored while input/editor controls are focused

---

### KB-06 Ã¢â‚¬â€ Kanban: Bulk Select And Move Cards (FR-KB-013)

Status: `DONE`

#### Mini-tasks

- [x] Confirm backend bulk update endpoint/hook support for status updates from kanban
- [x] Add kanban selection mode state (multi-card selection across columns)
- [x] Add toolbar controls for bulk move target and apply action
- [x] Execute bulk status move via existing `PATCH /tasks/bulk` flow with success/error feedback
- [x] Ensure drag interactions are disabled while selection mode is active
- [x] Add/update tests for selection toggling and bulk move behavior

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Reuse existing tasks bulk update API/hook; no backend changes for KB-06
  - Keep selection state local to kanban page (UI state), not persisted
  - Clear selection after successful bulk move; keep only failed IDs selected on partial failure

---

## Previous Sprint Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `DONE`

#### Mini-tasks

- [x] Check if dependency data is available in current task query response
- [x] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [x] Blocked = has predecessor with unfinished status; Blocking = has successor
- [x] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Keep task list API unchanged; load dependency edges via existing `useDependencies(projectId)` query
  - Compute per-task `blockedCount`/`blockingCount` in `KanbanPage` from active dependencies (`is_disabled === false`)
  - `Blocked` count increments only when predecessor task status is not `DONE`
  - Dependency badge click opens the existing task detail panel, which contains the dependency list section

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S04
**Dates:** 2026-03-23 -> 2026-04-06
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S04

### KB-01 Ã¢â‚¬â€ Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel Ã¢â‚¬â€ identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` Ã¢â‚¬â€ mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature Ã¢â‚¬â€ do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 Ã¢â‚¬â€ Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) Ã¢â‚¬â€ write ADR before coding
- [x] Add WIP limit config to kanban store (per-column, per-project)
- [x] Add UI to set limit in column header (input or settings modal)
- [x] Show visual warning on column header when card count exceeds limit
- [x] Persist limit setting across sessions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Store limits in backend project settings (`project.settings.kanban_wip_limits`) for cross-browser/device persistence
  - Keep a local kanban store copy for immediate UI state and optimistic updates

---

### KB-07 Ã¢â‚¬â€ Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` Ã¢â‚¬â€ use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) Ã¢â‚¬â€ avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 Ã¢â‚¬â€ Kanban: Dependency Indicator on Card (FR-KB-015)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Check if dependency data is available in current task query response
- [ ] Add blocked/blocking badge to `KanbanCard` when active dependencies exist
- [ ] Blocked = has predecessor with unfinished status; Blocking = has successor
- [ ] Badge should be visually distinct (e.g. icon + count)

#### Notes

- Dependencies: -
- Blockers: Depends on whether dependency data is included in task list API response
- Decisions: TBD Ã¢â‚¬â€ if not in response, decide whether to add to query or use separate fetch

---

## Previous Sprint Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S03
**Dates:** 2026-03-22 -> 2026-04-05
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S03

### TECH-04-A Ã¢â‚¬â€ Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` Ã¢â‚¬â€ destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` Ã¢â‚¬â€ add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` Ã¢â‚¬â€ add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` Ã¢â‚¬â€ capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) Ã¢â‚¬â€ do not introduce new error UI

---

### TECH-04-B Ã¢â‚¬â€ ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab Ã¢â‚¬â€ render `QueryError` or alert before tool list
- [ ] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` Ã¢â‚¬â€ invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure Ã¢â‚¬â€ surgical fix only

---

### TECH-04-C Ã¢â‚¬â€ Fix `setState` in `useEffect` (#26)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [ ] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` Ã¢â‚¬â€ remove state entirely if possible
- [ ] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D Ã¢â‚¬â€ Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [ ] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [ ] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [ ] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD Ã¢â‚¬â€ must read the hook intent first before committing to either approach

---

### TECH-04-E Ã¢â‚¬â€ Fix Gantt Milestone/Summary Click (#46)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` Ã¢â‚¬â€ keep only `onTaskClick(taskId)`
- [ ] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F Ã¢â‚¬â€ Fix AI Stream Error Event Field Name (#53)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `ai.service.ts` line 104: change `error: "Malformed streaming response"` Ã¢â€ â€™ `message: "Malformed streaming response"`
- [ ] Update corresponding test expectation in `ai.service.test.ts`
- [ ] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` Ã¢â‚¬â€ no contract changes

---

## Previous Sprint Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S02
**Dates:** 2026-03-21 -> 2026-04-04
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items Ã¢â‚¬â€ S02

### TECH-03-A Ã¢â‚¬â€ Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only Ã¢â‚¬â€ do not move the component

---

### TECH-03-B Ã¢â‚¬â€ Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` Ã¢â‚¬â€ wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies Ã¢â‚¬â€ that's a separate refactor; just remove the dead export

---

### TECH-03-C Ã¢â‚¬â€ Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only Ã¢â‚¬â€ do not touch production code

---

### TECH-03-D Ã¢â‚¬â€ Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache Ã¢â‚¬â€ verify no stale cache issues after rename

---

### TECH-03-E Ã¢â‚¬â€ Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` Ã¢â‚¬â€ import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` Ã¢â‚¬â€ import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components Ã¢â‚¬â€ import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket Ã¢â‚¬â€ import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` Ã¢â‚¬â€ import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` Ã¢â‚¬â€ import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` Ã¢â‚¬â€ import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` Ã¢â‚¬â€ import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` Ã¢â‚¬â€ fix all cross-feature internal imports
- [x] #52: AI feature Ã¢â‚¬â€ import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook Ã¢â‚¬â€ import auth through `@/features/auth` barrel
- [x] #55: Resources Ã¢â‚¬â€ replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing Ã¢â‚¬â€ add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items Ã¢â‚¬â€ S01

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
Ã¯Â»Â¿# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S01
**Dates:** 2026-03-21 -> 2026-04-04
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Template (copy per item)

### ITEM-ID - Item title

Status: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `DONE`

#### Mini-tasks

- [ ] Clarify acceptance criteria (requirements + design check)
- [ ] Backend implementation
- [ ] Frontend implementation
- [ ] Unit/integration tests
- [ ] Manual verification
- [ ] Update `requirements-traceability.md`
- [ ] Update requirements status (`DONE`/`PARTIAL`/`PENDING`)

#### Notes

- Dependencies:
- Blockers:
- Decisions:

---

## Active Items

### TECH-01 Ã¢â‚¬â€ Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` Ã¢â‚¬â€ capture all type errors
- [x] Run `cd frontend && npx eslint src/` Ã¢â‚¬â€ capture all lint violations
- [x] Run `cd frontend && npm test -- --run` Ã¢â‚¬â€ capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 Ã¢â‚¬â€ Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` Ã¢â‚¬â€ run /frontend-feature-audit shared
- [x] `auth` Ã¢â‚¬â€ run /frontend-feature-audit auth
- [x] `tasks` Ã¢â‚¬â€ run /frontend-feature-audit tasks
- [x] `projects` Ã¢â‚¬â€ run /frontend-feature-audit projects
- [x] `organizations` Ã¢â‚¬â€ run /frontend-feature-audit organizations
- [x] `kanban` Ã¢â‚¬â€ run /frontend-feature-audit kanban
- [x] `gantt` Ã¢â‚¬â€ run /frontend-feature-audit gantt
- [x] `dashboard` Ã¢â‚¬â€ run /frontend-feature-audit dashboard
- [x] `calendar` Ã¢â‚¬â€ run /frontend-feature-audit calendar
- [x] `ai` Ã¢â‚¬â€ run /frontend-feature-audit ai
- [x] `notifications` Ã¢â‚¬â€ run /frontend-feature-audit notifications
- [x] `resources` Ã¢â‚¬â€ run /frontend-feature-audit resources
- [x] `reports` Ã¢â‚¬â€ run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** Ã¢â‚¬â€ prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
