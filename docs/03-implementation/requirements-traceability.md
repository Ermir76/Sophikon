# Requirements Traceability Matrix

**Created:** 2026-03-06
**Purpose:** Current-state traceability for functional requirements and user stories against the committed codebase.

---

## Scope And Method

This document records what is evidenced by the current codebase review.

- It does not delete or rewrite the planned documents.
- It separates `Implemented`, `Partial`, and `Not evidenced in current mounted surface`.
- It is based on code inspection of mounted backend routers, frontend routes/pages/components, and current ORM/service surface.
- It is not a runtime test report.

---

## Status Legend

- `Implemented`: a concrete backend/frontend code path was found for the requirement/story.
- `Partial`: some supporting code exists, but full parity with the original requirement/story was not proven from this pass.
- `Not evidenced`: no matching mounted route/page/component flow was found in the current audited surface.

---

## Evidence Anchors

- `A1` Auth surface: `backend/app/api/v1/endpoints/auth.py`, `frontend/src/features/auth/api/auth.service.ts`, `frontend/src/features/auth/pages/LoginPage.tsx`, `frontend/src/features/auth/pages/RegisterPage.tsx`, `frontend/src/features/auth/pages/VerifyEmailPage.tsx`, `frontend/src/app/App.tsx`
- `A2` Organization surface: `backend/app/api/v1/endpoints/organizations.py`, `backend/app/api/v1/endpoints/organization_members.py`, `frontend/src/features/organizations/*`, `frontend/src/app/App.tsx`
- `A3` Project and insights surface: `backend/app/api/v1/endpoints/projects.py`, `backend/app/api/v1/endpoints/insights.py`, `backend/app/api/v1/endpoints/activity.py`, `frontend/src/features/projects/*`, `frontend/src/features/dashboard/*`, `frontend/src/app/App.tsx`
- `A4` Task, dependency, and assignment surface: `backend/app/api/v1/endpoints/tasks.py`, `backend/app/api/v1/endpoints/dependencies.py`, `backend/app/api/v1/endpoints/assignments.py`, `backend/app/service/dependency_service.py`, `frontend/src/features/tasks/*`
- `A5` Schedule, gantt, and calendar surface: `backend/app/api/v1/endpoints/schedule.py`, `backend/app/api/v1/endpoints/calendars.py`, `frontend/src/features/gantt/*`, `frontend/src/features/calendar/*`, `frontend/src/app/App.tsx`
- `A6` Resource and utilization surface: `backend/app/api/v1/endpoints/resources.py`, `backend/app/api/v1/endpoints/utilization.py`, `frontend/src/features/resources/*`, `frontend/src/app/App.tsx`
- `A7` AI surface: `backend/app/api/v1/endpoints/ai.py`, `backend/app/service/ai_service.py`, `ai-service/app/main.py`, `frontend/src/features/ai/*`
- `A8` Mounted backend scope boundary: `backend/app/main.py`
- `A9` Mounted frontend route boundary: `frontend/src/app/App.tsx`

---

## Functional Requirements

### 3.1 Authentication & User Management

| ID        | Status        | Evidence | Note                                                                          |
| --------- | ------------- | -------- | ----------------------------------------------------------------------------- |
| FR-AU-001 | Implemented   | A1       | Register flow exists in backend and frontend.                                 |
| FR-AU-002 | Implemented   | A1       | Login flow exists in backend and frontend.                                    |
| FR-AU-003 | Not evidenced | A1, A8   | No Google OAuth route is mounted in current auth endpoints.                   |
| FR-AU-004 | Implemented   | A1       | Logout flow exists in backend and auth store.                                 |
| FR-AU-005 | Not evidenced | A1, A8   | No password-reset routes found in current mounted auth surface.               |
| FR-AU-006 | Not evidenced | A1, A8   | No profile update route/page found in current mounted surface.                |
| FR-AU-007 | Implemented   | A1       | Refresh-token flow exists, using cookies rather than exposed bearer-token UI. |
| FR-AU-008 | Not evidenced | A1, A8   | No session-management route/page found in current mounted surface.            |

### 3.2 Project Management

| ID        | Status        | Evidence | Note                                                                                                                                                                            |
| --------- | ------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-PM-001 | Implemented   | A3       | Project create flow exists.                                                                                                                                                     |
| FR-PM-002 | Implemented   | A3       | Project update flow exists.                                                                                                                                                     |
| FR-PM-003 | Implemented   | A3       | Project delete flow exists.                                                                                                                                                     |
| FR-PM-004 | Implemented   | A3       | Project list flow exists.                                                                                                                                                       |
| FR-PM-005 | Implemented   | A3, A7   | `GET /projects/:id/dashboard` is mounted, the project overview page renders dashboard sections and drill-downs, and the page composes AI suggestions as dashboard risk signals. |
| FR-PM-006 | Partial       | A3       | Project status can be patched, but full workflow parity was not separately audited.                                                                                             |
| FR-PM-007 | Not evidenced | A3, A8   | No project-duplicate route/page found in current mounted surface.                                                                                                               |
| FR-PM-008 | Partial       | A3       | Backend project patch surface exists; explicit default-calendar workflow was not fully audited.                                                                                 |

### 3.3 Task Management

| ID        | Status      | Evidence | Note                                                                                                                                                                 |
| --------- | ----------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-TM-001 | Implemented | A4       | Task create flow exists.                                                                                                                                             |
| FR-TM-002 | Implemented | A4       | Task edit/detail update flow exists.                                                                                                                                 |
| FR-TM-003 | Implemented | A4       | Task delete flow exists.                                                                                                                                             |
| FR-TM-004 | Implemented | A4       | Indent/outdent hierarchy actions exist.                                                                                                                              |
| FR-TM-005 | Partial     | A4       | `wbs_code` exists and hierarchy services are present; full WBS-generation behavior was not runtime-verified.                                                         |
| FR-TM-006 | Implemented | A4       | Reorder route and UI hooks exist.                                                                                                                                    |
| FR-TM-007 | Implemented | A4       | Duration is part of task create/update types and UI.                                                                                                                 |
| FR-TM-008 | Implemented | A4       | Milestone field exists in current task types/models.                                                                                                                 |
| FR-TM-009 | Partial     | A4       | Constraint fields exist in current task model/types; full UX parity was not fully audited.                                                                           |
| FR-TM-010 | Partial     | A4       | Task-type fields exist in current task model/types; full UX parity was not fully audited.                                                                            |
| FR-TM-011 | Implemented | A4       | Progress fields and update flow exist.                                                                                                                               |
| FR-TM-012 | Implemented | A4       | Task notes field and edit flow exist.                                                                                                                                |
| FR-TM-013 | Implemented | A4       | Summary tasks auto-roll up span dates/duration, work, cost, and progress across child changes and scheduling; computed summary fields are rejected on direct update. |
| FR-TM-014 | Implemented | A4       | Bulk create/update/delete task flows exist, including per-item success/failure reporting for PATCH `/tasks/bulk` validation outcomes.                                |
| FR-TM-015 | Partial     | A4       | Work fields exist in current task model/types; end-to-end workflow not fully audited.                                                                                |
| FR-TM-016 | Partial     | A4       | Actual-date fields exist in current task model/types; end-to-end workflow not fully audited.                                                                         |

### 3.4 Dependency Management

| ID        | Status      | Evidence | Note                                                         |
| --------- | ----------- | -------- | ------------------------------------------------------------ |
| FR-DM-001 | Implemented | A4       | Dependency create flow exists.                               |
| FR-DM-002 | Implemented | A4       | FF dependency type is supported by current types/schema/UI.  |
| FR-DM-003 | Implemented | A4       | SS dependency type is supported by current types/schema/UI.  |
| FR-DM-004 | Implemented | A4       | SF dependency type is supported by current types/schema/UI.  |
| FR-DM-005 | Implemented | A4       | Lag fields exist in current schema/UI.                       |
| FR-DM-006 | Implemented | A4       | Dependency delete flow exists.                               |
| FR-DM-007 | Implemented | A4       | Circular-dependency check exists in `dependency_service.py`. |
| FR-DM-008 | Implemented | A4       | `is_disabled` is supported in current schema/UI.             |

### 3.5 Scheduling Engine

| ID        | Status        | Evidence | Note                                                                                                                                                                                                     |
| --------- | ------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-SE-001 | Implemented   | A5       | Schedule calculation endpoint exists.                                                                                                                                                                    |
| FR-SE-002 | Implemented   | A5       | Critical-path endpoint exists.                                                                                                                                                                           |
| FR-SE-003 | Partial       | A5       | Slack fields exist in models; current end-to-end behavior was not fully audited.                                                                                                                         |
| FR-SE-004 | Implemented   | A4, A5   | ASAP behavior is evidenced by the scheduler's earliest-start forward-pass default when no stricter constraint applies, and integration scheduling flows cover dependency-driven earliest-start outcomes. |
| FR-SE-005 | Partial       | A4, A5   | ALAP exists in current constraint types; behavior-level verification was not completed.                                                                                                                  |
| FR-SE-006 | Partial       | A4, A5   | Constraint fields exist; behavior-level verification was not completed.                                                                                                                                  |
| FR-SE-007 | Not evidenced | A4, A5   | No clear automatic recalculation trigger was verified from this pass.                                                                                                                                    |
| FR-SE-008 | Partial       | A5       | Forward-scheduling intent is present, but behavior-level verification was not completed.                                                                                                                 |

### 3.6 Gantt Chart

| ID        | Status        | Evidence | Note                                                                                         |
| --------- | ------------- | -------- | -------------------------------------------------------------------------------------------- |
| FR-GC-001 | Implemented   | A5       | Gantt chart rendering exists.                                                                |
| FR-GC-002 | Implemented   | A5       | Bars are date-positioned in current chart code.                                              |
| FR-GC-003 | Implemented   | A5       | Bar length is driven by duration/date span.                                                  |
| FR-GC-004 | Implemented   | A5       | Hierarchy is rendered in current gantt table/chart.                                          |
| FR-GC-005 | Implemented   | A5       | Dependency arrows/lines are rendered.                                                        |
| FR-GC-006 | Implemented   | A5       | Progress is rendered in current gantt surface.                                               |
| FR-GC-007 | Implemented   | A5       | Milestones are rendered.                                                                     |
| FR-GC-008 | Implemented   | A5       | Summary tasks are rendered.                                                                  |
| FR-GC-009 | Implemented   | A5       | Timeline header exists.                                                                      |
| FR-GC-010 | Implemented   | A5       | Zoom controls/state exist.                                                                   |
| FR-GC-011 | Implemented   | A5       | Horizontal scrolling exists.                                                                 |
| FR-GC-012 | Implemented   | A5       | Vertical scrolling exists.                                                                   |
| FR-GC-013 | Implemented   | A5       | Today line and "scroll to today" exist.                                                      |
| FR-GC-014 | Partial       | A5       | Critical-path toggle and rendering hooks exist; full visual parity was not runtime-verified. |
| FR-GC-015 | Implemented   | A5       | Task click selection exists.                                                                 |
| FR-GC-016 | Not evidenced | A5, A9   | No double-click-to-open flow was verified from this pass.                                    |
| FR-GC-017 | Not evidenced | A5, A9   | No drag-to-change-dates flow was verified from this pass.                                    |
| FR-GC-018 | Not evidenced | A5, A9   | No drag-edge resize flow was verified from this pass.                                        |
| FR-GC-019 | Not evidenced | A5, A9   | No drag-to-create-dependency flow was verified from this pass.                               |
| FR-GC-020 | Not evidenced | A5, A9   | No gantt context-menu flow was verified from this pass.                                      |

### 3.7 Calendar Management

| ID        | Status        | Evidence | Note                                                                                                    |
| --------- | ------------- | -------- | ------------------------------------------------------------------------------------------------------- |
| FR-CA-001 | Implemented   | A5       | Calendar create route exists.                                                                           |
| FR-CA-002 | Partial       | A5       | Calendar patch route exists; full work-week UI parity was not audited.                                  |
| FR-CA-003 | Implemented   | A5       | Calendar-exception create route exists.                                                                 |
| FR-CA-004 | Implemented   | A5       | Calendar-exception delete route exists.                                                                 |
| FR-CA-005 | Partial       | A5       | Base-calendar/inheritance fields exist; end-to-end workflow not fully audited.                          |
| FR-CA-006 | Not evidenced | A4, A5   | No current task calendar assignment workflow was evidenced in the mounted frontend/backend surface.     |
| FR-CA-007 | Not evidenced | A5, A6   | No current resource calendar assignment workflow was evidenced in the mounted frontend/backend surface. |

### 3.8 Resource Management

| ID        | Status        | Evidence | Note                                                                                                               |
| --------- | ------------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| FR-RM-001 | Implemented   | A6       | Work-resource create flow exists.                                                                                  |
| FR-RM-002 | Implemented   | A6       | Material-resource create flow exists.                                                                              |
| FR-RM-003 | Implemented   | A6       | Cost-resource create flow exists.                                                                                  |
| FR-RM-004 | Implemented   | A6       | Resource edit flow exists.                                                                                         |
| FR-RM-005 | Implemented   | A6       | Resource delete flow exists.                                                                                       |
| FR-RM-006 | Partial       | A6       | Default rate fields are editable on current resources, but the planned dedicated rates API surface is not mounted. |
| FR-RM-007 | Not evidenced | A6, A8   | No availability-management route/page was evidenced in the mounted surface.                                        |
| FR-RM-008 | Not evidenced | A6, A8   | Resource `user_id` exists in schema/model, but a current linking workflow was not evidenced.                       |
| FR-RM-009 | Not evidenced | A6, A8   | No resource-group workflow was evidenced in the mounted surface.                                                   |

### 3.9 Assignment Management

| ID        | Status      | Evidence | Note                                                                                                           |
| --------- | ----------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| FR-AS-001 | Implemented | A4       | Assignment create flow exists.                                                                                 |
| FR-AS-002 | Implemented | A4       | Allocation `units` are supported in current UI/schema.                                                         |
| FR-AS-003 | Implemented | A4       | Assignment delete flow exists.                                                                                 |
| FR-AS-004 | Partial     | A4       | `work_contour` exists in current schema/model, but explicit UI parity was not fully audited.                   |
| FR-AS-005 | Partial     | A4       | `actual_work` and `percent_work_complete` exist in schema/model, but explicit UI parity was not fully audited. |
| FR-AS-006 | Implemented | A6       | Resource workload/utilization page exists.                                                                     |
| FR-AS-007 | Implemented | A6       | Over-allocation warnings/list exist.                                                                           |

### 3.10 Baseline Management

| ID        | Status        | Evidence | Note                                  |
| --------- | ------------- | -------- | ------------------------------------- |
| FR-BL-001 | Not evidenced | A8, A9   | No mounted baseline route/page found. |
| FR-BL-002 | Not evidenced | A8, A9   | No mounted baseline route/page found. |
| FR-BL-003 | Not evidenced | A8, A9   | No mounted baseline route/page found. |
| FR-BL-004 | Not evidenced | A8, A9   | No mounted baseline route/page found. |
| FR-BL-005 | Not evidenced | A8, A9   | No mounted baseline route/page found. |
| FR-BL-006 | Not evidenced | A8, A9   | No mounted baseline route/page found. |

### 3.11 Time Tracking

| ID        | Status        | Evidence | Note                                    |
| --------- | ------------- | -------- | --------------------------------------- |
| FR-TT-001 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-002 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-003 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-004 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-005 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-006 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |
| FR-TT-007 | Not evidenced | A8, A9   | No mounted time-entry route/page found. |

### 3.12 AI Features

| ID        | Status        | Evidence | Note                                                                                                             |
| --------- | ------------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| FR-AI-001 | Implemented   | A7       | Project-scoped chat flow exists.                                                                                 |
| FR-AI-002 | Implemented   | A7       | Chat feature exists with project/task context surface.                                                           |
| FR-AI-003 | Partial       | A7       | Status-style project questions are supported by current AI surface, but broad coverage was not formally audited. |
| FR-AI-004 | Not evidenced | A7, A9   | No chat-command mutation-with-confirmation flow was evidenced.                                                   |
| FR-AI-005 | Implemented   | A7       | Estimate flow exists.                                                                                            |
| FR-AI-006 | Implemented   | A7       | Estimate reasoning is surfaced.                                                                                  |
| FR-AI-007 | Implemented   | A7       | Multi-task estimation surface exists in the docked panel.                                                        |
| FR-AI-008 | Implemented   | A7       | Suggestions flow exists.                                                                                         |
| FR-AI-009 | Implemented   | A7       | Streaming chat flow exists.                                                                                      |

### 3.13 Collaboration

| ID        | Status        | Evidence   | Note                                                                                                                                                                                            |
| --------- | ------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-CO-001 | Implemented   | A3, A8, A9 | Project invite flow is mounted in backend and frontend, including email invitation acceptance routing.                                                                                          |
| FR-CO-002 | Implemented   | A3, A8, A9 | Project member role change flow is mounted for owners via project member endpoints and settings UI.                                                                                             |
| FR-CO-003 | Implemented   | A3, A8, A9 | Project member removal flow is mounted with role-aware enforcement and settings UI actions.                                                                                                     |
| FR-CO-004 | Implemented   | A3, A8, A9 | Project member list flow is mounted in backend and displayed in the project settings members tab.                                                                                               |
| FR-CO-005 | Implemented   | A3, A8, A9 | A mounted websocket endpoint now exists at `/api/v1/ws/projects/{project_id}`, project mutation/activity flows publish realtime events after commit, and the frontend mounts a project-scoped websocket hook that invalidates live data on receipt. |
| FR-CO-006 | Implemented   | A3, A8, A9 | Project presence is tracked over the websocket protocol and surfaced in the app header as connected-user avatars with live connection state on project routes.                                                                        |
| FR-CO-007 | Implemented   | A3, A8, A9 | Project activity logging is mounted at `GET /projects/{id}/activity`, mutation flows write audit entries, and the project overview page renders the dedicated activity feed from that endpoint. |
| FR-CO-008 | Not evidenced | A8, A9     | No mounted task-comment flow found.                                                                                                                                                             |
| FR-CO-009 | Not evidenced | A8, A9     | No mounted mention flow found.                                                                                                                                                                  |
| FR-CO-010 | Not evidenced | A8, A9     | No mounted attachment flow found.                                                                                                                                                               |
| FR-CO-011 | Not evidenced | A8, A9     | No mounted notification flow found.                                                                                                                                                             |

### 3.14 Import/Export

| ID        | Status        | Evidence | Note                                       |
| --------- | ------------- | -------- | ------------------------------------------ |
| FR-IE-001 | Not evidenced | A8, A9   | No mounted export/import route/page found. |
| FR-IE-002 | Not evidenced | A8, A9   | No mounted export/import route/page found. |
| FR-IE-003 | Not evidenced | A8, A9   | No mounted export/import route/page found. |
| FR-IE-004 | Not evidenced | A8, A9   | No mounted export/import route/page found. |
| FR-IE-005 | Not evidenced | A8, A9   | No mounted export/import route/page found. |

### Future-Version Requirements

`FR-AI-020` through `FR-AI-025` and `FR-EN-001` through `FR-EN-006` remain planned, with one important exception: organization support corresponding to `FR-EN-001` is already partially implemented in the current codebase (`A2`), even though the requirement is still grouped under future versions.

---

## User Stories

| Story                              | Status        | Evidence   | Note                                                                                                                    |
| ---------------------------------- | ------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| US-1.1 Create New Project          | Implemented   | A3         | Project creation UI/backend exist.                                                                                      |
| US-1.2 Create Project with AI      | Not evidenced | A7, A9     | Current AI starts inside an existing project; no AI project-bootstrap flow was evidenced.                               |
| US-1.3 Import Existing Project     | Not evidenced | A8, A9     | No import surface was evidenced.                                                                                        |
| US-1.4 Project Dashboard           | Implemented   | A3, A7     | Project dashboard endpoint, overview page sections, drill-down links, and AI suggestion-backed risk widget are mounted. |
| US-2.1 Add Task                    | Implemented   | A4         | Add-task flows exist.                                                                                                   |
| US-2.2 Edit Task Properties        | Implemented   | A4         | Task detail/edit flows exist.                                                                                           |
| US-2.3 Create Task Hierarchy (WBS) | Implemented   | A4         | Indent/outdent/reorder hierarchy flows exist.                                                                           |
| US-2.4 Create Dependencies         | Partial       | A4, A5     | Dependency creation/editing exists, but gantt drag-link creation was not evidenced.                                     |
| US-2.5 AI Task Estimation          | Partial       | A7         | AI estimation exists, but not exactly in the story's dedicated task-row UX and not with historical-task evidence.       |
| US-2.6 Update Task Progress        | Partial       | A4         | Progress updates exist; progress notes/comments were not evidenced.                                                     |
| US-3.1 Add Resource                | Partial       | A6         | Resource creation exists, but not every acceptance item was fully evidenced.                                            |
| US-3.2 Assign Resource to Task     | Partial       | A4, A6     | Assignment flow exists, but gantt/dropdown-specific UX was not fully evidenced.                                         |
| US-3.3 View Resource Utilization   | Partial       | A6         | Utilization page exists; exact filter/summary parity was not fully audited.                                             |
| US-3.4 AI Resource Optimization    | Not evidenced | A7, A9     | No AI reallocation feature was evidenced.                                                                               |
| US-4.1 View Gantt Chart            | Implemented   | A5         | Core gantt view exists.                                                                                                 |
| US-4.2 Zoom & Navigate Gantt       | Partial       | A5         | Zoom and scroll exist; every navigation affordance from the story was not fully audited.                                |
| US-4.3 Interactive Gantt Editing   | Not evidenced | A5, A9     | Drag editing and context-menu behavior were not evidenced.                                                              |
| US-4.4 Critical Path Highlighting  | Partial       | A5         | Critical-path toggle/rendering exists; end-to-end parity was not runtime-verified.                                      |
| US-5.1 Chat with Project           | Partial       | A7         | Project-aware chat exists, but click-through entity navigation and some specific query types were not fully evidenced.  |
| US-5.2 AI Actions via Chat         | Not evidenced | A7, A9     | No free-form chat mutation flow was evidenced.                                                                          |
| US-5.3 AI Risk Alerts              | Partial       | A7         | Suggestions exist, but not proactive dashboard risk alerts.                                                             |
| US-5.4 AI Weekly Report            | Not evidenced | A7, A9     | No report-generation flow was evidenced.                                                                                |
| US-6.1 Invite Team Members         | Implemented   | A3, A8, A9 | Project-team invite, acceptance, and member management flows are mounted in the current collaboration surface.          |
| US-6.2 Real-time Updates           | Implemented   | A3, A8, A9 | Project-scoped websocket endpoint, presence snapshots/updates, and realtime mutation push flows are mounted in backend and consumed in frontend project routes. |
| US-6.3 Task Comments               | Not evidenced | A8, A9     | No task-comment flow was evidenced.                                                                                     |
| US-7.1 Save Baseline               | Not evidenced | A8, A9     | No baseline flow was evidenced.                                                                                         |
| US-7.2 Compare to Baseline         | Not evidenced | A8, A9     | No baseline flow was evidenced.                                                                                         |
| US-8.1 Export to MS Project XML    | Not evidenced | A8, A9     | No export flow was evidenced.                                                                                           |
| US-8.2 Export to PDF               | Not evidenced | A8, A9     | No export flow was evidenced.                                                                                           |

---

## Reading Rule

Use this file as the `current truth` companion to the planned docs:

- `docs/01-requirements/functional-requirements.md`
- `docs/01-requirements/user-stories.md`

When this matrix disagrees with the planned docs, treat the planned docs as intent and this file as the current audited implementation state.
