# Sophikon V1 - User Stories

**Version:** 4.0
**Date:** 2026-03-20
**Scope:** User stories only (user intent and business value)

---

## Status Legend

- `DONE`: Implemented and evidenced in current codebase.
- `PARTIAL`: Some support exists, but full acceptance coverage is not evidenced.
- `PENDING`: Not evidenced in current mounted product surface.

Status baseline comes from `docs/03-implementation/requirements-traceability.md`, with targeted code verification where needed.

---

## Personas

- Project Manager (PM): plans work, owns timelines and resources.
- Team Lead (TL): coordinates team execution and assignments.
- Team Member (TM): executes assigned work and updates progress.
- Stakeholder (SH): needs high-level visibility and reporting.

---

## Epic 1: Project Setup & Management

| ID     | User Story                                                                                                | Status  |
| ------ | --------------------------------------------------------------------------------------------------------- | ------- |
| US-1.1 | As a PM, I want to create a new project so that I can start planning work.                                | DONE    |
| US-1.2 | As a PM, I want AI to generate an initial project plan from a description so that I can bootstrap faster. | PENDING |
| US-1.3 | As a PM, I want to import an existing project so that I can migrate planning data.                        | PENDING |
| US-1.4 | As a PM, I want a project dashboard so that I can assess project health quickly.                          | DONE    |

## Epic 2: Task Management

| ID     | User Story                                                                                   | Status  |
| ------ | -------------------------------------------------------------------------------------------- | ------- |
| US-2.1 | As a PM, I want to add tasks so that project work is defined.                                | DONE    |
| US-2.2 | As a PM, I want to edit task properties so that each task is fully specified.                | DONE    |
| US-2.3 | As a PM, I want to build a WBS hierarchy so that tasks are structured clearly.               | DONE    |
| US-2.4 | As a PM, I want to create dependencies so that schedule logic is enforced.                   | DONE    |
| US-2.5 | As a PM, I want AI task estimation so that planning estimates are faster and more realistic. | PARTIAL |
| US-2.6 | As a team member, I want to update task progress so that project status stays accurate.      | DONE    |

## Epic 3: Resource Management

| ID     | User Story                                                                                  | Status  |
| ------ | ------------------------------------------------------------------------------------------- | ------- |
| US-3.1 | As a PM, I want to add resources so that work can be staffed.                               | PARTIAL |
| US-3.2 | As a PM, I want to assign resources to tasks so that ownership and allocation are explicit. | PARTIAL |
| US-3.3 | As a PM, I want to view utilization so that I can detect over/under allocation.             | PARTIAL |
| US-3.4 | As a PM, I want AI-driven resource optimization so that rebalancing is easier.              | PENDING |

## Epic 4: Gantt Chart

| ID     | User Story                                                                                      | Status  |
| ------ | ----------------------------------------------------------------------------------------------- | ------- |
| US-4.1 | As a PM, I want a Gantt chart view so that I can visualize timeline and sequencing.             | DONE    |
| US-4.2 | As a PM, I want zoom and navigation controls so that I can inspect different planning horizons. | PARTIAL |
| US-4.3 | As a PM, I want interactive Gantt editing so that I can adjust plans directly on the timeline.  | PARTIAL |
| US-4.4 | As a PM, I want critical path highlighting so that I can focus on schedule-driving work.        | DONE    |

## Epic 5: AI Assistant

| ID     | User Story                                                                                                         | Status  |
| ------ | ------------------------------------------------------------------------------------------------------------------ | ------- |
| US-5.1 | As a team member, I want to chat with project data in natural language so that I can retrieve information quickly. | PARTIAL |
| US-5.2 | As a PM, I want AI chat actions with confirmation so that I can apply changes safely from chat.                    | DONE    |
| US-5.3 | As a PM, I want AI risk alerts so that I can react before problems escalate.                                       | DONE    |
| US-5.4 | As a PM, I want AI-generated weekly reports so that stakeholder communication is faster.                           | PENDING |

## Epic 6: Collaboration

| ID     | User Story                                                                                       | Status |
| ------ | ------------------------------------------------------------------------------------------------ | ------ |
| US-6.1 | As a PM, I want to invite team members so that we can collaborate in one workspace.              | DONE   |
| US-6.2 | As a team member, I want real-time updates so that I always see current project data.            | DONE   |
| US-6.3 | As a team member, I want task comments and mentions so that work communication stays contextual. | DONE   |

## Epic 7: Baseline & Tracking

| ID     | User Story                                                                     | Status  |
| ------ | ------------------------------------------------------------------------------ | ------- |
| US-7.1 | As a PM, I want to save a baseline so that I can preserve a planning snapshot. | PENDING |
| US-7.2 | As a PM, I want to compare to baseline so that variance is visible.            | PENDING |

## Epic 8: Import/Export

| ID     | User Story                                                                                    | Status  |
| ------ | --------------------------------------------------------------------------------------------- | ------- |
| US-8.1 | As a PM, I want to export to MS Project XML so that I can exchange plans with external tools. | PENDING |
| US-8.2 | As a PM, I want to export Gantt views to PNG so that I can share visual plan snapshots.        | PENDING |

## Epic 9: Organization Management

| ID     | User Story                                                                                      | Status |
| ------ | ----------------------------------------------------------------------------------------------- | ------ |
| US-9.1 | As an organization owner/admin, I want to edit organization settings so that org metadata stays accurate. | DONE |
| US-9.2 | As an organization owner/admin, I want to invite members and manage roles so that access is controlled. | DONE |
| US-9.3 | As a user in multiple organizations, I want to switch active organization context so I work in the right workspace. | DONE |
| US-9.4 | As an organization stakeholder, I want an organization dashboard so that I can monitor overall execution and risk. | DONE |

## Epic 10: Account & AI Controls

| ID      | User Story                                                                                          | Status |
| ------- | --------------------------------------------------------------------------------------------------- | ------ |
| US-10.1 | As a user, I want to upload or remove my avatar so that my profile identity is represented in collaboration surfaces. | DONE |
| US-10.2 | As a user, I want to configure AI preferences and tool auto-approval so that AI behavior matches my risk tolerance. | DONE |
| US-10.3 | As a user, I want to browse and resume prior AI conversations so that I can continue earlier workflows. | DONE |
| US-10.4 | As a user, I want to approve or redirect AI-generated execution plans so that autonomous changes remain controlled. | DONE |
| US-10.5 | As a user, I want to manage notification delivery settings so that alert channels match my preferences. | DONE |

## Epic 11: Reporting

| ID      | User Story                                                                                 | Status  |
| ------- | ------------------------------------------------------------------------------------------ | ------- |
| US-11.1 | As a PM, I want a dedicated reports workspace so that reporting is discoverable in project navigation. | DONE    |
| US-11.2 | As a PM, I want actionable report widgets (health, budget, performance) so that I can analyze outcomes. | PENDING |

## Epic 12: Kanban Board

| ID      | User Story                                                                                                                    | Status  |
| ------- | ----------------------------------------------------------------------------------------------------------------------------- | ------- |
| US-12.1 | As a TM, I want to see my tasks on a Kanban board so that I can manage daily work without reading a Gantt chart.              | DONE    |
| US-12.2 | As a TM, I want to drag a card to a different column so that I can update task status directly on the board.                  | DONE    |
| US-12.3 | As a TM, I want to open a task detail panel from a card so that I can view and edit details without leaving the board.        | PENDING |
| US-12.4 | As a TL, I want to reorder cards within a column so that I can prioritize work visually.                                      | PENDING |
| US-12.5 | As a TL, I want to set WIP limits per column so that the team does not take on more than it can complete.                     | PENDING |
| US-12.6 | As a TL, I want to group cards into swimlanes by assignee or priority so that workload distribution is visible at a glance.   | PENDING |
| US-12.7 | As a TM, I want keyboard shortcuts on the board so that I can navigate and create cards without reaching for the mouse.       | PENDING |
| US-12.8 | As a TL, I want to select multiple cards and move them at once so that bulk status changes are fast.                          | PENDING |
| US-12.9 | As a TM, I want to see the assignee avatar on each card so that I know who owns each task without opening it.                 | PENDING |
| US-12.10 | As a TM, I want to see a dependency indicator on a card so that I know when a task is blocked before I start work on it.    | PENDING |
| US-12.11 | As a PM, I want an AI sprint health summary so that I can see which cards are at risk without reading every card individually. | PENDING |
| US-12.12 | As a TM, I want AI to fill in card details from a title so that creating a well-specified task takes seconds.                 | PENDING |
| US-12.13 | As a TL, I want AI to highlight cards with unresolved blockers or no recent activity so that stalled work is visible.         | PENDING |

## Epic 13: Account Lifecycle

| ID      | User Story                                                                                            | Status |
| ------- | ----------------------------------------------------------------------------------------------------- | ------ |
| US-13.1 | As a newly registered user, I want to verify my email from a link so that my account is trusted.     | DONE   |
| US-13.2 | As a user, I want to resend verification email when needed so that I can complete account activation. | DONE   |
| US-13.3 | As an authenticated user, I want to change my password so that I can maintain account security.      | DONE   |

---

## Story Status Summary

| Status  | Count |
| ------- | ----- |
| DONE    | 28    |
| PARTIAL | 7     |
| PENDING | 20    |

---

## Document History

| Version | Date       | Author | Changes |
| ------- | ---------- | ------ | ------- |
| 3.0     | 2026-03-20 | Codex  | Cleaned to user-story-only content and added explicit DONE/PARTIAL/PENDING status column for every story. |
| 4.0     | 2026-03-20 | Codex  | Coverage hardening pass: added user stories for organization management, account settings/AI controls, reporting workspace, and account lifecycle flows to trace shipped surfaces. |
| 4.1     | 2026-03-20 | Codex  | Consistency pass with FR/design docs: aligned US-8.2 export format from PDF to PNG to match current functional requirement and API design surface. |
| 4.2     | 2026-03-20 | Codex  | Consistency pass with FR status matrix: aligned US-2.4, US-2.6, and US-4.4 to DONE where mapped FRs are DONE and design/code evidence is present. |
| 5.0     | 2026-03-23 | wwwer  | Added Epic 12 (Kanban Board) with US-12.1–12.13 covering board basics, task detail panel, card reordering, WIP limits, swimlanes, keyboard shortcuts, bulk operations, assignee avatar, dependency indicators, and AI board features. Renumbered former Epic 12 to Epic 13. |
