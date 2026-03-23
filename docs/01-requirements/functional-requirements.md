# Sophikon V1 - Functional Requirements

**Version:** 9.0
**Date:** 2026-03-20
**Scope:** V1 product requirements only (what the system must do)

---

## Status Legend

- `DONE`: Implemented and evidenced in current codebase.
- `PARTIAL`: Some support exists, but full requirement parity is not evidenced.
- `PENDING`: Not evidenced in current mounted product surface.

Status baseline comes from `docs/03-implementation/requirements-traceability.md`, with targeted code verification where needed.

---

## 1. Authentication & User Management

| ID        | Requirement                         | Priority | Status  |
| --------- | ----------------------------------- | -------- | ------- |
| FR-AU-001 | Register with email/password        | Must     | DONE    |
| FR-AU-002 | Login with email/password           | Must     | DONE    |
| FR-AU-003 | Login with Google OAuth             | Must     | DONE    |
| FR-AU-004 | Logout (revoke token)               | Must     | DONE    |
| FR-AU-005 | Password reset via email            | Should   | DONE    |
| FR-AU-006 | Update profile                      | Should   | DONE    |
| FR-AU-007 | JWT with refresh tokens             | Must     | DONE    |
| FR-AU-008 | Session management                  | Should   | PENDING |
| FR-AU-009 | Verify email via link               | Must     | DONE    |
| FR-AU-010 | Resend verification email           | Should   | DONE    |
| FR-AU-011 | Change password while authenticated | Must     | DONE    |
| FR-AU-012 | Upload/remove profile avatar        | Should   | DONE    |
| FR-AU-013 | Manage AI preferences for account   | Should   | DONE    |

## 2. Project Management

| ID        | Requirement           | Priority | Status  |
| --------- | --------------------- | -------- | ------- |
| FR-PM-001 | Create project        | Must     | DONE    |
| FR-PM-002 | Edit project          | Must     | DONE    |
| FR-PM-003 | Delete project (soft) | Must     | DONE    |
| FR-PM-004 | List user's projects  | Must     | DONE    |
| FR-PM-005 | Project dashboard     | Must     | DONE    |
| FR-PM-006 | Set project status    | Should   | PARTIAL |
| FR-PM-007 | Duplicate project     | Could    | PENDING |
| FR-PM-008 | Set default calendar  | Should   | PARTIAL |

## 3. Task Management

| ID        | Requirement                       | Priority | Status  |
| --------- | --------------------------------- | -------- | ------- |
| FR-TM-001 | Create task                       | Must     | DONE    |
| FR-TM-002 | Edit task                         | Must     | DONE    |
| FR-TM-003 | Delete task (soft)                | Must     | DONE    |
| FR-TM-004 | Create hierarchy (indent/outdent) | Must     | DONE    |
| FR-TM-005 | Auto-generate WBS codes           | Must     | PARTIAL |
| FR-TM-006 | Reorder tasks (drag/drop)         | Must     | DONE    |
| FR-TM-007 | Set duration                      | Must     | DONE    |
| FR-TM-008 | Set as milestone                  | Must     | DONE    |
| FR-TM-009 | Set constraint type               | Should   | PARTIAL |
| FR-TM-010 | Set task type (scheduling)        | Should   | PARTIAL |
| FR-TM-011 | Update progress                   | Must     | DONE    |
| FR-TM-012 | Add notes                         | Should   | DONE    |
| FR-TM-013 | Summary tasks auto-calculate      | Must     | DONE    |
| FR-TM-014 | Bulk operations                   | Should   | DONE    |
| FR-TM-015 | Set work (effort)                 | Should   | PARTIAL |
| FR-TM-016 | Track actual dates                | Should   | PARTIAL |

## 4. Dependency Management

| ID        | Requirement                   | Priority | Status |
| --------- | ----------------------------- | -------- | ------ |
| FR-DM-001 | Create FS dependency          | Must     | DONE   |
| FR-DM-002 | Create FF dependency          | Should   | DONE   |
| FR-DM-003 | Create SS dependency          | Should   | DONE   |
| FR-DM-004 | Create SF dependency          | Could    | DONE   |
| FR-DM-005 | Set lag time                  | Should   | DONE   |
| FR-DM-006 | Delete dependency             | Must     | DONE   |
| FR-DM-007 | Prevent circular dependencies | Must     | DONE   |
| FR-DM-008 | Disable dependency            | Should   | DONE   |

## 5. Scheduling Engine

| ID        | Requirement                | Priority | Status  |
| --------- | -------------------------- | -------- | ------- |
| FR-SE-001 | Calculate successor dates  | Must     | DONE    |
| FR-SE-002 | Calculate critical path    | Must     | DONE    |
| FR-SE-003 | Calculate slack/float      | Should   | PARTIAL |
| FR-SE-004 | Respect ASAP constraint    | Must     | DONE    |
| FR-SE-005 | Respect ALAP constraint    | Should   | PARTIAL |
| FR-SE-006 | Respect date constraints   | Should   | PARTIAL |
| FR-SE-007 | Auto-recalculate on change | Must     | DONE    |
| FR-SE-008 | Forward scheduling         | Must     | PARTIAL |

## 6. Gantt Chart

| ID        | Requirement                  | Priority | Status |
| --------- | ---------------------------- | -------- | ------ |
| FR-GC-001 | Display task bars            | Must     | DONE   |
| FR-GC-002 | Bar position reflects dates  | Must     | DONE   |
| FR-GC-003 | Bar length reflects duration | Must     | DONE   |
| FR-GC-004 | Show hierarchy               | Must     | DONE   |
| FR-GC-005 | Show dependencies            | Must     | DONE   |
| FR-GC-006 | Show progress                | Must     | DONE   |
| FR-GC-007 | Show milestones              | Must     | DONE   |
| FR-GC-008 | Show summary tasks           | Must     | DONE   |
| FR-GC-009 | Timeline header              | Must     | DONE   |
| FR-GC-010 | Zoom levels                  | Must     | DONE   |
| FR-GC-011 | Horizontal scroll            | Must     | DONE   |
| FR-GC-012 | Vertical scroll              | Must     | DONE   |
| FR-GC-013 | Today line                   | Must     | DONE   |
| FR-GC-014 | Critical path highlight      | Should   | DONE   |
| FR-GC-015 | Click to select              | Must     | DONE   |
| FR-GC-016 | Double-click for details     | Must     | DONE   |
| FR-GC-017 | Drag to change dates         | Could    | DONE   |
| FR-GC-018 | Drag edges for duration      | Could    | DONE   |
| FR-GC-019 | Drag to create dependency    | Could    | DONE   |
| FR-GC-020 | Context menu                 | Should   | DONE   |

## 7. Calendar Management

| ID        | Requirement                 | Priority | Status  |
| --------- | --------------------------- | -------- | ------- |
| FR-CA-001 | Create calendar             | Must     | DONE    |
| FR-CA-002 | Edit work week              | Must     | PARTIAL |
| FR-CA-003 | Add exception (holiday)     | Must     | DONE    |
| FR-CA-004 | Delete exception            | Must     | DONE    |
| FR-CA-005 | Calendar inheritance        | Should   | PARTIAL |
| FR-CA-006 | Assign calendar to task     | Should   | PARTIAL |
| FR-CA-007 | Assign calendar to resource | Should   | PARTIAL |

## 8. Resource Management

| ID        | Requirement              | Priority | Status  |
| --------- | ------------------------ | -------- | ------- |
| FR-RM-001 | Create work resource     | Must     | DONE    |
| FR-RM-002 | Create material resource | Should   | DONE    |
| FR-RM-003 | Create cost resource     | Could    | DONE    |
| FR-RM-004 | Edit resource            | Must     | DONE    |
| FR-RM-005 | Delete resource          | Must     | DONE    |
| FR-RM-006 | Set rates                | Must     | PARTIAL |
| FR-RM-007 | Set availability         | Should   | PENDING |
| FR-RM-008 | Link resource to user    | Should   | PENDING |
| FR-RM-009 | Resource groups          | Should   | PENDING |

## 9. Assignment Management

| ID        | Requirement             | Priority | Status  |
| --------- | ----------------------- | -------- | ------- |
| FR-AS-001 | Assign resource to task | Must     | DONE    |
| FR-AS-002 | Set allocation units    | Must     | DONE    |
| FR-AS-003 | Remove assignment       | Must     | DONE    |
| FR-AS-004 | Set work contour        | Should   | PARTIAL |
| FR-AS-005 | Track actual work       | Should   | PARTIAL |
| FR-AS-006 | View resource workload  | Must     | DONE    |
| FR-AS-007 | Over-allocation warning | Should   | DONE    |

## 10. Baseline Management

| ID        | Requirement                 | Priority | Status  |
| --------- | --------------------------- | -------- | ------- |
| FR-BL-001 | Save baseline               | Must     | PENDING |
| FR-BL-002 | Name baseline               | Must     | PENDING |
| FR-BL-003 | Multiple baselines (0-10)   | Should   | PENDING |
| FR-BL-004 | View baseline data          | Must     | PENDING |
| FR-BL-005 | Compare current vs baseline | Should   | PENDING |
| FR-BL-006 | Delete baseline             | Should   | PENDING |

## 11. Time Tracking

| ID        | Requirement            | Priority | Status  |
| --------- | ---------------------- | -------- | ------- |
| FR-TT-001 | Log time entry         | Must     | PENDING |
| FR-TT-002 | Edit time entry        | Must     | PENDING |
| FR-TT-003 | Delete time entry      | Must     | PENDING |
| FR-TT-004 | View my timesheet      | Must     | PENDING |
| FR-TT-005 | View task time entries | Should   | PENDING |
| FR-TT-006 | Approval workflow      | Should   | PENDING |
| FR-TT-007 | Timesheet summary      | Should   | PENDING |

## 12. AI Features

| ID        | Requirement                           | Priority | Status  |
| --------- | ------------------------------------- | -------- | ------- |
| FR-AI-001 | Chat about project                    | Must     | DONE    |
| FR-AI-002 | Query tasks                           | Must     | DONE    |
| FR-AI-003 | Query status                          | Must     | PARTIAL |
| FR-AI-004 | Actions with confirmation             | Should   | DONE    |
| FR-AI-005 | Task estimation                       | Must     | DONE    |
| FR-AI-006 | Show reasoning                        | Should   | PARTIAL |
| FR-AI-007 | Bulk estimate                         | Should   | DONE    |
| FR-AI-008 | Suggestions                           | Should   | DONE    |
| FR-AI-009 | Streaming responses                   | Must     | DONE    |
| FR-AI-010 | Resolve pending AI tool approvals     | Should   | DONE    |
| FR-AI-011 | Approve or redirect AI execution plan | Should   | DONE    |
| FR-AI-012 | List AI conversations for a project   | Should   | DONE    |
| FR-AI-013 | Load AI conversation history          | Should   | DONE    |

## 13. Collaboration

| ID        | Requirement                  | Priority | Status |
| --------- | ---------------------------- | -------- | ------ |
| FR-CO-001 | Invite to project            | Must     | DONE   |
| FR-CO-002 | Set member role              | Must     | DONE   |
| FR-CO-003 | Remove member                | Must     | DONE   |
| FR-CO-004 | View members                 | Must     | DONE   |
| FR-CO-005 | Real-time updates            | Must     | DONE   |
| FR-CO-006 | Presence (who is editing)    | Should   | DONE   |
| FR-CO-007 | Activity log                 | Should   | DONE   |
| FR-CO-008 | Comments on tasks            | Should   | DONE   |
| FR-CO-009 | @mentions                    | Should   | DONE   |
| FR-CO-010 | File attachments             | Should   | DONE   |
| FR-CO-011 | Notifications                | Should   | DONE   |
| FR-CO-012 | Manage notification settings | Should   | DONE   |

## 14. Import/Export

| ID        | Requirement                | Priority | Status  |
| --------- | -------------------------- | -------- | ------- |
| FR-IE-001 | Export to CSV              | Must     | PENDING |
| FR-IE-002 | Import from CSV            | Should   | PENDING |
| FR-IE-003 | Export to MS Project XML   | Should   | PENDING |
| FR-IE-004 | Import from MS Project XML | Should   | PENDING |
| FR-IE-005 | Export Gantt as PNG        | Could    | PENDING |

## 15. Kanban Board

| ID        | Requirement                                                                        | Priority | Status  |
| --------- | ---------------------------------------------------------------------------------- | -------- | ------- |
| FR-KB-001 | Display 5-column Kanban board                                                      | Must     | DONE    |
| FR-KB-002 | Group leaf tasks by status                                                         | Must     | DONE    |
| FR-KB-003 | Drag card to change status                                                         | Must     | DONE    |
| FR-KB-004 | Card shows key task summary fields                                                 | Must     | DONE    |
| FR-KB-005 | Search and filter cards                                                            | Should   | DONE    |
| FR-KB-006 | Collapse column to icon strip                                                      | Should   | DONE    |
| FR-KB-007 | Quick-add card from column header                                                  | Should   | DONE    |
| FR-KB-008 | Open task detail panel from card without leaving the board                         | Must     | DONE    |
| FR-KB-009 | Drag to reorder cards within a column                                              | Should   | DONE    |
| FR-KB-010 | WIP limits — set max cards per column with visual warning when exceeded            | Should   | DONE    |
| FR-KB-011 | Swimlanes — group cards by assignee or priority within each column                 | Should   | DONE    |
| FR-KB-012 | Keyboard shortcuts — quick-add card, arrow navigation between cards                | Should   | DONE    |
| FR-KB-013 | Bulk select and move multiple cards across columns                                 | Should   | PENDING |
| FR-KB-014 | Show assignee avatar on card                                                       | Should   | DONE    |
| FR-KB-015 | Show dependency indicator on card — blocked and blocking states                    | Should   | DONE    |
| FR-KB-016 | AI sprint health summary — surface cards at risk based on board state              | Should   | PENDING |
| FR-KB-017 | AI quick-fill — generate card fields from title only                               | Could    | PENDING |
| FR-KB-018 | AI-detected blockers — highlight cards with unresolved dependencies or no activity | Could    | PENDING |

---

## 16. Organization Management

| ID        | Requirement                                         | Priority | Status |
| --------- | --------------------------------------------------- | -------- | ------ |
| FR-OR-001 | List organizations available to current user        | Must     | DONE   |
| FR-OR-002 | Create organization                                 | Must     | DONE   |
| FR-OR-003 | Update organization settings                        | Should   | DONE   |
| FR-OR-004 | Delete organization                                 | Should   | DONE   |
| FR-OR-005 | List organization members                           | Must     | DONE   |
| FR-OR-006 | Invite organization member                          | Must     | DONE   |
| FR-OR-007 | Update organization member role                     | Must     | DONE   |
| FR-OR-008 | Remove organization member                          | Must     | DONE   |
| FR-OR-009 | Resolve current user's organization role/membership | Should   | DONE   |
| FR-OR-010 | Show organization-level dashboard insights          | Should   | DONE   |

## 17. Reporting Workspace

| ID        | Requirement                                     | Priority | Status  |
| --------- | ----------------------------------------------- | -------- | ------- |
| FR-RP-001 | Provide project reports workspace route/page    | Should   | DONE    |
| FR-RP-002 | Render actionable reporting widgets and metrics | Should   | PENDING |

---

## 18. Future Functional Requirements

### 18.1 AI (Future)

| ID        | Requirement                                    | Priority | Status  |
| --------- | ---------------------------------------------- | -------- | ------- |
| FR-AI-020 | AI Project Planner (generate from description) | Should   | PENDING |
| FR-AI-021 | AI Risk Detector                               | Should   | PENDING |
| FR-AI-022 | AI Schedule Optimizer                          | Should   | PENDING |
| FR-AI-023 | AI Report Generator                            | Should   | PENDING |
| FR-AI-024 | AI Dependency Suggester                        | Could    | PENDING |
| FR-AI-025 | Learning from historical data                  | Could    | PENDING |

### 18.2 Enterprise (Future)

| ID        | Requirement                          | Priority | Status  |
| --------- | ------------------------------------ | -------- | ------- |
| FR-EN-001 | Multi-tenant organizations           | Must     | PARTIAL |
| FR-EN-002 | SSO/SAML authentication              | Should   | PENDING |
| FR-EN-003 | Advanced audit logging               | Should   | PENDING |
| FR-EN-004 | Custom roles/permissions             | Should   | PENDING |
| FR-EN-005 | API rate limiting (per organization) | Should   | PENDING |
| FR-EN-006 | Integrations (Jira, Slack, etc.)     | Could    | PENDING |

---

## Document History

| Version | Date       | Author | Changes                                                                                                                                                                                                                                    |
| ------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 8.0     | 2026-03-20 | Codex  | Cleaned to requirements-only content, added explicit DONE/PARTIAL/PENDING Status columns, synced with traceability and targeted code verification, retained FR-AI requirements in this file.                                               |
| 9.0     | 2026-03-20 | Codex  | Coverage hardening pass: added traced requirements for organization management, account settings extras, AI conversation/plan-approval flows, notification settings, and reporting workspace surfaces.                                     |
| 9.1     | 2026-03-20 | Codex  | Consistency pass with phase-2 design docs: adjusted FR-AI-006 from DONE to PARTIAL to match current design/code evidence (reasoning stream path not fully evidenced).                                                                      |
| 10.0    | 2026-03-23 | wwwer  | Kanban section expanded: added FR-KB-008 through FR-KB-018 covering task detail panel, card reordering, WIP limits, swimlanes, keyboard shortcuts, bulk operations, assignee avatar, dependency indicators, and AI-powered board features. |
| 10.1    | 2026-03-23 | Codex  | Marked FR-KB-015 as DONE after implementing blocked/blocking dependency indicators on Kanban cards.                                                                                                                                        |
| 10.2    | 2026-03-23 | Codex  | Marked FR-KB-009 as DONE after shipping in-column Kanban card reorder with persisted backend ordering and optimistic rollback.                                                                                                             |
