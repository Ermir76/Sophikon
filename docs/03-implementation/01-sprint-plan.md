# Sprint Plan

Purpose: define one sprint commitment with capacity, scope, and completion criteria.

---

## Current Sprint

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

## Previous Sprint

**Sprint ID:** S01
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
| S02    | 2026-03-21 -> 2026-04-04 | 7       | -         | -          | Frontend cleanup — dead code, cross-feature imports, query keys, failing tests      |
| S01    | 2026-03-21 -> 2026-04-04 | 7       | 7         | 0          | Frontend audit sprint — full tsc/eslint/test + 13-feature standards review complete |
