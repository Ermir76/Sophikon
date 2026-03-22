# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S03
**Dates:** 2026-03-22 -> 2026-04-05
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items — S03

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

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `CalendarPage.tsx`: replace `setSelectedCalendarId(calendars[0].id)` inside effect with `useState(() => calendars[0]?.id)` initializer or derive from data directly
- [ ] `TasksPage.tsx`: replace `setIsAddingFirstTask(false)` inside effect with derived value `tasks.length === 0` — remove state entirely if possible
- [ ] Verify ESLint `react-hooks/set-state-in-effect` no longer flags these files

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Prefer derived state over `useState` initialization if the value can be computed from props/query data

---

### TECH-04-D — Fix `useLayoutEffect` Missing Deps in `useCollapsedTree` (#30)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] Read `useCollapsedTree.ts` and determine intent of the `useLayoutEffect` at line 38
- [ ] If truly mount-only: add `// eslint-disable-next-line react-hooks/exhaustive-deps` with explicit rationale comment
- [ ] If should re-run on changes: add all 5 missing deps (`data`, `defaultCollapseAll`, `getParentId`, `setValue`, `storageKey`); ensure `getParentId` is stable (wrapped in `useCallback` at call sites if needed)
- [ ] Verify gantt and task tree views still behave correctly after change

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: TBD — must read the hook intent first before committing to either approach

---

### TECH-04-E — Fix Gantt Milestone/Summary Click (#46)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] `useGanttInteractions.ts`: remove `onTaskDoubleClick(taskId)` call from `handleChartTaskClick` — keep only `onTaskClick(taskId)`
- [ ] Manually verify: single click selects; double click opens panel; no regression on regular task bars

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
