# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S02
**Dates:** 2026-03-21 -> 2026-04-04
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

---

## Active Items — S02

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

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] #34: Prefix `ai-preferences` query key with feature namespace in auth hooks
- [ ] #38: Prefix `dependencies`, `assignments`, `attachments`, `comments` query keys with `tasks` namespace
- [ ] #45: Replace whole-store subscriptions in kanban with selector-based subscriptions

#### Notes

- Dependencies: -
- Blockers: -
- Decisions: Changing query keys invalidates cache — verify no stale cache issues after rename

---

### TECH-03-E — Fix Cross-Feature Internal Imports (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)

Status: `NOT_STARTED`

#### Mini-tasks

- [ ] #33: `AiDockedPanel.tsx` — import `useAiPreferences`/`useUpdateAiPreferences` through auth barrel (add to barrel if missing)
- [ ] #33: `ai.service.ts` — import `useAuthStore` from `@/features/auth` not internal path
- [ ] #37: Task-detail components — import through `@/features/tasks` barrel
- [ ] #39: Projects WebSocket — import query keys through `@/features/tasks` barrel
- [ ] #40: `ProjectOverviewPage` — import through `@/features/ai` barrel
- [ ] #44: `KanbanColumn` — import `useCreateTask` through `@/features/tasks` barrel
- [ ] #47: `useSchedule` — import `taskKeys` through `@/features/tasks` barrel
- [ ] #48: `GanttBarQuickInfo` — import `useAssignments` through `@/features/tasks` barrel
- [ ] #50: `CalendarPage` — fix all cross-feature internal imports
- [ ] #52: AI feature — import tasks types through `@/features/tasks` barrel
- [ ] #54: Notifications hook — import auth through `@/features/auth` barrel
- [ ] #55: Resources — replace relative imports with absolute `@/` imports

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
