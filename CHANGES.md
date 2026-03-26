# Changes Log

All code changes are documented here with explanations before they are applied.

---

## 2026-03-24 - Sprint S07: Authentication and Organization QA Fixes

## 2026-03-25 - Sprint S08: Project Management and Realtime QA Fixes

## 2026-03-25 - Sprint S09: Invitation Review, Auth Idle Refresh, and Org Role UX

## 2026-03-26 - Sprint S10: UX-04 Profile Settings Usability Batch

### UX-04 - Improve account settings clarity and safety in ProfilePage

**What:** Updated `ProfilePage` so `Save Changes` stays disabled until profile fields are modified, with an explicit pristine-state hint. Added password requirement guidance directly under the new-password field before submission. Added success feedback for avatar upload/removal and introduced a confirmation dialog before avatar deletion. Renamed technical labels (`Locale` to `Language`, `Timezone` to `Time zone`) and updated page header copy to user-facing account-settings wording. Grouped AI auto-approve toggles into intent-based sections (`Task creation and updates`, `Navigation and focus`) while preserving existing optimistic save behavior. Expanded focused `ProfilePage` test coverage for pristine-save state, password guidance visibility, avatar success/confirmation flow, and the grouped UX behaviors.

**Why:** S10 UX-04 targeted profile settings friction where actions looked available when nothing changed, password rules were only discoverable after validation errors, destructive avatar actions lacked explicit confirmation, and technical labels reduced clarity. The update improves user confidence and reduces accidental actions without changing backend contracts.

### FIX-14 / FIX-06 / FIX-08 - Finish invitation review flow and close the remaining related QA regressions

**What:** Finished the project-invitation review flow so bell notifications hide the inline message preview, `Review` opens the accept page in explicit review mode, the page renders the invitation title/message before acceptance, and focused tests now cover review mode, fallback mode, and the notification card behavior. Added a proactive authenticated-app refresh timer so idle sessions renew through `/auth/refresh` before the access token expires instead of dropping users to `/login` after inactivity. Stabilized the organization-members role update UX by showing a fixed row-level saving indicator and freezing role actions while a role change is in flight. On the backend, invitation acceptance now resolves the linked `invitation_received` notification and notification listing/unread counts filter out non-actionable invitation rows, so accepted invites disappear cleanly from the bell and the unread badge stays correct. Added focused backend/frontend coverage for all of the above.

**Why:** The S09 invite UX fix was not actually complete while the review screen still omitted the invitation title and the accepted notification stayed actionable in the bell after the invite was used. The remaining S08 stretch items were also still open: idle users could be bounced to `/login` despite a valid refresh token, and org-role changes showed unstable motion during save instead of a clear pending state. This pass closes those remaining QA regressions as one coherent auth/invite/organization hardening sweep.

### FIX-09 / FIX-13 - Finalize the Vite websocket proxy and stabilize realtime hooks

**What:** Kept the `ws: true` Vite `/api` proxy configuration in place and hardened both `useProjectWebSocket` and `useNotificationWebSocket` so their effects depend only on true input changes. Store actions, navigation, and query-client access now flow through refs inside the hooks, and focused rerender coverage proves they do not create extra websocket connections when the inputs stay the same.

**Why:** The QA pass found two linked realtime problems: local dev was not proxying websocket upgrades through Vite, and the mounted websocket hooks could reconnect unnecessarily because their effects closed over unstable dependencies. Together these issues caused failed realtime behavior and noisy "closed before established" warnings.

---

### FIX-10 / FIX-11 / FIX-12 - Harden invite acceptance and removed-member project access

**What:** Updated `ProjectInvitationAcceptPage` so it renders from resolved invitation result state instead of transient mutation flags, preserves one in-flight accept request/result per invite lookup, and keeps the success card visible after acceptance. The page now accepts either an email-link `token` or a bell-notification `invitation_id`, so existing org members can enter the same acceptance flow from the notification inbox. When the user clicks `Go to Project`, the page resolves the invited project's organization, switches the active org context, shows a toast when the org context changes, and routes into the invited project. If that final project-open step fails, the page stays on the success card and surfaces the lookup failure clearly. `useAcceptProjectInvitation` now invalidates the organizations list on success so the org switcher refreshes without a manual reload. `ProjectLayout` now intercepts project-access 403s and shows a clear "You no longer have access to this project" message with a path back to the projects list. Added focused backend/frontend coverage for invite notifications, invitation acceptance by notification id, the accept page, invite-accept invalidation, project layout access loss, and both websocket hooks.

**Why:** The S08 QA findings showed that project invitation acceptance could succeed server-side while the frontend stayed stuck, the org switcher remained stale until a manual refresh after joining through an invite, and removed project members saw a generic error path instead of an explicit access-loss message. Follow-up UX validation also showed that invites for users already inside the organization should surface in the bell, not email only, and that both entry paths must converge on the same acceptance flow without leaving the user in the wrong org context when opening the accepted project. These fixes close the shipped UX regressions without adding new product scope beyond the missing notification path.

---

### FIX-01 / FIX-02 / FIX-03 - Harden avatar errors and organization delete flows

**What:** Updated `ProfilePage` so avatar upload failures are converted into safe user-facing messages via `toast.error` and inline alert state instead of attempting to render raw validation payloads. Fixed the shared frontend API client so avatar and attachment uploads send real `multipart/form-data` instead of forced JSON, added `/media` proxying in Vite dev so returned avatar URLs resolve locally, and updated `NavUser` to render `AvatarImage` instead of initials-only fallback when `avatar_url` exists. Added focused frontend coverage for the profile crash path. Updated organization slug persistence so soft-deleted organizations no longer reserve the slug forever, aligned repository lookups with active-only organization semantics, and added backend verification for slug reuse after delete. Updated `OrgSettingsPage` so deleting the active organization automatically switches the user back to the personal organization, with focused frontend coverage for the fallback behavior.

**Why:** The QA pass found three confirmed issues in shipped account/organization flows: profile avatar upload could crash the page on 422 responses, deleting an organization permanently reserved its slug despite soft delete, and deleting the active organization left the sidebar/app in a broken no-context state. Follow-up validation also showed that avatar upload had additional transport/render gaps in dev (`application/json` instead of multipart, missing `/media` proxy, and initials-only sidebar rendering). These fixes close the confirmed regressions without expanding product scope.

---

### FIX-04 / FIX-05 - Normalize profile-save feedback for password and AI preferences

**What:** Updated `ProfilePage` so successful password changes use the standard Sonner success toast and still reset the submitted form. Updated the AI preferences toggle flow to show `Preferences saved` on successful mutation and moved the toggle UI to a page-local optimistic state so the switch stays visually stable while the save request is in flight. Added focused `ProfilePage` test coverage for both paths.

**Why:** The Authentication QA pass found two remaining UX issues after the core S07 fixes shipped: change-password success feedback did not match the rest of the application, and AI preference toggles saved silently while briefly flashing during the pending state. These were low-risk polish fixes that fit the sprint stretch window and close the remaining tracked auth UX regressions from that QA pass.

---

## 2026-03-24 - Sprint S06: KB-09 Kanban AI Sprint Health Summary

### KB-09 - Implement FR-KB-016 Risk Summary Surface in Kanban

**What:** Added a new `Sprint Health` control in `KanbanToolbar` that triggers manual `useAiSuggestions` refresh (`enabled=false` + `refetch`) and introduced `KanbanHealthSummary` in `KanbanPage` to render HIGH/MEDIUM risk suggestions grouped by `affected_task_id` with title/description details. Added loading, retryable error, and no-risk states that do not block board interaction. Wired risk-entry clicks to open the existing `TaskDetailPanel` for the affected card and added focused coverage in `KanbanPage`, `KanbanToolbar`, and the new summary component tests.

**Why:** FR-KB-016 requires board-scoped AI risk visibility without forcing background fetches on mount. Manual refresh plus grouped risk context gives PMs actionable triage signals while preserving the existing kanban workflow and task-detail UX.

---

## 2026-03-23 - Sprint S05: KB-06 Kanban Bulk Select and Move

### KB-06 - Implement FR-KB-013 Multi-Card Selection and Bulk Status Move

**What:** Added kanban selection mode with per-card toggle selection, selection count, target-column selector, clear action, and bulk move action in `KanbanToolbar`. Wired selection behavior through `KanbanPage` -> `KanbanBoard` -> `KanbanColumn` -> `KanbanCard`, including selected-card visual state and drag disable while selection mode is active. Reused existing tasks bulk update flow by exporting `useBulkUpdateTasks` through the tasks feature barrel and calling `PATCH /projects/{project_id}/tasks/bulk` with `{ status }` updates for selected cards. Added tests covering toolbar selection controls, page-level selection/bulk-move behavior, and board prop wiring.

**Why:** FR-KB-013 and US-12.8 require fast multi-card status transitions directly in Kanban. Reusing the existing bulk update API minimized scope/risk while preserving existing single-card drag and detail-panel workflows when selection mode is off.

---

## 2026-03-23 - Sprint S05: KB-05 Kanban Keyboard Shortcuts

### KB-05 - Implement FR-KB-012 Keyboard-First Board Controls

**What:** Added board-scoped keyboard handling in `KanbanBoard` with roving card focus, arrow-key navigation across cards/columns, `Enter` open-detail behavior, and `n` quick-add targeting for the focused column. Extended `KanbanColumn`/`KanbanCard` to support focus wiring and keyboard quick-add triggers. Added a visible keyboard-shortcuts help control in `KanbanToolbar`. Updated kanban tests to cover keyboard navigation, quick-add shortcut behavior, input-focus guard behavior, and quick-add trigger plumbing.

**Why:** FR-KB-012 requires keyboard-first board control so users can quickly add and open tasks without pointer interactions while preserving existing drag/drop behavior and avoiding shortcut collisions during text entry.

---

## 2026-03-23 - Sprint S05: KB-04 Kanban Swimlanes by Assignee/Priority

### KB-04 - Implement FR-KB-011 Swimlane Grouping in Board Columns

**What:** Added lane mode support (`none`/`assignee`/`priority`) in kanban types and store, persisted per-project lane preference in `useKanbanStore`, added a lane-mode selector to `KanbanToolbar`, and wired lane mode through `KanbanPage` and `KanbanBoard`. Updated `KanbanColumn` to render stable lane groups with clear headers, explicit `Unassigned` handling for assignee mode, and preserved sortable drag context for lane-mode views. Added/updated focused tests across store, toolbar, board, column, and page coverage, including lane grouping and lane-mode drag-context assertions.

**Why:** FR-KB-011/US-12.6 require workload visibility by grouping cards within each status column by assignee or priority, without regressing existing kanban interactions.

---

## 2026-03-23 - Sprint S05: KB-02 Kanban Card Reordering Within Column

### KB-02 - Implement FR-KB-009 In-Column Card Reorder with Persistence

**What:** Switched Kanban cards to sortable drag behavior, added same-column reorder handling in `useKanbanDrag`, and wired existing task reorder API mutation with optimistic cache updates and rollback on failure. Kept cross-column drag for status changes intact. Added focused tests for reorder mutation payloads, optimistic ordering behavior, and no-op guards.

**Why:** FR-KB-009/US-12.4 require card prioritization inside a column with persisted order. Reusing the existing task reorder backend contract avoided new API surface while delivering immediate UI feedback and safe rollback on mutation failure.

---

## 2026-03-23 - Sprint S04: KB-08 Kanban Dependency Indicator on Card

### KB-08 - Implement FR-KB-015 Dependency State Badges

**What:** Added dependency indicator derivation in `KanbanPage` using existing `useDependencies(projectId)` data and passed per-task `blockedCount`/`blockingCount` into board/column/card rendering. `KanbanCard` now renders visually distinct blocked/blocking badges with icon + count, and badge click opens the existing task detail panel context. Added tests for indicator derivation and badge rendering/click behavior; updated kanban board/column tests for new props.

**Why:** FR-KB-015 requires cards to surface dependency risk directly in board view so blocked work is visible without opening each task. Reusing the existing dependency query avoided backend/API contract changes while keeping indicator state accurate for active dependencies.

---

## 2026-03-23 - SDLC Orchestrator Hardening

### Autopilot Close-Cycle Gate (Workflow Safety)

**What:** Updated `AGENTS.md` and `.codex/skills/dev-lifecycle/SKILL.md` with an explicit close-cycle gate that prevents task closure after BUILD-only execution. The gate requires running REVIEW skill chain, SYNC doc updates, `/done`, and `/cc` (when commit finalization is requested), and explicitly states that manual lint/test runs cannot replace required review/sync skills.

**Why:** A prior autopilot pass completed implementation and tests but skipped explicit skill-based review/sync closure. This hardening makes that class of miss non-repeatable by turning it into a policy violation at the orchestrator layer.

---

## 2026-03-23 - Sprint S04: KB-03 Kanban WIP Limits per Column

### KB-03 - Implement FR-KB-010 WIP Limits with Backend Persistence

**What:** Added bounded `kanban_wip_limits` to backend `ProjectSettingsPatch`, added API test coverage for project patch acceptance, and implemented kanban UI/store wiring for per-column limit set/clear, over-limit warning state, and project-scoped limit hydration. Limits are persisted via project settings updates and restored on board load. Added ADR-008 documenting the storage decision and updated KB-03 implementation docs/traceability.

**Why:** FR-KB-010 requires configurable per-column WIP limits with a visual warning when exceeded and persistence across sessions. Browser-only storage is not reliable across browser/device changes, so persistence was implemented in backend `project.settings.kanban_wip_limits` and mirrored locally only for responsive UI updates.

---

## 2026-03-23 — Sprint S03: TECH-04-E Gantt Milestone/Summary Click

### TECH-04-E — Fix Gantt Milestone/Summary Click (#46)

**What:** Removed `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` in `useGanttInteractions.ts`. Updated deps array accordingly.

**Why:** `handleChartTaskClick` was calling both `onTaskClick` and `onTaskDoubleClick` on a single click, which caused clicking any task bar to immediately open the detail panel. The intended behavior is single click = select only, double click = open panel. `handleChartTaskDoubleClick` already calls `onTaskDoubleClick` correctly — the duplicate call in the single-click handler was a copy-paste bug.

---

## 2026-03-23 — Sprint S03: TECH-04-D useLayoutEffect Missing Deps

### TECH-04-D — Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

**What:** Added an `// eslint-disable-next-line react-hooks/exhaustive-deps` directive with a rationale comment to the first `useLayoutEffect` in `useCollapsedTree.ts`.

**Why:** ESLint flagged the effect for missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`). The effect is intentionally mount/first-load-only: an `initializedRef` guards against re-runs regardless of dep changes. Adding the full dep list would be semantically wrong — the effect is not reactive, it fires once when `data` first arrives (empty → non-empty) and never again. A suppress directive with rationale is the correct resolution.

---

## 2026-03-22 — Sprint S03: TECH-04-F AI Stream Error Event Field Name

### TECH-04-F — Fix AI Stream Error Event Field Name (#53)

**What:** Changed `ai.service.ts` catch block to emit `{ type: "error", message: "..." }` instead of `{ type: "error", error: "..." }`. Updated the matching test expectation in `ai.service.test.ts`.

**Why:** The declared `AiChatEvent` type in `types.ts` defines the error event as `{ type: "error"; message: string }`. The service was emitting `error:` instead of `message:`, breaking the contract. `AiDockedPanel.tsx` correctly reads `event.message` — the mismatch meant a malformed JSON parse failure would produce an event that the panel could not display (it would silently fall through the `|| "AI chat failed"` fallback).

---

## 2026-03-21 — Sprint S02: TECH-03-E Cross-Feature Internal Imports

### TECH-03-E — Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

**What:** Fixed 11 files across ai, gantt, kanban, calendar, notifications, resources, projects, and tasks features that bypassed feature public barrels by importing from internal module paths (`@/features/X/hooks/Y`, `@/features/X/store/Z`). Updated auth and tasks barrels to export missing symbols (`useAiPreferences`, `useUpdateAiPreferences`, `taskKeys`, `useCreateTask`, `assignmentKeys`, `commentKeys`, `dependencyKeys`). Also updated 2 test files to mock barrel paths instead of internal paths (required to prevent barrel-loaded side effects from breaking tests).

**Why:** Cross-feature internal imports bypass each feature's public API contract. If an internal file is renamed or restructured, all consumers that import through internal paths break silently — the barrel is the single point of change. Standards require all cross-feature imports to go through `@/features/X` (the barrel).

---

## 2026-03-21 — Sprint S02: TECH-03-D Query Key Namespacing + Zustand Selectors

### TECH-03-D — Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

**What:** Prefixed four un-namespaced tasks query keys (`dependencies`, `assignments`, `attachments`, `comments`) with `tasks` namespace; prefixed `ai-preferences` key with `auth` namespace; replaced whole-store `useKanbanStore()` calls in `KanbanPage` and `KanbanColumn` with individual selector subscriptions.

**Why:** Standards require all query keys to be namespaced by feature to prevent cross-feature cache collisions. Whole-store Zustand subscriptions cause unnecessary re-renders when any part of the store changes; selectors scope re-renders to only the slice each component actually uses.

---

## 2026-03-21 — Sprint S01: Frontend Audit Complete

Sprint S01 was a pure audit sprint — no production code was changed. The goal was to establish a prioritized issue backlog for the frontend before remediating any bugs.

---

### TECH-01 — Frontend Automated Audit

**What:** Ran `tsc --noEmit`, `eslint src/`, and `npm test -- --run` across the entire frontend. Triaged every finding against existing dismissed/open issues and the roadmap.

**Why:** Needed a clean baseline of type errors, lint violations, and failing tests before any manual review — so that TECH-02 reviewers wouldn't re-report the same mechanical issues.

**Output:** Confirmed findings written to `issues/open_issues/`.

---

### TECH-02 — Frontend Standards Review

**What:** Ran `/frontend-feature-audit` on all 13 feature folders: `shared`, `auth`, `tasks`, `projects`, `organizations`, `kanban`, `gantt`, `dashboard`, `calendar`, `ai`, `notifications`, `resources`, `reports`.

**Why:** Systematic pass to catch dead code, standards violations, cross-feature inconsistencies, and architectural drift that automated tools miss.

**Output:** Confirmed findings (bugs, not roadmap items) written to `issues/open_issues/`. False positives dismissed via `/dismissed`.

---

## 2026-02-20 — Security & Cleanup Session

The following changes were made during this session. Each entry explains **what** was changed, **why** it was changed, and **what file** was affected.

---

### 1. IDOR Fix — Project listing by organization

**File:** `backend/app/api/v1/endpoints/projects.py`

**What changed:** Added a call to `get_org_membership_or_404(db, organization_id, user)` before listing projects when `organization_id` is provided.

**Why:** Without this check, any authenticated user could pass any `organization_id` to `GET /projects?organization_id=<ID>` and see all projects belonging to that organization — even if they're not a member. This is an IDOR (Insecure Direct Object Reference) vulnerability. The fix verifies the user is a member of the org before returning its projects. Uses the same `get_org_membership_or_404` dependency already used in `create_project`.

---

### 2. Swagger/OpenAPI docs disabled in production

**File:** `backend/app/main.py`

**What changed:** Added `docs_url`, `redoc_url`, and `openapi_url` parameters to the `FastAPI()` constructor. They resolve to their normal URLs when `ENV == "development"`, and `None` (disabled, returns 404) otherwise.

**Why:** Swagger UI exposes your full API schema (endpoints, parameters, auth requirements) to anyone who visits `/docs`. Since your API is only consumed by your own frontend, there's no reason to expose this map in production. Attackers use it to find endpoints to target.

---

### 3. Password max_length on registration

**File:** `backend/app/schema/auth.py`

**What changed:** `UserRegisterRequest.password` changed from `Field(min_length=8)` to `Field(min_length=8, max_length=128)`.

**Why:** bcrypt only uses the first 72 bytes of a password, but still processes whatever is sent. Without a max_length, an attacker can send a 1MB password on every registration request, wasting CPU on bcrypt hashing. 128 characters is the standard cap — way above any real password, but short enough to prevent abuse. Pydantic rejects oversized passwords with a 422 before bcrypt is ever called.

---

### 4. Password max_length on login

**File:** `backend/app/schema/auth.py`

**What changed:** `UserLoginRequest.password` changed from `str` to `Field(max_length=128)`.

**Why:** Same bcrypt DoS risk as registration. No `min_length` on login — we don't want to lock out users who may have registered under different rules.

---

### 5. Cookie path scoping

**File:** `backend/app/api/v1/endpoints/auth.py`

**What changed:** Added `path="/api"` to all access token `set_cookie` calls, and `path="/api/v1/auth"` to all refresh token `set_cookie` calls. Also added matching `path` arguments to `delete_cookie` calls in the logout endpoint.

**Why:** Without `path`, cookies default to `path="/"`, meaning the refresh token is sent with every single request (projects, tasks, resources, etc.). The refresh token should only be sent to auth endpoints (refresh, logout). This reduces the attack surface — if any non-auth endpoint has a vulnerability, the refresh token is never exposed. The `delete_cookie` calls need matching paths or the browser won't remove the cookies.

**Cookie paths:**
- Access token: `path="/api"` — sent to all API routes
- Refresh token: `path="/api/v1/auth"` — sent only to auth routes

---

### 6. Global email mock in tests

**File:** `backend/tests/conftest.py`

**What changed:** Added a global `autouse` fixture `_mock_mail_globally` that patches `email_service._get_mail_client` with a `MagicMock` for all tests.

**Why:** Only `test_email_verification.py` was mocking the mail client. The other 17 test files all register users (which triggers `send_verification_email`), and since the mail client wasn't mocked, real emails were being sent through your Gmail SMTP to fake addresses like `test@example.com`. This caused hundreds of bounce-back emails in your inbox. The global mock ensures no test ever sends a real email.

---

### 7. Removed dead `frontend_url` parameter

**Files:**
- `backend/app/service/email_service.py` — removed `frontend_url` from function signature
- `backend/app/api/v1/endpoints/auth.py` — removed `frontend_url` variable and argument from both call sites (register and resend)

**Why:** After the GET+redirect refactor for email verification, the verification link now uses `settings.BACKEND_URL` (pointing to the backend API). The `frontend_url` parameter was no longer used inside `send_verification_email()` but was still being accepted and passed in. Both callers were also doing unnecessary work to extract it from the `Origin` header. Dead code removed.

---

## Rules going forward

- Every change will be documented here **before** it is applied
- Each entry will explain **what**, **why**, and **which file**
- No changes without explicit approval

---

## 2026-03-23 - Sprint S04: KB-01 Task Detail Panel from Kanban Card

### KB-01 - Implement FR-KB-008 Task Detail Panel Open from Kanban Card

**What:** Added kanban detail-panel selection state to `useKanbanStore` (`selectedTaskId`, `setSelectedTaskId`, `clearSelectedTaskId`), wired card click propagation (`KanbanCard` -> `KanbanColumn` -> `KanbanBoard`), and mounted `TaskDetailPanel` directly in `KanbanPage` so card clicks open inline task details without route navigation. Added and updated focused tests for store behavior, card click callback, page-level panel open flow, and board-mounted interactivity while panel is open.

**Why:** FR-KB-008 and US-12.3 require opening task detail directly from a Kanban card without leaving the board. This implementation reuses the existing task detail surface and keeps the board view active while enabling direct edit access from card context.
