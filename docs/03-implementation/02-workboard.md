# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S12
**Dates:** TBD
**References:** `docs/03-implementation/01-sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/03-requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items — S12

### AGT-01 — Agent policy engine: centralized permission and role check before every tool execution

Status: `DONE`

#### Mini-tasks

- [x] Define `ToolPolicy` enum (`allow`, `allow_with_approval`, `deny`) and `PolicyDecision` dataclass
- [x] Create `agent/policy.py` with `check_tool_policy(tool_name, tool_input, ctx) → PolicyDecision`
- [x] Implement action allowlist check — reject unknown tool names
- [x] Implement role check — map project role (viewer/member/manager/owner) to allowed tool tiers (read/write/destructive/UI)
- [x] Implement scope check — validate entity IDs in `tool_input` belong to `ctx.project_id` (task/dependency/assignment/resource IDs)
- [x] Add `role_name` to `AgentContext` and pass it from AI endpoint `ProjectAccess` when building the context
- [x] Wire `check_tool_policy` into `executor.py` before tool execution and before destructive approval branching
- [x] On `deny` → return explicit tool-result error to the LLM (no execution)
- [x] On `allow_with_approval` → reuse existing `_wait_for_tool_approval` mechanism
- [x] Add default policy config (viewer=read+UI only, member=read+write+UI, manager/owner=all)
- [x] Tests: viewer blocked from write tools, member allowed writes, deny on unknown tool, scope violation returns deny, destructive tools still require per-action approval

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Policy is implemented as a pure service-layer decision function and keeps destructive approval as a second gate.
  - Scope validation is object-level and project-scoped for task/dependency/resource/assignment references.

---

### AGT-02 — Agent kill switch: per-project and per-org flag to disable agent execution

Status: `DONE`

#### Mini-tasks

- [x] Add `agent_enabled` boolean to project settings JSON schema (default: true when missing)
- [x] Add `agent_enabled` boolean to organization settings JSON schema (default: true when missing)
- [x] Check both flags at `prepare_chat_stream` entry — reject with clear `InvalidOperationError` if either is false
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

## Previous Sprint Items — S10

### UX-01 — Invitation flow blockers + recovery

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

### UX-02 — Notification center IA + accessibility baseline

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

### UX-03 — Membership actions safety + copy clarity

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

### UX-04 — Profile settings usability batch

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

### FIX-17 — AI service mock-provider tests fail in live mode (Stretch)

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

### UX-05 — Visual consistency polish pass (Stretch)

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

## Previous Sprint Items — S09

### FIX-14 — Invitation review page UX overhaul

Status: `DONE`

#### Mini-tasks

- [x] Write ADR-009 for route-state decision (done during planning)
- [x] Add "Considered" entry to roadmap for future GET invitation endpoint (done during planning)
- [x] Notification card: remove invitation message line — keep only project name, role, and Accept/Review buttons
- [x] "Review" button: navigate to accept page with route state `{ review: true, title, message }`
- [x] "Accept" button: accepts inline then navigates with accepted data (kept existing behavior)
- [x] Accept page — review mode: show invitation details card (title, full message) with "Accept Invitation" and "Back" buttons; do NOT auto-accept
- [x] Accept page — auto-accept mode: keep current behavior (auto-accept on mount, show "Invitation Accepted" + "Go to Project")
- [x] Accept page — fallback: when route state is missing (email link, page refresh), auto-accept as before
- [x] Accept page — after accept in review mode: transition to accepted state with "Go to Project"
- [x] Tests: update/add coverage for review mode, auto-accept mode, fallback mode, and notification card without message
- [x] Resolve accepted invite notifications so non-actionable invitation rows disappear from the bell and unread counts stay correct

#### Notes

- Dependencies: FIX-10 (accept page foundation)
- Blockers: -
- Decisions: ADR-009 — route state for invitation details remains the review-mode source for now; future GET endpoint is still tracked in the roadmap Considered section.
- Scope: frontend review UX plus targeted backend notification resolution for accepted invitations.

---

### FIX-06 — Silent token refresh not proactive (#26)

Status: `DONE`

#### Mini-tasks

- [x] Confirm the app only refreshed auth reactively after a 401 and had no proactive idle-session timer
- [x] Add an authenticated app-level refresh timer before access-token expiry
- [x] Verify the timer path with focused frontend coverage

#### Notes

- Files: `frontend/src/app/App.tsx`, `frontend/src/app/App.test.tsx`
- The refresh remains cookie-based through `POST /auth/refresh`; no new backend contract was needed

---

### FIX-08 — Org member role change layout glitch (#33)

Status: `DONE`

#### Mini-tasks

- [x] Investigate the role-update pending-state rendering in the org members page
- [x] Add a stable per-row saving indicator and freeze role actions while a role update is in flight
- [x] Verify the pending state with focused frontend coverage

#### Notes

- Files: `frontend/src/features/organizations/pages/OrgMembersPage.tsx`, `frontend/src/features/organizations/components/MembersTable.tsx`, `frontend/src/features/organizations/components/MemberActions.tsx`
- The fix keeps the active row visually stable and prevents overlapping role updates from multiple menus

---

## Previous Sprint Items — S08

### FIX-09 — Finalize Vite WS proxy fix (#39)

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

### FIX-10 — Project invite accept page stuck on "Accepting invitation..." (#35)

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

### FIX-11 — Org switcher not updated after project invite accept (#36)

Status: `DONE`

#### Mini-tasks

- [x] In the accept mutation's `onSuccess`, invalidate the organizations query so the sidebar org list refetches
- [x] Export organization query keys through the feature barrel so the cross-feature invalidation stays within public API rules
- [x] Verify the invalidation behavior and auto-switch follow-through with focused hook/page coverage

#### Notes

- File: `frontend/src/features/projects/hooks/useProjectMembers.ts` (the accept mutation's onSuccess callback)
- The org query key is likely in `frontend/src/features/organizations/` — find it and invalidate after accept
- Depends on FIX-10 being resolved first

---

### FIX-12 — Removed project member sees generic error (#37)

Status: `DONE`

#### Mini-tasks

- [x] Catch the project-access 403 at the shared project layout boundary
- [x] Show a clear "You no longer have access to this project" state with a path back to `/projects`
- [x] Verify the access-loss UI with focused project-layout coverage

#### Notes

- Files: `frontend/src/features/projects/components/ProjectLayout.tsx` or the project route guard
- Backend returns 403 via `PermissionDeniedError` when a non-member accesses a project
- The fix should handle 403 specifically — don't mask other errors

---

### FIX-13 — WebSocket hooks unstable effect dependencies (#40)

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

## Previous Sprint Items — S07

### FIX-01 — Avatar upload crashes with raw Pydantic error (#27)

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

### FIX-02 — Deleted org slug not released (#31)

Status: `DONE`

#### Mini-tasks

- [x] Check if org delete is soft delete — confirmed: sets `is_deleted=True`, `deleted_at`
- [x] Update slug uniqueness to exclude soft-deleted orgs and align service/repository lookups with active-org semantics
- [x] Verify: delete an org, recreate with the same slug — succeeds

#### Notes

- Model: `backend/app/models/organization.py` — `slug` previously had a global unique constraint
- Service: `backend/app/service/organization_service.py` — `soft_delete_organization()`
- Implemented fix: replace the global slug unique index with an active-only partial unique index and keep repository lookups scoped to non-deleted orgs

---

### FIX-03 — Sidebar no fallback after org deletion (#32)

Status: `DONE`

#### Mini-tasks

- [x] Find where org deletion success is handled in the frontend store/page
- [x] After deletion, find the user's personal org and set it as active
- [x] Verify: delete active org → app switches to personal org automatically

#### Notes

- Depends on FIX-02 being stable first
- Personal org is identifiable by `is_personal: true` on the org object

---

### FIX-04 — Change password missing toast (#29)

Status: `DONE`

#### Mini-tasks

- [x] Replace inline-only success feedback with standard Sonner success toast
- [x] Keep the form reset behavior after successful password change
- [x] Verify with focused `ProfilePage` test coverage

#### Notes

- File: `frontend/src/features/auth/pages/ProfilePage.tsx`
- Follow the existing mutation feedback pattern used in settings pages that already use `toast.success(...)`

---

### FIX-05 — AI preferences toggle glitch (#30)

Status: `DONE`

#### Mini-tasks

- [x] Add visible success feedback after AI preference save
- [x] Remove the switch flash caused by pending-state handling on save
- [x] Verify toggle behavior with focused `ProfilePage` test coverage

#### Notes

- Files: `frontend/src/features/auth/pages/ProfilePage.tsx`, `frontend/src/features/auth/pages/ProfilePage.test.tsx`
- Implemented with page-local optimistic toggle state plus success/error reconciliation from the mutation response

---

## Previous Sprint Items — S06

### KB-09 — Kanban: AI Sprint Health Summary (FR-KB-016)

Status: `DONE`

#### Mini-tasks

- [x] Add "Sprint Health" button to Kanban toolbar — triggers `refetch()` on `useAiSuggestions`, does not auto-fetch on mount
- [x] Wire `useAiSuggestions(projectId, limit, enabled=false)` into `KanbanPage` — use `refetch()` on button press, not `enabled` toggle
- [x] Build `KanbanHealthSummary` component: render HIGH/MEDIUM severity suggestions grouped by `affected_task_id`, show `title` + `description` per risk
- [x] Link each risk entry to the affected kanban card — clicking a risk highlights the card or opens the existing `TaskDetailPanel`
- [x] Add loading spinner and error fallback (with retry) that do not block board interactions
- [x] Add tests: summary renders on success, empty state when no HIGH/MEDIUM suggestions, error fallback shown on failure

#### Notes

- Dependencies: `KB-01` complete
- Blockers: -
- Decisions:
  - No backend changes — `GET /projects/{id}/ai/suggestions` already returns `AiSuggestion[]` with `severity`, `title`, `description`, `affected_task_id`
  - No new types — `AiSuggestion`, `AiSuggestionsResponse` in `ai/types.ts` are the full contract
  - No new service calls — `aiService.suggestions()` and `useAiSuggestions()` already exist in `useAi.ts`
  - Fetch is manual only: `refetchOnMount: false`, `refetchOnWindowFocus: false` already set on the hook; pass `enabled=false` and call `refetch()` on button press
  - Filter to HIGH/MEDIUM only in the component — LOW severity suggestions are not surfaced in this view
  - Keep V1 project-scoped and board-context only (no cross-project aggregation)

---

## Previous Sprint Items — S05

### KB-02 — Kanban: Card Reordering Within Column (FR-KB-009)

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

### KB-04 — Kanban: Swimlanes by Assignee/Priority (FR-KB-011)

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

### KB-05 — Kanban: Keyboard Shortcuts (FR-KB-012)

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

### KB-06 — Kanban: Bulk Select And Move Cards (FR-KB-013)

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

## Previous Sprint Items — S04

### KB-01 — Kanban: Task Detail Panel from Card (FR-KB-008)

Status: `DONE`

#### Mini-tasks

- [x] Read existing `TaskDetailPanel` component and tasks barrel — identify what to re-use
- [x] Add slide-in panel state to kanban store (`selectedTaskId: string | null`)
- [x] Wire card click to set `selectedTaskId` (replace current no-op)
- [x] Render `TaskDetailPanel` inside `KanbanPage` — mount alongside board, not as route navigation
- [x] Ensure panel is closeable (Escape key + close button)
- [x] Verify board stays mounted and interactive while panel is open

#### Notes

- Dependencies: -
- Blockers: -
- Decisions:
  - Use existing `TaskDetailPanel` from tasks feature — do not build a new one
  - Keep panel state in kanban Zustand store (`selectedTaskId` + setter/clearer)
  - Open panel on kanban card click; keep drag behavior unchanged
  - Render panel directly in `KanbanPage` as non-floating `Sheet` (`floating` omitted)

---

### KB-03 — Kanban: WIP Limits per Column (FR-KB-010)

Status: `DONE`

#### Mini-tasks

- [x] Design decision: where to store WIP limits (localStorage per project vs backend) — write ADR before coding
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

### KB-07 — Kanban: Assignee Avatar on Card (FR-KB-014)

Status: `DONE`

#### Mini-tasks

**Backend**
- [x] Add `TaskAssignmentSummary` schema: `resource_id`, `resource_name`, `resource_initials`
- [x] Extend `TaskRead` schema with `assignments: list[TaskAssignmentSummary]`
- [x] Update task list service/repository to JOIN and embed assignments in the task list response

**Frontend**
- [x] Add `assignments` field to `Task` type in `frontend/src/features/tasks/types.ts`
- [x] Render assignee avatar on `KanbanCard` — use `Avatar`/`AvatarFallback` from `shared/ui/avatar`; show initials if no avatar
- [x] Add tooltip with full resource name on hover
- [x] Handle unassigned state gracefully (no avatar rendered)
- [x] Write tests: avatar renders when assigned, nothing renders when unassigned

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Embed `assignments` in task list response (Option A) — avoids N+1 queries. Shape: `[{ resource_id, resource_name, resource_initials }]`. Resource has no `avatar_url` so initials-only fallback is the norm.

---

### KB-08 — Kanban: Dependency Indicator on Card (FR-KB-015)

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

## Previous Sprint Items — S03

### TECH-04-A — Batch Error State Fixes (#41 #43 #51 #56)

Status: `DONE`

#### Mini-tasks

- [x] #41: `OrgSwitcher.tsx` — destructure `isError`/`refetch`; render inline error/retry in dropdown when `isError` is true
- [x] #43: `useKanbanDrag.ts` — add `onError: (error) => toast.error(getErrorMessage(error))` to `mutate()` call
- [x] #51: `CalendarPage.tsx` — add `exceptionsQuery.isError` branch rendering `QueryError` with retry before empty-state branch
- [x] #56: `UtilizationPage.tsx` — capture `isError`/`refetch` from `useOverAllocations`; render `QueryError` for over-allocation section on error

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Use existing `QueryError` component pattern (see `DashboardPage.tsx`) — do not introduce new error UI

---

### TECH-04-B — ProfilePage AI Error State + Remove Double Refetch (#35)

Status: `DONE`

#### Mini-tasks

- [x] Add `else if (aiPreferencesQuery.isError)` branch in AI Settings tab — render `QueryError` or alert before tool list
- [x] Remove redundant `aiPreferencesQuery.refetch()` call from `handleAiToggle` `onSuccess` — invalidation already handles it

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Do not refactor the surrounding tab structure — surgical fix only

---

### TECH-04-C — Fix `setState` in `useEffect` (#26)

Status: `DONE`

#### Mini-tasks

- [x] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [x] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` — remove state entirely if possible
- [x] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D — Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `DONE`

#### Mini-tasks

- [x] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [x] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [x] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [x] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD — must read the hook intent first before committing to either approach

---

### TECH-04-E — Fix Gantt Milestone/Summary Click (#46)

Status: `DONE`

#### Mini-tasks

- [x] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` — keep only `onTaskClick(taskId)`
- [x] Manually verify: single click selects; double click opens panel; no regression on regular task bars

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: 1-line removal; do not touch `handleChartTaskDoubleClick`

---

### TECH-04-F — Fix AI Stream Error Event Field Name (#53)

Status: `DONE`

#### Mini-tasks

- [x] `ai.service.ts` line 104: change `error: "Malformed streaming response"` → `message: "Malformed streaming response"`
- [x] Update corresponding test expectation in `ai.service.test.ts`
- [x] Verify `AiDockedPanel.tsx` correctly receives and displays the error message

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Align to the declared `{ type: "error"; message: string }` contract in `ai/types.ts` — no contract changes

---

## Previous Sprint Items — S02

### TECH-03-A — Fix Failing Gantt Tests (#27)

Status: `DONE`

#### Mini-tasks

- [x] Export `TaskDetailPanel` from `frontend/src/features/tasks/index.ts`
- [x] Verify all 3 failing Gantt tests pass
- [x] Run `npm test -- --run` to confirm no regressions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Fix is barrel-only — do not move the component

---

### TECH-03-B — Remove Dead Code (#28 #32 #36 #42 #49)

Status: `DONE`

#### Mini-tasks

- [x] #28: Remove unused `useEffect` import from `AiDockedPanel.tsx`; remove unused `GanttHoverTooltip` import from `GanttContainer.tsx`
- [x] #32: Delete `frontend/src/shared/ui/empty.tsx`; remove `getInitials` export from `shared/lib/utils.ts`
- [x] #36: Fixed show/hide password button in `LoginPage.tsx` — wired up state toggle and EyeOff icon
- [x] #42: Remove dead exports (`InviteMemberDialog`, `MembersTable`, `MemberActions`) from organizations barrel
- [x] #49: Delete `GanttClickPopoverOverlay` file and remove any import references

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: For #32, do NOT consolidate the three inline `getInitials` copies — that's a separate refactor; just remove the dead export

---

### TECH-03-C — Fix `any` Types in Test Files (#29)

Status: `DONE`

#### Mini-tasks

- [x] Find all `any` usages in test files (`*.test.ts`, `*.test.tsx`)
- [x] Replace with proper types or `unknown` + type narrowing
- [x] Confirm `tsc --noEmit` passes with no new errors

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Scope strictly to test files only — do not touch production code

---

### TECH-03-D — Fix Query Key Namespacing + Zustand Selectors (#34 #38 #45)

Status: `DONE`

#### Mini-tasks

- [x] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [x] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [x] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache — verify no stale cache issues after rename

---

### TECH-03-E — Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `DONE`

#### Mini-tasks

- [x] #33: `AiDockedPanel.tsx` — import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [x] #33: `ai.service.ts` — import `useAuthStore` from `@/features/auth` not internal path
- [x] #37: Task-detail components — import through `@/features/tasks` barrel
- [x] #39: Projects WebSocket — import query keys through `@/features/tasks` barrel
- [x] #40: `ProjectOverviewPage` — import through `@/features/ai` barrel
- [x] #44: `KanbanColumn` — import `useCreateTask` through `@/features/tasks` barrel
- [x] #47: `useSchedule` — import `taskKeys` through `@/features/tasks` barrel
- [x] #48: `GanttBarQuickInfo` — import `useAssignments` through `@/features/tasks` barrel
- [x] #50: `CalendarPage` — fix all cross-feature internal imports
- [x] #52: AI feature — import tasks types through `@/features/tasks` barrel
- [x] #54: Notifications hook — import auth through `@/features/auth` barrel
- [x] #55: Resources — replace relative imports with absolute `@/` imports

#### Notes

- Dependencies: Some barrel exports may be missing — add them as part of this task
- Blockers: -
- Decisions: Never add internal path imports as a workaround; always fix the barrel

---

## Previous Sprint Items — S01

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

### TECH-01 — Frontend Automated Audit

Status: `DONE`

#### Mini-tasks

- [x] Run `cd frontend && npx tsc --noEmit` — capture all type errors
- [x] Run `cd frontend && npx eslint src/` — capture all lint violations
- [x] Run `cd frontend && npm test -- --run` — capture all failing tests
- [x] Triage each finding: skip if already in `issues/dismissed_issues/`, `issues/open_issues/`, or is a planned roadmap item
- [x] Write new `issues/open_issues/` files for every surviving confirmed finding
- [x] Mark TECH-01 DONE in workboard

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: tsc + eslint run in main session (not subagent) so output lands directly in context

---

### TECH-02 — Frontend Standards Review

Status: `DONE`

#### Mini-tasks

- [x] `shared/` — run /frontend-feature-audit shared
- [x] `auth` — run /frontend-feature-audit auth
- [x] `tasks` — run /frontend-feature-audit tasks
- [x] `projects` — run /frontend-feature-audit projects
- [x] `organizations` — run /frontend-feature-audit organizations
- [x] `kanban` — run /frontend-feature-audit kanban
- [x] `gantt` — run /frontend-feature-audit gantt
- [x] `dashboard` — run /frontend-feature-audit dashboard
- [x] `calendar` — run /frontend-feature-audit calendar
- [x] `ai` — run /frontend-feature-audit ai
- [x] `notifications` — run /frontend-feature-audit notifications
- [x] `resources` — run /frontend-feature-audit resources
- [x] `reports` — run /frontend-feature-audit reports
- [x] Mark TECH-02 DONE in workboard

#### Notes

- Dependencies: TECH-01 complete first
- Blockers: -
- Decisions: **one feature per session** — prevents context loss. Each session: pick next unchecked feature, run /consistency-review scoped to that feature only, commit findings to issues/ before ending session.
