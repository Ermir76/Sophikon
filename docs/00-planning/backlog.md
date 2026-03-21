# Product Backlog

Purpose: single prioritized list of planned work across FRs, agent-platform items, and technical debt.

**Last updated:** YYYY-MM-DD
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
| FR-XXX  | FR                      | Placeholder item | P2       | 3      | -            | V1.0           | NOT_READY                                                   | -     | Replace with real item |

---

## Release Buckets

### V1.0 (Committed)

| Item ID | Title | Points | Planned Sprint |
| ------- | ----- | ------ | -------------- |
| -       | -     | -      | -              |

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
