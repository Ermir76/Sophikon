# Sprint Plan

Purpose: define one sprint commitment with capacity, scope, and completion criteria.

---

## S16 — Bug fixes + agent tooling + prompt caching

**Goal:** Fix two S14 search bugs (index mismatch, stale cache), give the agent proper subtask drill-down tooling, and wire prompt caching end-to-end through all three AI providers.

### Scope

- In scope: backend search expression fix, frontend search cache invalidation, agent `get_tasks` parent filter + `search_tasks` response enrichment, prompt caching wiring through brain_service to Anthropic/OpenAI/Gemini providers.
- Out of scope: new agent tools beyond parent filtering, new search features, provider-side caching policy tuning.

### Design Decisions (Approved)

1. **FIX-18**: Change `task_repo.py` search expression from `concat_ws()` to `coalesce() || coalesce()` to match the GIN index expression character-for-character.
2. **FIX-19**: Add `taskKeys.searches()` invalidation to all 9 task mutation `onSuccess` callbacks in `useTasks.ts`.
3. **AGT-08 — Agent subtask drill-down**:
   - Add `parent_task_id` optional filter param to `get_tasks` tool — returns only direct children of the specified task.
   - Add `is_summary` field to `search_tasks` response — agent knows immediately if a hit has children.
   - Update tool descriptions in `tool_registry.py` so the agent learns the drill-down pattern.
4. **AGT-07 — Prompt caching last-mile**:
   - Forward `prompt_cache` from `brain_service.py` to all provider functions.
   - Anthropic: convert system prompt to content block list with `cache_control: {"type": "ephemeral"}`.
   - OpenAI: structure system message for automatic caching eligibility.
   - Gemini: apply cache config via `GenerateContentConfig`.
   - Update `test_brain_service.py` assertion to verify passthrough.

---

## S15 — Settings consolidation

**Goal:** Replace the split-brain `/profile` + `/settings` + `/members` routes with a single `/settings` destination using a 3-column layout (app sidebar unchanged, anchor nav column, scrollable content). Consolidates Profile, Security, Notifications, AI Preferences, Org General, Members, and Billing into one place.

### Scope

- In scope: new `features/settings/` feature folder (SettingsPage, 3-column layout, SettingsAnchorNav, 7 section components), route consolidation in `App.tsx`, NavUser footer redesign, AppSidebar global nav cleanup, AppHeader notification link update, Notifications section (new UI using existing hooks).
- Out of scope: no new backend endpoints, no schema changes, no new `shared/ui` primitives.

### Design Decisions (Approved)

1. **Route consolidation**: `/settings` is the single settings destination. `/profile` and `/members` become `<Navigate>` redirects to `/settings`. `/settings` no longer requires `OrgGuard` at the route level.
2. **Layout pattern**: 3 columns — app sidebar (unchanged) | sticky anchor nav column | scrollable content. No sidebar inside settings. Claude.ai pattern.
3. **Feature location**: new `features/settings/` folder. Spans auth + org concerns, owned by neither.
4. **Anchor nav sections**: Profile · Security · Notifications · AI Preferences · General · Members · Billing
5. **NavUser footer**: Settings button (direct click to `/settings`) stacked above the avatar row. Avatar row dropdown trimmed to Theme + Logout only. "Profile" item removed entirely.
6. **AppSidebar**: `Members` and `Settings` items removed from `globalNavItems`. Sidebar `defaultOpen={false}`.
7. **Notifications section**: implement using existing `useNotificationSettings` / `useUpdateNotificationSettings` hooks — no new backend work.
8. **Section content sources**: Profile, Security, AI Preferences extracted from `ProfilePage`. General extracted from `OrgSettingsPage`. Members extracted from `OrgMembersPage`. Source pages deleted after extraction (routes redirect away).
9. **OrgGuard replacement**: General and Members sections read `activeOrgId` from `useOrgStore` and render a graceful empty state when null. This also handles org switcher mid-session.
10. **Role-based visibility**: General and Members anchor nav items hidden for non-admin/non-owner roles. Replicate the `isAdminOrOwner` check from `AppSidebar`.
11. **Mobile**: anchor nav becomes a sticky horizontal pill bar at `< 768px`.
12. **Active section tracking**: `IntersectionObserver` drives the highlighted anchor nav item as user scrolls.

### Execution Update

- UX-08: `DONE` (single `/settings` destination shipped with consolidated sections, nav/app wiring cleanup, legacy page removal, and focused frontend regression coverage).
- QA Gate: `GO` (targeted frontend tests passed for `SettingsPage`, `NotificationsSection`, and `AppHeader`).
- Progress: `1/1` committed S15 items complete.

---

## S14 — Task search + agent foundation

**Goal:** Replace fake in-memory task search with DB-level search exposed to UI and agent tools, then harden the agent foundation with versioned system prompts, normalized tool catalog usage, and prompt-caching hooks.

### Scope

- In scope: backend task search endpoint + query path, frontend search integration, agent `search_tasks` rewrite, prompt/tooling foundation work.
- Out of scope: new multi-agent orchestration, large ai-service provider rewrites.

### Design Decisions (Approved)

1. **Search endpoint contract**
   - `GET /projects/{project_id}/tasks/search`
   - `q` is required and must be non-empty after trim.
   - Empty `q` returns `400 VALIDATION_ERROR` (no fallback-to-recent behavior).
2. **Filter semantics**
   - `status` accepts model-level values only: `BACKLOG | TODO | IN_PROGRESS | IN_REVIEW | DONE`.
   - Derived deadline filter is separate: `overdue_only` boolean.
3. **Parent-task filter naming**
   - Use `include_parents` (not `include_summary`) to avoid ambiguity.
4. **Search return contract (v1)**
   - Limit-only search for now, no offset/cursor pagination.
   - Repository/service return list-only (no total count in v1 contract).
5. **Prompt versioning**
   - Introduce `PROMPT_VERSION = "1"` in the agent prompt module.
   - Persist/log prompt version with each conversation run for traceability.

### Backend Plan

- Add DB-level search query in repository (PostgreSQL full-text on active tasks).
- Add search service function and API endpoint wiring (`api -> service -> repository`).
- Add index + migration for search performance.
- Rewire agent `search_tasks` tool to call search service instead of loading `list_tasks(..., per_page=250)` and filtering in Python.

### Frontend Plan

- Add task search API client method and query hook with debounced input.
- Replace local/in-memory filtering with backend search results.
- Keep explicit loading/empty/error states.

### Agent Foundation Plan

- Replace minimal system prompt with structured versioned prompt module.
- Keep single source for tool schemas and route planner/executor through that catalog.
- Add optional prompt-caching metadata path in backend->ai-service complete request (backward-compatible if provider ignores hints).

### Risks and Mitigation

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Search quality mismatch on short queries | Irrelevant results | FTS ranking + normalized query parsing + UI debounce | wwwer |
| Search latency on large projects | Slow chat/UI search | Add GIN index and hard limit defaults | wwwer |
| Prompt changes regress agent behavior | Lower answer quality | Versioned prompt + rollout validation against existing flows | wwwer |
| Contract drift between backend and ai-service | Runtime failures | Update both request contract models in same change set | wwwer |

### Execution Update

- FIX-20: `DONE` (remember-me is now a real login/session policy, carried through refresh-token rotation with a persistence flag plus migration support; verify-email recovery now surfaces resend failures inline; focused backend/frontend auth tests passed and review gate closed `PASS`).
- AGT-05: `DONE` (DB-level `/tasks/search` endpoint + repository full-text search + GIN index migration + agent `search_tasks` rewrite + frontend debounced search integration shipped).
- AGT-06: `DONE` (versioned prompts, shared planner/executor tool catalog, prompt-cache metadata contracts in backend and ai-service, and prompt metadata traceability persistence completed).
- QA Gate: `GO` (targeted backend suites `tests/unit/api/v1/test_tasks.py`, `tests/unit/service/test_agent_tool_registry.py`, `tests/unit/service/test_agent_executor.py`, `tests/unit/service/test_agent_history.py`, `tests/unit/service/test_agent_loop.py` and targeted ai-service suites `tests/test_brain_service.py`, `tests/test_contracts.py` passed).
- Progress: `2/2` committed S14 items complete, plus unplanned auth hardening fix `FIX-20` delivered and closed.

---

## Current Sprint

**Sprint ID:** S13
**Dates:** 2026-03-28 -> 2026-03-29
**Goal:** AI panel UX overhaul — clean up styling with semantic tokens + unify floating TaskDetailPanel across all views (ADR-010)
**Owner(s):** wwwer

### Capacity

- Estimated effort: `~2 days`
- Planned points capacity: `4`

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| ------- | ----- | ------ | ------- | ------------ | ------------- |
| UX-06 | AI panel styling & layout redesign | 2 | Hardcoded colors (emerald, amber, blue, black/5, white/5, primary/10, card/70) bypass theme; tool call rows create visual noise; message bubbles have unnecessary role labels; status banners use colored stripes instead of icons; overall chat UX feels cluttered | - | All hardcoded colors replaced with semantic tokens; user messages right-aligned bg-muted, AI messages left-aligned no-bg with bot icon; tool call rows are compact muted log lines; status banners use bg-muted + icon differentiation; PlanApprovalCard uses bg-card (no opacity); input area uses design system defaults; ReasoningStep uses bg-muted |
| UX-07 | Unified floating TaskDetailPanel across all views (ADR-010) | 2 | Task detail panel behaves inconsistently: Gantt uses floating + decoupled state, Tasks/Kanban use side sheet + conflated state; floating panel needed alongside AI docked panel | UX-06 | All three views (Tasks, Gantt, Kanban) use `floating` TaskDetailPanel; selection (highlight) decoupled from detail (open panel) via separate state; double-click opens detail on all views; kebab/context menu "View Details" still works; tests updated |

**Total committed points:** `4`

### Execution Update

- UX-06: `DONE` (all hardcoded colors replaced with semantic tokens across 4 AI panel components; message bubbles, tool call rows, status banners, suggestion badges, plan card, reasoning step all restyled; S12 isAgentEnabled logic preserved with updated styling)
- UX-07: `DONE` (Tasks and Kanban now use floating TaskDetailPanel with decoupled selection/detail state; single-click selection + double-click open behavior aligned with Gantt pattern; focused tests updated and passing)
- QA Gate: `GO` (targeted frontend suite passed after KanbanPage expectation updates)
- Progress: `4/4` points complete

### Sprint Review

- Planned points: `4`
- Completed points: `4`
- Carry-over points: `0`
- Main wins: Completed S13 UX-06 + UX-07 with unified floating task-detail interaction across views, preserved alternative openers, and closed QA with updated regression coverage.
- Main misses: -
- Process changes for next sprint: Keep interaction-contract changes and test-expectation updates in the same commit to avoid temporary red CI during review.

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| Styling changes may break existing test snapshots | Test failures | Update affected test assertions after visual changes | wwwer |
| Suggestion severity badges lose color differentiation | Reduced scannability | Use Badge variants (destructive/secondary/outline) instead of raw color classes | wwwer |
| Kanban store shape change (new detailTaskId) | Persisted store may have stale shape | detailTaskId is not persisted (partialize excludes it); no migration needed | wwwer |
| Double-click on touch devices | Touch users can't double-tap reliably | Keep kebab menu and context menu as alternative openers; double-click is desktop enhancement | wwwer |

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
