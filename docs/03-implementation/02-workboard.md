# Workboard

Purpose: execution checklist for currently committed sprint items.

**Sprint ID:** S01
**Dates:** 2026-03-21 -> 2026-04-04
**References:** `docs/03-implementation/sprint-plan.md`, `docs/00-planning/backlog.md`, `docs/03-implementation/requirements-traceability.md`

Rule: one section per committed item. Keep tasks concrete and small.

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
