# Product Backlog

Purpose: single prioritized list of planned work across FRs, agent-platform items, and technical debt.

**Last updated:** 2026-03-26
**Status source:** `docs/03-implementation/03-requirements-traceability.md` + `docs/03-implementation/01-sprint-plan.md` + `docs/03-implementation/02-workboard.md`
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

| Item ID   | Type (`FR`/`AP`/`TECH`) | Title                                                                                                | Priority | Points | Dependencies     | Target Release | Status (`NOT_READY`/`READY`/`IN_PROGRESS`/`BLOCKED`/`DONE`) | Owner | Notes                        |
| --------- | ----------------------- | ---------------------------------------------------------------------------------------------------- | -------- | ------ | ---------------- | -------------- | ----------------------------------------------------------- | ----- | ---------------------------- |
| TECH-01   | TECH                    | Frontend Automated Audit (tsc + eslint + tests → issue triage)                                       | P1       | 2      | -                | V1.0           | DONE                                                        | -     | S01                          |
| TECH-02   | TECH                    | Frontend Standards Review (feature-by-feature /consistency-review)                                   | P1       | 5      | TECH-01          | V1.0           | DONE                                                        | -     | S01; one feature per session |
| TECH-03-A | TECH                    | Fix failing Gantt tests — export TaskDetailPanel from tasks barrel (#27)                             | P1       | 1      | TECH-01, TECH-02 | V1.0           | DONE                                                        | -     | S02                          |
| TECH-03-B | TECH                    | Remove dead code — unused imports, dead files/exports, non-functional UI (#28 #32 #36 #42 #49)       | P1       | 2      | TECH-01, TECH-02 | V1.0           | DONE                                                        | -     | S02                          |
| TECH-03-C | TECH                    | Fix `any` types in test files (#29)                                                                  | P1       | 1      | TECH-01, TECH-02 | V1.0           | DONE                                                        | -     | S02                          |
| TECH-03-D | TECH                    | Fix query key namespacing + Zustand selectors (#34 #38 #45)                                          | P1       | 1      | TECH-01, TECH-02 | V1.0           | DONE                                                        | -     | S02                          |
| TECH-03-E | TECH                    | Fix cross-feature internal imports (11 files) (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)          | P1       | 2      | TECH-01, TECH-02 | V1.0           | DONE                                                        | -     | S02                          |
| TECH-04-A | TECH                    | Batch error state fixes — OrgSwitcher, Kanban drag, Calendar exceptions, Resources (#41 #43 #51 #56) | P2       | 2      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |
| TECH-04-B | TECH                    | ProfilePage AI error state + remove double refetch (#35)                                             | P2       | 1      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |
| TECH-04-C | TECH                    | Fix setState in useEffect — CalendarPage + TasksPage (#26)                                           | P2       | 1      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |
| TECH-04-D | TECH                    | Fix useLayoutEffect missing deps in useCollapsedTree (#30)                                           | P2       | 1      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |
| TECH-04-E | TECH                    | Fix Gantt milestone/summary click opens detail panel (#46)                                           | P2       | 1      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |
| TECH-04-F | TECH                    | Fix AI stream error event field name mismatch (#53)                                                  | P2       | 1      | TECH-03-A..E     | V1.0           | DONE                                                        | -     | S03                          |

| KB-01 | FR | Kanban: task detail panel from card (FR-KB-008) | P1 | 2 | TECH-04-A..F | V1.0 | DONE | - | S04 |
| KB-02 | FR | Kanban: card reordering within column (FR-KB-009) | P2 | 2 | KB-01 | V1.0 | DONE | - | S05 |
| KB-03 | FR | Kanban: WIP limits per column (FR-KB-010) | P2 | 2 | - | V1.0 | DONE | - | S04 |
| KB-04 | FR | Kanban: swimlanes by assignee/priority (FR-KB-011) | P2 | 3 | - | V1.0 | DONE | - | S05 |
| KB-05 | FR | Kanban: keyboard shortcuts (FR-KB-012) | P2 | 2 | KB-01 | V1.0 | DONE | - | S05 |
| KB-06 | FR | Kanban: bulk select and move cards (FR-KB-013) | P2 | 2 | - | V1.0 | DONE | - | S05 |
| KB-07 | FR | Kanban: assignee avatar on card (FR-KB-014) | P2 | 1 | - | V1.0 | DONE | - | S04 |
| KB-08 | FR | Kanban: dependency indicator on card (FR-KB-015) | P2 | 1 | - | V1.0 | DONE | - | S04 |
| KB-09 | FR | Kanban: AI sprint health summary (FR-KB-016) | P2 | 3 | KB-01 | V1.0 | DONE | wwwer | S06 |
| KB-10 | FR | Kanban: AI quick-fill from title (FR-KB-017) | P3 | 2 | KB-01 | V1.1 | NOT_READY | - | - |
| KB-11 | FR | Kanban: AI-detected blockers highlight (FR-KB-018) | P3 | 2 | KB-09 | V1.1 | NOT_READY | - | - |
| FIX-01 | TECH | Avatar upload crashes with raw Pydantic error in UI (#27) | P0 | 1 | - | V1.0 | DONE | wwwer | S07 |
| FIX-02 | TECH | Deleted org name/slug not released after soft delete (#31) | P0 | 1 | - | V1.0 | DONE | wwwer | S07 |
| FIX-03 | TECH | Sidebar no fallback to personal org after deletion (#32) | P1 | 1 | FIX-02 | V1.0 | DONE | wwwer | S07 |
| FIX-04 | TECH | Change password success not using Sonner toast (#29) | P2 | 1 | - | V1.0 | DONE | wwwer | S07 stretch |
| FIX-05 | TECH | AI preferences toggle glitch — no confirmation + icon flash (#30) | P2 | 1 | - | V1.0 | DONE | wwwer | S07 stretch |
| FIX-06 | TECH | Silent token refresh not proactive — user kicked to /login after idle (#26) | P1 | 2 | - | V1.0 | DONE | wwwer | S09 |
| FIX-07 | TECH | Password reset allows reuse of previous password (#28) | P2 | 1 | - | V1.0 | READY | - | - |
| FIX-08 | TECH | Org member role change shows layout glitch (#33) | P2 | 1 | - | V1.0 | DONE | wwwer | S09 |
| FIX-09 | TECH | Commit Vite WS proxy fix — add ws:true to /api proxy (#39) | P0 | 1 | - | V1.0 | DONE | wwwer | S08 |
| FIX-10 | TECH | Project invite accept page stuck on "Accepting invitation..." (#35) | P0 | 1 | - | V1.0 | DONE | wwwer | S08 |
| FIX-11 | TECH | Org switcher not updated after project invite accept (#36) | P1 | 1 | FIX-10 | V1.0 | DONE | wwwer | S08 |
| FIX-12 | TECH | Removed project member sees generic error instead of clear message (#37) | P1 | 1 | - | V1.0 | DONE | wwwer | S08 |
| FIX-13 | TECH | WebSocket hooks unstable effect dependencies — double-connect (#40) | P1 | 1 | - | V1.0 | DONE | wwwer | S08 |
| FIX-14 | TECH | Invitation review page UX — review-before-accept flow with invitation details | P1 | 2 | FIX-10 | V1.0 | DONE | wwwer | S09 |
| UX-01 | TECH | Invitation flow blockers + recovery | P0 | 2 | FIX-14 | V1.0 | DONE | wwwer | S10 |
| UX-02 | TECH | Notification center IA + accessibility baseline | P1 | 2 | UX-01 | V1.0 | DONE | wwwer | S10 |
| UX-03 | TECH | Membership actions safety + copy clarity | P1 | 2 | FIX-08 | V1.0 | DONE | wwwer | S10 |
| UX-04 | TECH | Profile settings usability batch | P1 | 2 | FIX-04, FIX-05 | V1.0 | DONE | wwwer | S10 |
| UX-05 | TECH | Visual consistency polish pass (stretch) | P2 | 2 | UX-01, UX-02, UX-03, UX-04 | V1.0 | DONE | wwwer | S10 stretch |
| FIX-15 | TECH | Blocking sync file I/O in async handlers — avatars + attachments (#42) | P3 | 1 | - | V1.1 | READY | - | S10 stretch |
| FIX-16 | TECH | AI preferences update bypasses service layer (#43) | P3 | 1 | - | V1.1 | READY | - | S10 stretch |
| FIX-17 | TECH | AI service mock-provider tests fail in live mode — mock _complete_from_service | P2 | 1 | - | V1.0 | DONE | wwwer | S10 stretch |

---

## Release Buckets

### V1.0 (Completed)

| Item ID   | Title                                                                                               | Points | Sprint |
| --------- | --------------------------------------------------------------------------------------------------- | ------ | ------ |
| TECH-01   | Frontend Automated Audit                                                                            | 2      | S01    |
| TECH-02   | Frontend Standards Review                                                                           | 5      | S01    |
| TECH-03-A | Fix failing Gantt tests — export TaskDetailPanel from tasks barrel (#27)                            | 1      | S02    |
| TECH-03-B | Remove dead code — unused imports, dead files/exports, non-functional UI (#28 #32 #36 #42 #49)      | 2      | S02    |
| TECH-03-C | Fix `any` types in test files (#29)                                                                 | 1      | S02    |
| TECH-03-D | Fix query key namespacing + Zustand selectors (#34 #38 #45)                                         | 1      | S02    |
| TECH-03-E | Fix cross-feature internal imports (11 files) (#33 #37 #39 #40 #44 #47 #48 #50 #52 #54 #55)         | 2      | S02    |
| TECH-04-A | Batch error state fixes — OrgSwitcher, Kanban drag, Calendar exceptions, Resources (#41 #43 #51 #56) | 2      | S03    |
| TECH-04-B | ProfilePage AI error state + remove double refetch (#35)                                            | 1      | S03    |
| TECH-04-C | Fix setState in useEffect — CalendarPage + TasksPage (#26)                                          | 1      | S03    |
| TECH-04-D | Fix useLayoutEffect missing deps in useCollapsedTree (#30)                                          | 1      | S03    |
| TECH-04-E | Fix Gantt milestone/summary click opens detail panel (#46)                                          | 1      | S03    |
| TECH-04-F | Fix AI stream error event field name mismatch (#53)                                                 | 1      | S03    |
| KB-01     | Kanban: task detail panel from card (FR-KB-008)                                                     | 2      | S04    |
| KB-02     | Kanban: card reordering within column (FR-KB-009)                                                   | 2      | S05    |
| KB-03     | Kanban: WIP limits per column (FR-KB-010)                                                           | 2      | S04    |
| KB-04     | Kanban: swimlanes by assignee/priority (FR-KB-011)                                                  | 3      | S05    |
| KB-05     | Kanban: keyboard shortcuts (FR-KB-012)                                                              | 2      | S05    |
| KB-06     | Kanban: bulk select and move cards (FR-KB-013)                                                      | 2      | S05    |
| KB-07     | Kanban: assignee avatar on card (FR-KB-014)                                                         | 1      | S04    |
| KB-08     | Kanban: dependency indicator on card (FR-KB-015)                                                    | 1      | S04    |
| KB-09     | Kanban: AI sprint health summary (FR-KB-016)                                                        | 3      | S06    |
| FIX-01    | Avatar upload crashes with raw Pydantic error in UI (#27)                                           | 1      | S07    |
| FIX-02    | Deleted org name/slug not released after soft delete (#31)                                          | 1      | S07    |
| FIX-03    | Sidebar no fallback to personal org after deletion (#32)                                            | 1      | S07    |
| FIX-04    | Change password success not using Sonner toast (#29)                                                | 1      | S07    |
| FIX-05    | AI preferences toggle glitch — no confirmation + icon flash (#30)                                   | 1      | S07    |
| FIX-09    | Commit Vite WS proxy fix — add ws:true to /api proxy (#39)                                          | 1      | S08    |
| FIX-10    | Project invite accept page stuck on "Accepting invitation..." (#35)                                 | 1      | S08    |
| FIX-11    | Org switcher not updated after project invite accept (#36)                                          | 1      | S08    |
| FIX-12    | Removed project member sees generic error instead of clear message (#37)                             | 1      | S08    |
| FIX-13    | WebSocket hooks unstable effect dependencies — double-connect (#40)                                  | 1      | S08    |
| FIX-06    | Silent token refresh not proactive — user kicked to /login after idle (#26)                         | 2      | S09    |
| FIX-08    | Org member role change shows layout glitch (#33)                                                    | 1      | S09    |
| FIX-14    | Invitation review page UX — review-before-accept flow with invitation details                        | 2      | S09    |
| UX-01     | Invitation flow blockers + recovery                                                                    | 2      | S10    |
| UX-02     | Notification center IA + accessibility baseline                                                        | 2      | S10    |
| UX-03     | Membership actions safety + copy clarity                                                               | 2      | S10    |
| UX-04     | Profile settings usability batch                                                                       | 2      | S10    |
| UX-05     | Visual consistency polish pass (stretch)                                                               | 2      | S10    |
| FIX-17    | AI service mock-provider tests fail in live mode — mock _complete_from_service                        | 1      | S10    |

### V1.0 (Remaining Backlog)

| Item ID | Title                                            | Points | Status | Notes                        |
| ------- | ------------------------------------------------ | ------ | ------ | ---------------------------- |
| FIX-07   | Password reset allows reuse of previous password (#28) | 1      | READY | - |

### V1.1 (Planned)

| Item ID | Title                                              | Points | Status    | Notes                       |
| ------- | -------------------------------------------------- | ------ | --------- | --------------------------- |
| KB-10   | Kanban: AI quick-fill from title (FR-KB-017)        | 2      | NOT_READY | Depends on `KB-01`          |
| KB-11   | Kanban: AI-detected blockers highlight (FR-KB-018)  | 2      | NOT_READY | Depends on `KB-09`          |

---

## Backlog Hygiene Checklist

- Remove duplicates.
- Split all `13` point items before sprint commitment.
- Ensure each committed item has clear acceptance criteria in requirements/design docs.
- Keep `Status` and `Planned Sprint` synchronized with `sprint-plan.md`.
