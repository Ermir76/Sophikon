# Sprint Plan

Purpose: define one sprint commitment with capacity, scope, and completion criteria.

## Current Sprint

**Sprint ID:** S18
**Dates:** 2026-04-03 -> TBD
**Goal:** Fix dashboard audit bugs — resolve all P1 correctness, navigation, and performance issues found across three independent audits so the post-login landing page is reliable and demo-ready.
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2-3 days`
- Planned points capacity: `9`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| DASH-01 | Dashboard bootstrap race — loading vs empty-org indistinguishable on first load | 1 | Three audits flagged this independently; first impression after login is broken | - | `DashboardPage` distinguishes org-hydration-in-progress from genuine no-org state; loading indicator covers the bootstrap gap; focused test protects the guard |
| DASH-03 | Dashboard trend chart timezone shift — dates render as previous day in UTC-negative timezones | 1 | Correctness bug visible to every US-timezone user; one-liner fix | - | Trend tick formatter parses date-only strings without UTC coercion; labels match exact API day in any timezone |
| DASH-06 | Dashboard `date.today()` uses server-local timezone instead of UTC anchor | 1 | Fragile correctness in `resolve_window` and `get_org_dashboard_insights`; easy fix | - | All `date.today()` replaced with `datetime.now(timezone.utc).date()` in insights service; backend tests confirm UTC-safe window resolution |
| DASH-04 | Dashboard activity feed not clickable — items are plain `<li>` despite routing data from backend | 2 | Contradicts the "navigation hub" promise; all three audits flagged it | - | Activity items are clickable links routing to correct project/task/resource pages using `entity_type`, `entity_id`, and `project_id`; test covers click navigation |
| DASH-05 | Dashboard N+1 in overallocation stats — 2N DB queries per load via per-project loop | 2 | Performance degrades with org size; acknowledged in code comment | - | Overallocation stats computed in a single batched query; backend test confirms correct stats for multi-project org |
| DASH-02 | Dashboard KPI cards drill into wrong project — all 4 link to highest-risk project | 2 | Navigation shortcut sends users to wrong context; needs product decision on target | - | Each KPI card links to a correct destination for its metric, or drill-down is removed if no accurate target exists |

**Total committed points:** `9`

### Stretch (Optional)

| Item ID | Title | Trigger to pull in |
| ------- | ----- | ------------------ |
| DASH-08 | Dashboard refresh indicator polish | Pull in if committed items ship early |
| DASH-09 | Dashboard page-level and component-level automated tests | Pull in if stretch capacity remains |

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| DASH-02 requires a product decision on where KPI cards should link | Blocks implementation or results in wrong target | Decide before building: (a) filtered project list, (b) remove drill-down, (c) other | wwwer |
| Bootstrap race fix may interact with org-store hydration timing | Regression in sidebar org switcher | Test org resolution flow end-to-end after fix | wwwer |
| N+1 batch refactor changes query structure in insights_service | Regression in dashboard stats | Run existing backend insight tests plus new batched-query test | wwwer |

### Execution Update

- DASH-01: `DONE` (dashboard bootstrap now distinguishes org-list loading and org-list failure from the no-org empty state; focused page tests cover both branches)
- DASH-03: `DONE` (trend tick rendering now parses date-only buckets as local calendar dates; focused shared-ui test covers the timezone-shift regression)
- DASH-06: `DONE` (dashboard date-only logic now resolves through shared `time_policy` business-day helpers using scoped project/org context instead of ad hoc `date.today()` calls)
- DASH-04: `DONE` (organization dashboard recent activity is now clickable and routes into the related project, task list, or resource page; contract clarified as project-scoped cross-project activity)
- DASH-05: `DONE` (org dashboard over-allocation stats now use batched resource/assignment queries plus a shared aggregation helper; focused backend service coverage added for UUID-normalized matching)
- DASH-02: `DONE` (all org-level KPI cards now drill into `/projects` rather than a guessed single-project context)
- Stretch delivered: `DASH-09` partial (focused dashboard page/component/frontend tests plus backend service tests added during review closeout to prove the changed behavior directly)
- QA Gate: `GO` (targeted frontend dashboard slice and targeted backend dashboard slice both passed after reviewer-requested coverage was added)
- Progress: `9/9` committed points complete

### Sprint Review

- Planned points: `9`
- Completed points: `9`
- Carry-over points: `0`
- Main wins: Closed all dashboard audit findings and finished the branch with direct automated proof for the risky time-window, routing, and batched aggregation changes.
- Main misses: Review surfaced that the first pass did not include enough direct backend/frontend test coverage for the changed dashboard behavior, so closeout took an extra QA-focused pass.
- Process changes for next sprint: When a dashboard or summary layer changes both behavior and aggregation strategy, add the direct service/component tests in the same pass instead of waiting for review to force them.

---

## Previous Sprint

**Sprint ID:** S17
**Dates:** 2026-04-02 -> TBD
**Goal:** Close the remaining manual verification debt from shipped work and fix auth issue `#48` so unverified accounts are governed by a real backend-enforced policy instead of a reminder-only flow.
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2-3 days`
- Planned points capacity: `7`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| QA-01 | Carry forward manual verification sweep for shipped S14/S16 work | 2 | Workboard still has unchecked validation tasks for auth persistence, task search/index behavior, agent subtask drill-down, and ai-service prompt-caching streams; these must move out of stale sprint history and become explicit current work | FIX-18, FIX-19, AGT-07, AGT-08, FIX-20 shipped | Every carried-forward manual check from the workboard has an explicit result recorded (`PASS`, `FAIL`, or follow-up issue created), and no inherited S16 checkbox remains as ambiguous pending debt |
| AUTH-01 | Enforce post-expiry policy for unverified users (`#48`) | 5 | QA confirmed a P0: newly registered users keep full access indefinitely even after verification-link expiry because enforcement exists only at the token/reminder layer | - | Backend defines and enforces an unverified-user access policy after the grace period; auth/session checks block or restrict unverified users per the chosen policy; frontend reflects the enforced state; focused tests cover the policy path |

**Total committed points:** `7`

### Execution Update

- QA-01: `PENDING` (manual verification debt carried forward from the active workboard instead of leaving stale unchecked boxes on a closed sprint block)
- AUTH-01: `DONE` (issue `#48` now enforces a 24-hour verification grace period across login, refresh, `/auth/me`, and representative protected routes; recovery uses public resend plus 6h/12h reminder emails; targeted backend/frontend auth-policy tests passed, while a broader auth test slice still shows an unrelated flaky oauth-state baseline test outside AUTH-01 scope)
- Progress: `5/7` points complete

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Manual checks can sprawl without clear evidence capture | Workboard stays ambiguous and stale | Record each carried-forward check as `PASS`, `FAIL`, or new follow-up issue in the workboard notes | wwwer |
| Auth `#48` requires a product/security policy choice, not just a code patch | Rework or inconsistent enforcement | Lock the grace-period/enforcement rule before implementation and apply it in backend auth/session paths | wwwer |
| Enforcing verification too aggressively may block legitimate sign-up recovery | UX friction and support load | Pair enforcement with clear resend/recovery messaging and test the expired-link path | wwwer |

---

## Previous Sprint

**Sprint ID:** S16
**Dates:** TBD
**Goal:** Bug fixes + agent tooling + prompt caching
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `4`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| FIX-18 | GIN index mismatch | 1 | DB task search shipped with a query/index expression mismatch that could prevent index usage | AGT-05 | Repository search expression matches the migration index expression exactly and search can use the index |
| FIX-19 | Search cache invalidation | 1 | Task mutations left cached search results stale in the UI | AGT-05 | Every task mutation invalidates `taskKeys.searches()` so search results refresh after create/update/delete |
| AGT-08 | Agent subtask drill-down | 1 | Agent could not efficiently move from a summary-task search hit to direct children | AGT-05 | `search_tasks` returns `is_summary`; `get_tasks` accepts `parent_task_id`; tool descriptions document the drill-down pattern |
| AGT-07 | Prompt caching last-mile | 1 | `prompt_cache` metadata reached the ai-service boundary but was dropped before provider calls | AGT-06 | `brain_service.py` passes `prompt_cache` to Anthropic/OpenAI/Gemini providers and tests verify passthrough |

**Total committed points:** `4`

### Execution Update

- FIX-18: `DONE` (search expression updated to match the GIN index expression exactly)
- FIX-19: `DONE` (task search invalidation wired through all task mutations)
- AGT-08: `DONE` (agent drill-down contract shipped with `parent_task_id` and `is_summary`)
- AGT-07: `DONE` (prompt-cache passthrough wired through ai-service providers)
- Stretch delivered: `FIX-20` auth remember-me and verification recovery hardening closed with review gate `PASS`
- Carry-forward: manual verification work moved into `S17` as `QA-01` so `S16` stays closed and historical rather than half-open
- Progress: `4/4` committed S16 items complete

### Sprint Review

- Planned points: `4`
- Completed points: `4`
- Carry-over points: `2` into `S17` (`QA-01` manual verification sweep)
- Main wins: Closed the underlying code changes for search reliability, agent drill-down, prompt caching, and auth remember-me hardening.
- Main misses: Manual validation tasks were left as unchecked residue in the workboard instead of being rolled forward into a new sprint immediately.
- Process changes for next sprint: When a sprint closes, convert any remaining unchecked workboard items into a new pending sprint item instead of leaving them attached to a `DONE` block.

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Search/index fix may still hide runtime issues without manual DB verification | False confidence | Carry manual `EXPLAIN ANALYZE` verification into S17 | wwwer |
| Agent/provider fixes rely on behavior that unit tests do not fully exercise end-to-end | Runtime regression risk | Carry the missing end-to-end/manual checks into S17 | wwwer |

---

## Previous Sprint

**Sprint ID:** S15
**Dates:** 2026-03-30 -> 2026-03-31
**Goal:** Replace the split-brain `/profile` + `/settings` + `/members` routes with a single `/settings` destination using a 3-column layout (app sidebar unchanged, anchor nav column, scrollable content).
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `3`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| UX-08 | Settings consolidation | 3 | Profile, members, notifications, and settings were split across routes and entry points, creating navigation drift and duplicated information architecture | UX-04, UX-02 | `/settings` becomes the single destination with consolidated sections, redirects from `/profile` and `/members`, updated app/nav wiring, and focused regression coverage |

**Total committed points:** `3`

### Execution Update

- UX-08: `DONE` (single `/settings` destination shipped with consolidated sections, nav/app wiring cleanup, legacy page removal, and focused frontend regression coverage)
- QA Gate: `GO` (targeted frontend tests passed for `SettingsPage`, `NotificationsSection`, and `AppHeader`)
- Progress: `3/3` points complete

### Sprint Review

- Planned points: `3`
- Completed points: `3`
- Carry-over points: `0`
- Main wins: Unified settings, profile, members, and notification-settings entry points into one coherent destination.
- Main misses: -
- Process changes for next sprint: Keep route cleanup, navigation updates, and regression assertions in the same closeout pass.

---

## Previous Sprint

**Sprint ID:** S14
**Dates:** 2026-03-30 -> 2026-04-02
**Goal:** Replace fake in-memory task search with DB-level search exposed to UI and agent tools, then harden the agent foundation with versioned system prompts, normalized tool catalog usage, and prompt-caching hooks.
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2-3 days`
- Planned points capacity: `2`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| AGT-05 | Task search + agent search foundation | 1 | Task search in UI and agent flow was still fake/in-memory, limiting scale and correctness | - | DB-level task search endpoint, repository full-text search, search index, frontend integration, and agent `search_tasks` rewrite are all in place |
| AGT-06 | Agent prompt/tooling foundation hardening | 1 | Prompt/tool contract drift between backend and ai-service made agent evolution brittle | - | Versioned prompts, shared tool catalog usage, prompt-cache metadata flow, and traceability persistence are wired end-to-end |

**Total committed points:** `2`

### Execution Update

- AGT-05: `DONE` (DB-level `/tasks/search` endpoint + repository full-text search + GIN index migration + agent `search_tasks` rewrite + frontend debounced search integration shipped)
- AGT-06: `DONE` (versioned prompts, shared planner/executor tool catalog, prompt-cache metadata contracts in backend and ai-service, and prompt metadata traceability persistence completed)
- Stretch delivered: `FIX-20` auth remember-me and verification recovery hardening closed with review gate `PASS`
- QA Gate: `GO` (targeted backend and ai-service suites passed)
- Progress: `2/2` committed S14 items complete

### Sprint Review

- Planned points: `2`
- Completed points: `2`
- Carry-over points: `0`
- Main wins: Landed the real task-search backend path and stabilized the agent prompt/tool contract in the same sprint window.
- Main misses: Manual verification debt was not rolled forward immediately and had to be corrected later.
- Process changes for next sprint: Move any leftover manual checks into a new sprint item immediately instead of leaving them attached to completed blocks.

---

## Previous Sprint

**Sprint ID:** S13
**Dates:** 2026-03-28 -> 2026-03-29
**Goal:** AI panel UX overhaul - clean up styling with semantic tokens and unify floating TaskDetailPanel across all views (ADR-010)
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `4`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| UX-06 | AI panel styling and layout redesign | 2 | Hardcoded colors and noisy tool-call/status presentation made the chat UI feel cluttered and off-system | - | Semantic tokens replace raw colors, message/tool/status presentation is simplified, and panel components align with the design system |
| UX-07 | Unified floating TaskDetailPanel across all views | 2 | Gantt, Tasks, and Kanban had inconsistent detail-panel interaction models | UX-06 | All three views use the floating detail panel with aligned selection/open behavior and updated tests |

**Total committed points:** `4`

### Execution Update

- UX-06: `DONE` (all hardcoded colors replaced with semantic tokens across the AI panel components; message bubbles, tool call rows, status banners, suggestion badges, plan card, and reasoning step were restyled)
- UX-07: `DONE` (Tasks and Kanban now use the floating TaskDetailPanel with decoupled selection/detail state and aligned double-click open behavior)
- QA Gate: `GO` (targeted frontend suite passed after expectation updates)
- Progress: `4/4` points complete

### Sprint Review

- Planned points: `4`
- Completed points: `4`
- Carry-over points: `0`
- Main wins: Completed the AI panel cleanup and aligned task-detail interaction across the major task views.
- Main misses: -
- Process changes for next sprint: Keep interaction-contract changes and related test updates in the same commit to avoid temporary red review states.

---

## Previous Sprint

**Sprint ID:** S12
**Dates:** TBD (after S11)
**Goal:** Agent platform hardening — close safety gaps identified in autonomous-ui-agent-blueprint audit: policy engine, kill switch, post-condition verification, and UI action completion
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2-3 days`
- Planned points capacity: `7`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| AGT-01 | Agent policy engine: centralized permission and role check before every tool execution | 5 | Any project member who can call `/chat` can trigger any write tool — no role-based enforcement at tool level; agent promises safety tiers but only enforces destructive-tier; shipping more autonomy features on a foundation with no policy layer is the "2+5+8 without finishing the equation" problem | - | Centralized `check_tool_policy(tool_name, ctx)` called before every `execute_tool` in executor; policy checks action allowlist, user role (viewer can't write), project-scoped ID ownership; policy returns `allow / allow_with_approval / deny`; denied tools return error to LLM; tests cover viewer-blocked, member-allowed, deny-unknown-tool, scope-violation |
| AGT-02 | Agent kill switch: per-project and per-org flag to disable agent execution | 2 | No way to turn off the agent for a project if it misbehaves or user doesn't want it; basic trust requirement before expanding autonomy | - | `agent_enabled` boolean in `project.settings` (default true); org-level `agent_enabled` in `organization.settings` (default true); `prepare_chat_stream` rejects with `400 INVALID_OPERATION` and clear message if either flag is false; project settings UI exposes toggle; tests cover both flags |

**Total committed points:** `7`

### Execution Update

- AGT-01: `DONE` (policy engine implemented in `agent/policy.py`, wired in executor before tool execution, role + scope + unknown-tool deny paths covered by unit tests)
- AGT-02: `DONE` (project/org `agent_enabled` kill-switch checks enforced in chat + proactive monitor, project settings/UI disable state implemented, focused backend/frontend tests complete)
- QA Gate: `GO` (diff-scoped backend/frontend suites passed after follow-up closures)
- Progress: `7/7` points complete

### Sprint Review

- Planned points: `7`
- Completed points: `7`
- Carry-over points: `0`
- Main wins: Shipped policy engine and kill switch with full SDLC cycle; both agent safety gates wired and tested.
- Main misses: -
- Process changes for next sprint: -

---

## Previous Sprint

**Sprint ID:** S11
**Dates:** 2026-03-27 -> 2026-03-29
**Goal:** Percent-driven status — unify task status as a derived view of percent_complete with configurable review threshold per project
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `7`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| FEAT-01 | Percent-driven status: derive task status from percent_complete with configurable review threshold | 5 | Status and percent_complete are fully independent — kanban, Gantt, and task list can show contradictory state; no competitor unifies these | - | `update_task` auto-derives status from percent using project-level thresholds; kanban drag sets `percent_complete` to column entry value; project settings UI exposes review threshold (default 80%); BACKLOG↔TODO remains manual; Gantt tooltip and task list badge read derived status; tests cover all threshold transitions |
| FEAT-02 | Percent-driven status: summary task status auto-derived from rolled-up percent | 2 | Summary tasks already roll up percent from children but status stays stale | FEAT-01 | `apply_summary_rollup` derives status from rolled-up percent using same thresholds; parent card on kanban auto-moves when children complete; tests cover rollup-driven status transitions |

**Total committed points:** `7`

### Execution Update

- FEAT-01: `DONE` (status/percent derivation, project thresholds, migration backfill, and focused backend/frontend tests complete)
- FEAT-02: `DONE` (summary status derived from rolled-up percent in `recalculate_summary`; unit tests cover all threshold boundaries and clear path)
- Progress: `7/7` points complete

### Stretch (Optional)

| Item ID | Title | Trigger to pull in |
| ------- | ----- | ------------------ |
| FIX-07 | Password reset allows reuse of previous password (#28) | Pull in if FEAT-01 + FEAT-02 ship early |

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Kanban drag now sets percent instead of status — may confuse users who expect direct status control | UX friction, support tickets | Show percent change in card after drop; keep BACKLOG↔TODO as manual override for the 0% edge case | wwwer |
| Existing tasks may have status/percent mismatch after migration | Inconsistent board on first load | Alembic migration backfills status from current percent_complete using default thresholds | wwwer |
| Teams with unusual review workflows may need non-default threshold | Feature feels rigid if only one threshold | Expose threshold in project settings with clear label and sensible default (80%) | wwwer |

---

## Next Sprint (Draft)

**Sprint ID:** S12
**Dates:** TBD (after S11)
**Goal:** Agent platform hardening — close safety gaps identified in autonomous-ui-agent-blueprint audit: policy engine, kill switch, post-condition verification, and UI action completion
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2-3 days`
- Planned points capacity: `7`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| AGT-01 | Agent policy engine: centralized permission and role check before every tool execution | 5 | Any project member who can call `/chat` can trigger any write tool — no role-based enforcement at tool level; agent promises safety tiers but only enforces destructive-tier; shipping more autonomy features on a foundation with no policy layer is the "2+5+8 without finishing the equation" problem | - | Centralized `check_tool_policy(tool_name, ctx)` called before every `execute_tool` in executor; policy checks action allowlist, user role (viewer can't write), project-scoped ID ownership; policy returns `allow / allow_with_approval / deny`; denied tools return error to LLM; tests cover viewer-blocked, member-allowed, deny-unknown-tool, scope-violation |
| AGT-02 | Agent kill switch: per-project and per-org flag to disable agent execution | 2 | No way to turn off the agent for a project if it misbehaves or user doesn't want it; basic trust requirement before expanding autonomy | - | `agent_enabled` boolean in `project.settings` (default true); org-level `agent_enabled` in `organization.settings` (default true); `prepare_chat_stream` rejects with `400 INVALID_OPERATION` and clear message if either flag is false; project settings UI exposes toggle; tests cover both flags |

**Total committed points:** `7`

### Execution Update

- AGT-01: `DONE` (policy engine implemented in `agent/policy.py`, wired in executor before tool execution, role + scope + unknown-tool deny paths covered by unit tests)
- AGT-02: `DONE` (project/org `agent_enabled` kill-switch checks enforced in chat + proactive monitor, project settings/UI disable state implemented, focused backend/frontend tests complete)
- QA Gate: `GO` (diff-scoped backend/frontend suites passed after follow-up closures)
- Progress: `7/7` points complete

### Stretch (Optional)

| Item ID | Title | Trigger to pull in |
| ------- | ----- | ------------------ |
| AGT-03 | Agent post-condition verification: validate tool results match plan intent before continuing | Pull in if AGT-01 + AGT-02 ship early |
| AGT-04 | Agent UI actions: implement highlight_tasks, open_task, filter_view handlers on frontend | Pull in if stretch capacity remains |

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Policy engine adds latency to every tool call | Perceived slowness in agent execution | Keep policy check as a pure in-memory function (role lookup from ctx, no extra DB query); benchmark before/after | wwwer |
| Defining role→tool mapping may conflict with existing endpoint-level RBAC | Duplicate or contradictory permission logic | Policy engine reads the same role that the API layer uses; tool policy is additive (agent-specific restrictions), not a replacement for endpoint RBAC | wwwer |
| Kill switch may confuse users if agent features are visible but disabled | UX friction — user clicks AI chat and gets error | When disabled, hide or grey out AI panel entry point; show clear "AI agent is disabled for this project" message | wwwer |
| Post-condition verification (stretch) requires defining expected outcomes per tool category | Design effort may be larger than estimated | Start with write tools only (verify entity exists after create, verify field changed after update); skip read tools | wwwer |

### Design Notes

**Policy engine architecture:**
```
executor.py → check_tool_policy(tool_name, tool_input, ctx)
                ├─ action_allowlist check (is this tool allowed?)
                ├─ role_check (does user's project role permit this tier?)
                ├─ scope_check (are all IDs in tool_input within ctx.project_id?)
                └─ returns: allow | allow_with_approval | deny
```

**Tool tier → role mapping (default policy):**

| Tool tier | Viewer | Member | Manager | Owner |
|-----------|--------|--------|---------|-------|
| Read | allow | allow | allow | allow |
| UI | allow | allow | allow | allow |
| Write | deny | allow | allow | allow |
| Destructive | deny | deny | allow_with_approval | allow_with_approval |

**Kill switch data model:**
- `project.settings.agent_enabled` (boolean, default true)
- `organization.settings.agent_enabled` (boolean, default true)
- Org-level false overrides project-level true (org wins)
- Check happens once at `prepare_chat_stream` entry — not per-tool

**Post-condition verification (stretch — design sketch):**

| Tool category | Verification |
|---------------|-------------|
| create_task | Returned ID exists and name matches input |
| update_task | Changed fields match patch values |
| delete_task | Task marked as deleted |
| add_dependency | Dependency exists between specified tasks |
| assign_resource | Assignment exists for task+resource pair |
| read tools | Skip (no mutation to verify) |

On mismatch: log warning, return error result to LLM, let LLM decide to retry or escalate. Max 1 retry per tool call.

---

## Previous Sprint

**Sprint ID:** S10
**Dates:** 2026-03-26 -> 2026-03-28
**Goal:** Execute grouped UX remediation from `docs/06-qa/ux-review-2026-03-26.md` with focus on flow blockers, accessibility, and action clarity
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `8`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| UX-01 | Invitation flow blockers + recovery | 2 | P0 UX debt in invitation accept path creates dead-end and unclear loading/error behavior | FIX-14 | Invalid/missing invitation states provide recovery CTA, centered layout, live status text, spinner, and explicit alert semantics; review-mode back action is no longer misleading |
| UX-02 | Notification center IA + accessibility baseline | 2 | Notification panel currently mixes settings and feed actions, with weak a11y affordances | UX-01 | Notification settings moved out of bell feed; bell/read actions meet target sizes and accessible labels; unread count and status updates are screen-reader friendly |
| UX-03 | Membership actions safety + copy clarity | 2 | Role/member actions are high-risk and currently too easy to misfire or misread | FIX-08 | Role changes have confirmation or undo; destructive actions use explicit entity-focused copy; action labels are unambiguous in members and notifications |
| UX-04 | Profile settings usability batch | 2 | Profile page has clustered medium/high friction (save-state ambiguity, password guidance, ungrouped AI toggles) | FIX-04, FIX-05 | Save button reflects dirty state, password requirements are visible before submit, AI toggles are grouped by intent, and account/settings labels use user-facing language |

**Total committed points:** `8`

### Stretch (Optional)

| Item ID | Title | Trigger to pull in |
| ------- | ----- | ------------------ |
| UX-05 | Visual consistency polish pass (type scale, spacing, badge/opacity normalization) | Pull in only if UX-01..UX-04 are completed and reviewed |
| FIX-15 | Blocking sync file I/O in async handlers — avatars + attachments (#42) | Pull in if stretch capacity remains after UX-05 |
| FIX-16 | AI preferences update bypasses service layer (#43) | Pull in if stretch capacity remains after UX-05 |
| FIX-17 | AI service mock-provider tests fail in live mode — need to mock _complete_from_service | Pull in first — blocks git push |

### Sprint Review

- Planned points: `8`
- Completed points: `11`
- Carry-over points: `0`
- Main wins: Closed all four committed UX batches (`UX-01..UX-04`) and both stretch items (`UX-05`, `FIX-17`) with focused test coverage and frontend visual/accessibility cleanup in invitation, notifications, members, and profile flows.
- Main misses: Local pre-commit in `main` currently runs `ProfilePage.test.tsx` with baseline failures unrelated to S10 doc-sync scope, which added friction to final merge choreography.
- Process changes for next sprint: Finish closeout by syncing `workboard`, `sprint-plan`, and `backlog` in the same pass before final handoff to avoid status drift.

---

---

## Previous Sprint

**Sprint ID:** S08
**Dates:** 2026-03-25 -> 2026-03-25
**Goal:** QA fix pass #2 — close Project Management and WebSocket issues found during QA domains 3–4
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 hours`
- Planned points capacity: `5`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| FIX-09 | Finalize Vite WS proxy fix (#39) | 1 | ❌ Already applied in working tree, needs sprint verification | — | `ws: true` retained in `frontend/vite.config.ts`; focused websocket-hook coverage passes against the dev-proxy configuration |
| FIX-10 | Project invite accept page stuck on "Accepting invitation..." (#35) | 1 | ❌ Accept succeeds server-side but UI never shows success | — | Accept page transitions to success state with "Open Project" button after backend returns 200 |
| FIX-11 | Org switcher not updated after project invite accept (#36) | 1 | ⚠️ User must refresh to see new org | FIX-10 | Org list refetches automatically after invite accept; new org appears in switcher without refresh |
| FIX-12 | Removed project member sees generic error (#37) | 1 | ⚠️ User sees raw error instead of explanation | — | Non-member navigating to project URL sees clear "no access" message or redirect with toast |
| FIX-13 | WebSocket hooks unstable effect dependencies (#40) | 1 | ⚠️ Double-connect on every page load, console warnings | — | WS hooks connect once per project/page; no "closed before established" console warnings |

**Total committed points:** `5`

### Sprint Review

- Planned points: `5`
- Completed points: `5`
- Carry-over points: `0`
- Main wins: Closed all five S08 QA fixes in one frontend pass: the Vite `/api` proxy now explicitly keeps WebSocket upgrades enabled, project invite acceptance renders a stable success state and switches into the invited organization when the user clicks `Go to Project`, org-switcher data invalidates immediately after invite acceptance, removed members now see a clear no-access state instead of a generic error, both websocket hooks were hardened to avoid reconnect churn from unstable effect dependencies, and existing organization members now also receive a bell notification for new project invites that routes into the same accept flow.
- Main misses: End-to-end browser verification through Mailpit/devtools was not run in this session; verification evidence is the focused Vitest coverage for the changed flows and hooks.
- Process changes for next sprint: When a sprint item says "commit" but the user did not ask for commit finalization, normalize the sprint wording to the actual requested deliverable and keep `/cc` explicitly opt-in.

---

---

## Previous Sprint

**Sprint ID:** S07
**Dates:** 2026-03-24 -> 2026-03-24
**Goal:** QA bug fixes — close confirmed ❌ bugs found in Authentication and Organizations QA pass
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 hours`
- Planned points capacity: `3`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| FIX-01 | Avatar upload crashes with raw Pydantic error in UI (#27) | 1 | ❌ Confirmed crash | — | Upload succeeds end-to-end; avatar renders from returned media URL; on failure error shown via `getErrorMessage()` + toast |
| FIX-02 | Deleted org slug not released (#31) | 1 | ❌ Confirmed bug — blocks org slug reuse | — | After deletion, the same slug can be reused immediately |
| FIX-03 | Sidebar no fallback after org deletion (#32) | 1 | ⚠️ Leaves user in blank broken state | FIX-02 | After deleting active org, app switches to personal org automatically |

**Total committed points:** `3`

### Stretch (Optional)

| Item ID | Title | Trigger to pull in |
| ------- | ----- | ------------------ |
| FIX-04 | Change password missing toast (#29) | Pulled in after committed fixes shipped cleanly |
| FIX-05 | AI preferences toggle glitch (#30) | Pulled in after committed fixes shipped cleanly |

### Sprint Review

- Planned points: `3`
- Completed points: `5`
- Carry-over points: `0`
- Main wins: Fixed the avatar flow end-to-end by sending real multipart uploads, surfacing safe user-facing failures, proxying returned `/media` avatar URLs in local dev, and rendering the uploaded avatar in both profile and sidebar UI; deleting an active organization now falls back to the personal organization automatically; soft-deleted organization slugs can be reused; change-password success now uses the standard Sonner toast; and AI preference toggles now show save confirmation without the switch flash during save.
- Main misses: -
- Process changes for next sprint: Treat schema-level uniqueness bugs as explicit design decisions before accepting a workboard fix at face value; review the matching design doc/ADR state before changing DB constraints.

---

---

## Previous Sprint

**Sprint ID:** S06
**Dates:** 2026-04-08 -> 2026-04-21
**Goal:** Kanban AI risk visibility — sprint health summary with actionable risk surfacing
**Owner(s):** wwwer

### Capacity

- Available focus days: `10`
- Focus factor: `0.6`
- Effective days: `10 * 0.6 = 6`
- Planned points capacity: `7`
- Buffer: `~15%` (1 pt)

### Commitment Rules

1. Do not exceed planned points capacity.
2. Do not commit blocked items.
3. Do not commit items without clear acceptance criteria.

### Committed Items

| Item ID | Title                                                        | Points | Why now                                              | Dependencies | Done criteria                                                                                           |
| ------- | ------------------------------------------------------------ | ------ | ---------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------- |
| KB-09   | Kanban: AI sprint health summary (FR-KB-016)                 | 3      | Only remaining `READY` V1.0 backlog item; unlocks AI-assisted risk triage on the board | KB-01 | Kanban shows AI-generated risk summary with at-risk cards, clear rationale per card, and refresh behavior validated by tests |

**Total committed points:** `3`

### Stretch (Optional)

| Item ID | Title                                         | Points | Trigger to pull in           |
| ------- | --------------------------------------------- | ------ | ---------------------------- |
| -       | -                                             | -      | Pull in only after a new item is marked `READY` in backlog |

### Risks and Blockers

| Risk/Blocker                                                        | Impact                              | Mitigation                                                              | Owner |
| ------------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------- | ----- |
| LLM risk summary quality may be noisy in early implementation        | False positives reduce trust        | Reuse existing structured AI suggestions contract (typed schema + validation) and surface rationale in UI text | wwwer |
| Summary refresh timing may cause stale risk signals                  | PM decisions made on stale board view | Tie summary refresh to explicit user action plus query invalidation events | wwwer |
| AI summary generation latency can degrade board responsiveness       | Perceived slowness in kanban workflow | Keep summary request isolated from core board rendering and show independent loading state | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `3`
- Completed points: `3`
- Carry-over points: `0`
- Main wins: Shipped `KB-09` with manual Sprint Health fetch, grouped HIGH/MEDIUM risk summary, and card-level drill-in to existing task detail panel.
- Main misses:
- Process changes for next sprint: Keep AI summary interactions opt-in (`enabled=false` + explicit refresh) to avoid background fetch noise on board load.

---

---

## Previous Sprint

**Sprint ID:** S05
**Dates:** 2026-03-24 -> 2026-04-07
**Goal:** Kanban execution controls — in-column reorder, swimlanes, and keyboard-first board navigation
**Owner(s):** wwwer

### Committed Items

| Item ID | Title                                                        | Points | Outcome |
| ------- | ------------------------------------------------------------ | ------ | ------- |
| KB-02   | Kanban: card reordering within column (FR-KB-009)            | 2      | DONE    |
| KB-04   | Kanban: swimlanes by assignee/priority (FR-KB-011)           | 3      | DONE    |
| KB-05   | Kanban: keyboard shortcuts (FR-KB-012)                       | 2      | DONE    |
| KB-06   | Kanban: bulk select and move cards (FR-KB-013, stretch)      | 2      | DONE    |

### Sprint Review

- Planned points: `7`
- Completed points: `9`
- Carry-over points: `0`
- Main wins: Shipped all committed S05 items and activated stretch `KB-06` with end-to-end delivery, test coverage, and synchronized planning docs.
- Main misses: -
- Process changes for next sprint: Under-commit when backlog has only one `READY` item and preserve buffer for unplanned review fallout.

---

## Sprint Archive — S04

**Sprint ID:** S04
**Dates:** 2026-03-23 -> 2026-04-06
**Goal:** Kanban enhancement — task detail panel, WIP limits, assignee avatar, dependency indicator
**Owner(s):** wwwer

### Committed Items

| Item ID | Title                                                        | Points | Outcome |
| ------- | ------------------------------------------------------------ | ------ | ------- |
| KB-01   | Kanban: task detail panel from card (FR-KB-008)              | 2      | DONE    |
| KB-03   | Kanban: WIP limits per column (FR-KB-010)                    | 2      | DONE    |
| KB-07   | Kanban: assignee avatar on card (FR-KB-014)                  | 1      | DONE    |
| KB-08   | Kanban: dependency indicator on card (FR-KB-015)             | 1      | DONE    |

### Sprint Review

- Planned points: `6`
- Completed points: `6`
- Carry-over points: `0`
- Main wins: Shipped all four committed S04 items in one session; task detail panel integration and WIP limits persistence closed end-to-end.
- Main misses: -
- Process changes for next sprint: Keep autopilot closure gate strict (REVIEW + SYNC + `/done` before handoff).

---

## Sprint Archive — S03

**Sprint ID:** S03
**Dates:** 2026-03-22 -> 2026-04-05
**Goal:** Fix P2 frontend bugs — missing error states, hook anti-patterns, Gantt UX inconsistency, and AI stream contract mismatch
**Owner(s):** wwwer

### Capacity

- Available focus days: `10`
- Focus factor: `0.6`
- Effective days: `10 * 0.6 = 6`
- Planned points capacity: `7`
- Buffer: `~15%` (1 pt)

### Commitment Rules

1. Do not exceed planned points capacity.
2. Do not commit blocked items.
3. Do not commit items without clear acceptance criteria.

### Committed Items

| Item ID    | Title                                                                                              | Points | Why now                                   | Dependencies | Done criteria                                                                                    |
| ---------- | -------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------ |
| TECH-04-A  | Batch error state fixes — OrgSwitcher, Kanban drag, Calendar exceptions, Resources (#41 #43 #51 #56) | 2      | All trivial 1-liner fixes; same pattern   | -            | `isError` handled with `QueryError`/toast in all 4 locations; no silent failures                |
| TECH-04-B  | ProfilePage AI error state + remove double refetch (#35)                                           | 1      | Misleading UI when API down               | -            | `isError` branch renders error UI; redundant `refetch()` call removed from `handleAiToggle`     |
| TECH-04-C  | Fix `setState` in `useEffect` — CalendarPage + TasksPage (#26)                                    | 1      | ESLint violation; cascade render risk     | -            | `setSelectedCalendarId` and `setIsAddingFirstTask` removed from effect bodies; ESLint passes     |
| TECH-04-D  | Fix `useLayoutEffect` missing deps in `useCollapsedTree` (#30)                                    | 1      | Stale closure across features             | -            | All 5 missing deps added or documented with explicit rationale; ESLint `exhaustive-deps` passes  |
| TECH-04-E  | Fix Gantt milestone/summary click opens detail panel (#46)                                         | 1      | UX inconsistency vs regular task bars     | -            | Single click selects only; `onTaskDoubleClick` removed from `handleChartTaskClick`              |
| TECH-04-F  | Fix AI stream error event field name mismatch (#53)                                                | 1      | Breaks declared event contract            | -            | `ai.service.ts` emits `{ type: "error", message: ... }`; test expectation aligned               |

**Total committed points:** `7`

### Stretch (Optional)

| Item ID | Title | Points | Trigger to pull in |
| ------- | ----- | ------ | ------------------ |
| -       | -     | -      | Pull in if all 6 items ship early |

### Risks and Blockers

| Risk/Blocker                                                   | Impact                        | Mitigation                                                          | Owner |
| -------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------- | ----- |
| `useCollapsedTree` deps fix triggers mount-time re-renders     | Visual regression in tree UIs | Test gantt + task tree views after fix; scope to run-once if needed | wwwer |
| `setState` removal in CalendarPage may need derived state rework | More refactor than expected  | Derive from `calendars[0]?.id` directly; no new state introduced    | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `7`
- Completed points: `7`
- Carry-over points: `0`
- Main wins: All 6 items shipped; TECH-04-D resolved as eslint-disable (mount-only intent confirmed); TECH-04-E was a clean 1-line removal
- Main misses: -
- Process changes for next sprint: -

---

---

## Sprint Archive — S02

**Sprint ID:** S02
**Dates:** 2026-03-21 -> 2026-04-04
**Goal:** Frontend cleanup — remove dead code, fix cross-feature import violations, fix query key namespacing, and repair the failing Gantt test suite
**Owner(s):** wwwer

### Capacity

- Available focus days: `10`
- Focus factor: `0.6`
- Effective days: `10 * 0.6 = 6`
- Planned points capacity: `7`
- Buffer: `~15%` (1 pt)

### Commitment Rules

1. Do not exceed planned points capacity.
2. Do not commit blocked items.
3. Do not commit items without clear acceptance criteria.

### Committed Items

| Item ID   | Title                                                                            | Points | Why now                                   | Dependencies | Done criteria                                                                |
| --------- | -------------------------------------------------------------------------------- | ------ | ----------------------------------------- | ------------ | ---------------------------------------------------------------------------- |
| TECH-03-A | Fix failing Gantt tests (#27)                                                    | 1      | P1 — tests are broken now                 | -            | All 3 Gantt tests pass; TaskDetailPanel exported from tasks barrel           |
| TECH-03-B | Remove dead code (#28 #32 #36 #42 #49)                                           | 2      | Low-risk, high noise-reduction            | -            | Unused imports removed; dead files/exports deleted; login eye button removed |
| TECH-03-C | Fix `any` types in test files (#29)                                              | 1      | Type safety in tests                      | -            | No `any` types remain in test files; tsc passes                              |
| TECH-03-D | Fix query key namespacing + Zustand selectors (#34 #38 #45)                      | 1      | Standards compliance                      | -            | All query keys namespaced by feature; kanban store accessed via selectors    |
| TECH-03-E | ~~Fix cross-feature internal imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)~~ ✅ | 2      | Standards compliance; 1-line fix per file | -            | All 11 files import through public barrel; no internal path imports          |

**Total committed points:** `7`

### Stretch (Optional)

| Item ID   | Title                                              | Points | Trigger to pull in                 |
| --------- | -------------------------------------------------- | ------ | ---------------------------------- |
| TECH-03-F | P2 bug fixes (#26 #30 #35 #41 #43 #46 #51 #53 #56) | TBD    | Pull in if cleanup completes early |

### Risks and Blockers

| Risk/Blocker                                             | Impact                   | Mitigation                                              | Owner |
| -------------------------------------------------------- | ------------------------ | ------------------------------------------------------- | ----- |
| Cross-feature import fixes expose missing barrel exports | Compile errors           | Add missing exports to barrels as part of the fix       | wwwer |
| `any` removal triggers cascading type errors             | More work than estimated | Scope strictly to test files only; skip production code | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `7`
- Completed points: `7`
- Carry-over points: `0`
- Main wins:
- Main misses:
- Process changes for next sprint:

---

---

## Sprint Archive — S01
**Dates:** 2026-03-21 -> 2026-04-04
**Goal:** Complete frontend quality audit — automated tool scan + feature-by-feature standards review — producing a prioritized issue backlog for remediation
**Owner(s):** wwwer

### Capacity

- Available focus days: `10`
- Focus factor: `0.6`
- Effective days: `10 * 0.6 = 6`
- Planned points capacity: `7`
- Buffer: `~15%` (1 pt)

### Commitment Rules

1. Do not exceed planned points capacity.
2. Do not commit blocked items.
3. Do not commit items without clear acceptance criteria.

### Committed Items

| Item ID | Title                     | Points | Why now                                                               | Dependencies     | Done criteria                                                                       |
| ------- | ------------------------- | ------ | --------------------------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------- |
| TECH-01 | Frontend Automated Audit  | 2      | Foundation for all other audit work                                   | -                | tsc + eslint + test results captured; all surviving findings in issues/open_issues/ |
| TECH-02 | Frontend Standards Review | 5      | Identify dead code, standards violations, cross-agent inconsistencies | TECH-01 complete | All 12 features reviewed via /consistency-review; findings triaged into issues/     |

**Total committed points:** `7`

### Stretch (Optional)

| Item ID | Title                    | Points | Trigger to pull in                                         |
| ------- | ------------------------ | ------ | ---------------------------------------------------------- |
| TECH-03 | Frontend Bug Remediation | TBD    | Pull in only if TECH-01+02 finish early and scope is small |

### Risks and Blockers

| Risk/Blocker                    | Impact                  | Mitigation                                                         | Owner |
| ------------------------------- | ----------------------- | ------------------------------------------------------------------ | ----- |
| tsc/eslint finds 50+ violations | Triage time blows out   | Ruthlessly filter: dismissed_issues + roadmap items don't count    | wwwer |
| Context loss mid-TECH-02        | Review quality degrades | One feature per session, findings committed to issues/ immediately | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `7`
- Completed points: `7`
- Carry-over points: `0`
- Main wins: Full frontend audit complete — tsc, eslint, tests captured; all 13 feature folders reviewed via /consistency-review; confirmed findings written to issues/open_issues/
- Main misses: -
- Process changes for next sprint: -

---

## Sprint History

| Sprint | Dates                    | Planned | Completed | Carry-over | Notes                                                                               |
| ------ | ------------------------ | ------- | --------- | ---------- | ----------------------------------------------------------------------------------- |
| S13    | 2026-03-28 -> 2026-03-29 | 4       | 4         | 0          | AI panel UX overhaul completed: semantic styling refresh + unified floating TaskDetailPanel workflow (single-click select, double-click open) |
| S16    | TBD                      | TBD     | TBD       | TBD        | Added unplanned auth hardening follow-up: real remember-me/session persistence across refresh rotation plus verify-email resend recovery feedback and focused auth coverage. |
| S12    | TBD                      | 7       | 7         | 0          | Agent platform hardening: policy engine + kill switch shipped with full SDLC cycle |
| S11    | 2026-03-27 -> 2026-03-29 | 7       | 7         | 0          | Percent-driven status: derive task status from percent_complete with configurable review threshold |
| S10    | 2026-03-26 -> 2026-03-28 | 8       | 11        | 0          | Shipped UX remediation groups `UX-01..UX-04` plus stretch `UX-05` and `FIX-17`; invitation/notification/member/profile flows were hardened and visual consistency pass completed. |
| S08    | 2026-03-25 -> 2026-03-25 | 5       | 5         | 0          | Closed all five S08 QA fixes: Vite WS proxy, invite accept page, org switcher invalidation, removed-member error state, and WebSocket hook stabilization |
| S07    | 2026-03-24 -> 2026-03-24 | 3       | 5         | 0          | Closed three committed QA fixes plus stretch `FIX-04` and `FIX-05`: avatar upload/render flow, reusable soft-deleted org slugs, personal-org fallback after deleting the active org, password-change success toast, and stable AI preference save feedback |
| S06    | 2026-04-08 -> 2026-04-21 | 3       | 3         | 0          | Shipped KB-09 AI sprint health summary with manual refresh and kanban card drill-in |
| S05    | 2026-03-24 -> 2026-04-07 | 7       | 9         | 0          | Shipped KB-02/KB-04/KB-05 and activated stretch KB-06 with full closeout |
| S04    | 2026-03-23 -> 2026-04-06 | 6       | 6         | 0          | Kanban enhancements — task detail panel, WIP limits, assignee avatar, dependency indicator shipped |
| S03    | 2026-03-22 -> 2026-04-05 | 7       | 7         | 0          | P2 bug fixes — error states, hook anti-patterns, Gantt UX, AI contract              |
| S02    | 2026-03-21 -> 2026-04-04 | 7       | 7         | 0          | Frontend cleanup — dead code, cross-feature imports, query keys, failing tests      |
| S01    | 2026-03-21 -> 2026-04-04 | 7       | 7         | 0          | Frontend audit sprint — full tsc/eslint/test + 13-feature standards review complete |
