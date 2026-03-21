# Product Backlog

Purpose: single prioritized list of planned work across FRs, agent-platform items, and technical debt.

**Last updated:** 2026-03-21
**Status source:** `docs/03-implementation/requirements-traceability.md`
**Roadmap source:** `docs/ROADMAP.md`

Points scale:

- `1` = half day
- `2` = 1 day
- `3` = 2-3 days
- `5` = 3-5 days
- `8` = ~1 week
- `13` = must split

---

## Prioritization Rules

1. `P0` = release blocker or critical defect.
2. `P1` = required for committed release scope.
3. `P2` = important but can slip one sprint.
4. `P3` = optional or post-release.

---

## Backlog Items

| Item ID | Type (`FR`/`AP`/`TECH`) | Title            | Priority | Points | Dependencies | Target Release | Status (`NOT_READY`/`READY`/`IN_PROGRESS`/`BLOCKED`/`DONE`) | Owner | Notes                  |
| ------- | ----------------------- | ---------------- | -------- | ------ | ------------ | -------------- | ----------------------------------------------------------- | ----- | ---------------------- |
| TECH-01 | TECH                    | Frontend Automated Audit (tsc + eslint + tests → issue triage) | P1 | 2 | - | V1.0 | DONE | - | S01 |
| TECH-02 | TECH                    | Frontend Standards Review (feature-by-feature /consistency-review) | P1 | 5 | TECH-01 | V1.0 | DONE | - | S01; one feature per session |
| TECH-03-A | TECH                  | Fix failing Gantt tests — export TaskDetailPanel from tasks barrel (#27) | P1 | 1 | TECH-01, TECH-02 | V1.0 | IN_PROGRESS | - | S02 |
| TECH-03-B | TECH                  | Remove dead code — unused imports, dead files/exports, non-functional UI (#28 #32 #36 #42 #49) | P1 | 2 | TECH-01, TECH-02 | V1.0 | IN_PROGRESS | - | S02 |
| TECH-03-C | TECH                  | Fix `any` types in test files (#29) | P1 | 1 | TECH-01, TECH-02 | V1.0 | IN_PROGRESS | - | S02 |
| TECH-03-D | TECH                  | Fix query key namespacing + Zustand selectors (#34 #38 #45) | P1 | 1 | TECH-01, TECH-02 | V1.0 | IN_PROGRESS | - | S02 |
| TECH-03-E | TECH                  | Fix cross-feature internal imports (11 files) (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55) | P1 | 2 | TECH-01, TECH-02 | V1.0 | IN_PROGRESS | - | S02 |
| TECH-04   | TECH                  | Frontend P2 bug fixes (#26 #30 #35 #41 #43 #46 #51 #53 #56) | P1 | TBD | TECH-03-A..E | V1.0 | NOT_READY | - | S03 |

---

## Release Buckets

### V1.0 (Committed)

| Item ID | Title | Points | Planned Sprint |
| ------- | ----- | ------ | -------------- |
| TECH-01 | Frontend Automated Audit | 2 | S01 |
| TECH-02 | Frontend Standards Review | 5 | S01 |
| TECH-03 | Frontend Bug Remediation | TBD | S02 |

### V1.1 (Planned)

| Item ID | Title | Points | Notes |
| ------- | ----- | ------ | ----- |
| -       | -     | -      | -     |

---

## Backlog Hygiene Checklist

- Remove duplicates.
- Split all `13` point items before sprint commitment.
- Ensure each committed item has clear acceptance criteria in requirements/design docs.
- Keep `Status` and `Planned Sprint` synchronized with `sprint-plan.md`.
