# Sprint Plan

Purpose: define one sprint commitment with capacity, scope, and completion criteria.

---

## Current Sprint

**Sprint ID:** S04
**Dates:** 2026-03-23 -> 2026-04-06
**Goal:** Kanban enhancement — task detail panel, WIP limits, assignee avatar, dependency indicator
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
| KB-01   | Kanban: task detail panel from card (FR-KB-008)              | 2      | P1; unblocks KB-02, KB-05, KB-09                    | -            | Clicking a card opens the existing task detail panel inline; board stays mounted; panel is closeable    |
| KB-03   | Kanban: WIP limits per column (FR-KB-010)                    | 2      | Independent; high value; no deps                     | -            | Per-column limit configurable; column header shows warning indicator when limit exceeded                |
| KB-07   | Kanban: assignee avatar on card (FR-KB-014)                  | 1      | Independent; 1-liner; high visibility improvement    | -            | Assignee avatar rendered on card; falls back to initials if no avatar; tooltip shows full name          |
| KB-08   | Kanban: dependency indicator on card (FR-KB-015)             | 1      | Independent; 1-liner; unblocks team visibility       | -            | Card shows blocked/blocking badge when active dependencies exist; badge links to dependency list        |

**Total committed points:** `6`

### Stretch (Optional)

| Item ID | Title                                         | Points | Trigger to pull in           |
| ------- | --------------------------------------------- | ------ | ---------------------------- |
| KB-02   | Kanban: card reordering within column (FR-KB-009) | 2  | Pull in if KB-01 ships early |

### Risks and Blockers

| Risk/Blocker                                                        | Impact                              | Mitigation                                                              | Owner |
| ------------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------- | ----- |
| Task detail panel integration may need new barrel exports           | Scope creep into tasks feature      | Read tasks barrel first; add exports cleanly without touching internals | wwwer |
| WIP limit storage (localStorage vs backend) requires design decision | Architecture choice before coding  | Decide and write ADR before touching code                               | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `6`
- Completed points: `-`
- Carry-over points: `-`
- Main wins:
- Main misses:
- Process changes for next sprint:

---

---

## Previous Sprint

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

## Previous Sprint

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
| S03    | 2026-03-22 -> 2026-04-05 | 7       | -         | -          | P2 bug fixes — error states, hook anti-patterns, Gantt UX, AI contract              |
| S02    | 2026-03-21 -> 2026-04-04 | 7       | 7         | 0          | Frontend cleanup — dead code, cross-feature imports, query keys, failing tests      |
| S01    | 2026-03-21 -> 2026-04-04 | 7       | 7         | 0          | Frontend audit sprint — full tsc/eslint/test + 13-feature standards review complete |
