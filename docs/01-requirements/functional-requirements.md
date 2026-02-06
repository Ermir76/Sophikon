# Sophikon V1 - Functional Requirements Document

**Version:** 1.0
**Date:** 2026-02-06
**Status:** Aligned with Database Schema v1.0
**Scope:** V1.0 MVP (10-week university project)

---

## Document References

| Document          | Path                                                      | Description                |
| ----------------- | --------------------------------------------------------- | -------------------------- |
| Database Schema   | [database-schema.md](../02-design/database-schema.md)     | 25 tables, full SQL        |
| API Specification | [api-specification.md](../02-design/api-specification.md) | REST + WebSocket endpoints |
| User Stories      | [user-stories.md](./user-stories.md)                      | Acceptance criteria        |
| AI Features       | [ai-features.md](./ai-features.md)                        | AI implementation details  |

---

## 1. Executive Summary

Sophikon V1 is a modern, AI-powered project management web application. This document defines the functional requirements for **V1.0 MVP**.

### Version Roadmap

| Version  | Focus          | Key Features                                           |
| -------- | -------------- | ------------------------------------------------------ |
| **V1.0** | Foundation MVP | Full PM core, resources, calendars, baselines, AI chat |
| **V2.2** | Intelligence   | AI project planner, risk detection, schedule optimizer |
| **V3.0** | Enterprise     | Multi-tenant, SSO, organizations, integrations         |

---

## 2. Core Entities & Data Models

> **Source of Truth:** [database-schema.md](../02-design/database-schema.md)

### 2.1 Entity Overview (V1.0 - 25 Tables)

```
Auth & Users (4)          Project Core (3)         Scheduling (2)
├── user                  ├── project              ├── calendar
├── role                  ├── project_member       └── calendar_exception
├── refresh_token         └── project_invitation
└── password_reset

Work Items (2)            Dependencies (1)         Resources (3)
├── task                  └── dependency           ├── resource
└── task_baseline                                  ├── resource_rate
                                                   └── resource_availability

Assignments (2)           Time Tracking (1)        Collaboration (3)
├── assignment            └── time_entry           ├── comment
└── assignment_baseline                            ├── attachment
                                                   └── notification

AI (3)                    Audit (1)
├── ai_conversation       └── activity_log
├── ai_message
└── ai_usage
```

---

### 2.2 User & Authentication

#### USER

| Field          | Type      | Description        | Notes                  |
| -------------- | --------- | ------------------ | ---------------------- |
| id             | UUID      | Primary key        |                        |
| email          | string    | Unique email       | Login identifier       |
| password_hash  | string    | bcrypt hash        | NULL for OAuth         |
| full_name      | string    | Display name       |                        |
| avatar_url     | string    | Profile picture    |                        |
| system_role_id | FK        | Reference to role  | admin or user          |
| oauth_provider | string    | google, github     |                        |
| oauth_id       | string    | Provider's user ID |                        |
| is_active      | boolean   | Account enabled    | Soft disable           |
| email_verified | boolean   | Email confirmed    |                        |
| preferences    | JSONB     | User settings      | Timezone, locale, etc. |
| timezone       | string    | User timezone      | Default: UTC           |
| locale         | string    | Language/region    | Default: en-US         |
| last_login_at  | timestamp | Last login         |                        |
| created_at     | timestamp | Registration       |                        |
| updated_at     | timestamp | Last update        |                        |

#### ROLE (RBAC-Ready)

| Field       | Type      | Description       | Notes                        |
| ----------- | --------- | ----------------- | ---------------------------- |
| id          | UUID      | Primary key       | Fixed UUIDs for system roles |
| name        | string    | Role name         | Unique                       |
| description | text      | Role description  |                              |
| permissions | JSONB     | Permission array  | ["project:*", "task:read"]   |
| is_system   | boolean   | System role       | Cannot modify/delete         |
| scope       | string    | system or project |                              |
| created_at  | timestamp |                   |                              |
| updated_at  | timestamp |                   |                              |

**System Roles (Seeded):**

| Role    | Scope   | Permissions                                                    |
| ------- | ------- | -------------------------------------------------------------- |
| admin   | system  | system:\*                                                      |
| user    | system  | project:create, project:read_own                               |
| owner   | project | project:_, task:_, resource:_, member:_                        |
| manager | project | project:read, project:update, task:_, resource:_, member:read  |
| member  | project | project:read, task:read, task:update_assigned, time:create_own |
| viewer  | project | project:read, task:read, resource:read                         |

---

### 2.3 Project

#### PROJECT

| Field               | Type      | Description         | Notes                |
| ------------------- | --------- | ------------------- | -------------------- |
| id                  | UUID      | Primary key         |                      |
| owner_id            | FK        | Project owner       | References user      |
| name                | string    | Project name        | Max 255              |
| description         | text      | Description         |                      |
| start_date          | date      | Project start       | Required             |
| finish_date         | date      | Calculated finish   | From tasks           |
| status_date         | date      | Progress as-of date | For earned value     |
| schedule_from       | enum      | START or FINISH     | Scheduling direction |
| default_calendar_id | FK        | Default calendar    | References calendar  |
| status              | enum      | Project status      | See below            |
| budget              | decimal   | Project budget      | Optional             |
| currency            | string    | Currency code       | Default: USD         |
| settings            | JSONB     | Project settings    | See below            |
| is_deleted          | boolean   | Soft delete         |                      |
| deleted_at          | timestamp | When deleted        |                      |
| created_at          | timestamp |                     |                      |
| updated_at          | timestamp |                     |                      |

**Status Values:** PLANNING, ACTIVE, ON_HOLD, COMPLETED, CANCELLED

**Settings JSONB:**

```json
{
  "hours_per_day": 8,
  "hours_per_week": 40,
  "days_per_month": 20,
  "first_day_of_week": 1,
  "default_task_type": "FIXED_UNITS",
  "new_tasks_effort_driven": true,
  "auto_calculate": true
}
```

#### PROJECT_MEMBER

| Field       | Type      | Description     | Notes                          |
| ----------- | --------- | --------------- | ------------------------------ |
| id          | UUID      | Primary key     |                                |
| project_id  | FK        | Project         |                                |
| user_id     | FK        | User            |                                |
| role_id     | FK        | Project role    | References role (RBAC)         |
| resource_id | FK        | Linked resource | Optional - if user is resource |
| joined_at   | timestamp | When joined     |                                |
| updated_at  | timestamp |                 |                                |

**Unique:** (project_id, user_id)

#### PROJECT_INVITATION

| Field         | Type      | Description      | Notes    |
| ------------- | --------- | ---------------- | -------- |
| id            | UUID      | Primary key      |          |
| project_id    | FK        | Project          |          |
| invited_by_id | FK        | Inviter          |          |
| email         | string    | Invitee email    |          |
| role_id       | FK        | Role to assign   |          |
| token_hash    | string    | Email link token | Hashed   |
| message       | text      | Personal message | Optional |
| expires_at    | timestamp | Expiration       | 7 days   |
| accepted_at   | timestamp | When accepted    |          |
| is_revoked    | boolean   | Cancelled        |          |
| created_at    | timestamp |                  |          |

---

### 2.4 Scheduling

#### CALENDAR

| Field            | Type      | Description        | Notes         |
| ---------------- | --------- | ------------------ | ------------- |
| id               | UUID      | Primary key        |               |
| project_id       | FK        | Project            | NULL = global |
| name             | string    | Calendar name      |               |
| base_calendar_id | FK        | Parent calendar    | Inheritance   |
| is_base          | boolean   | Template calendar  |               |
| work_week        | JSONB     | 7-day work pattern | See below     |
| created_at       | timestamp |                    |               |
| updated_at       | timestamp |                    |               |

**Work Week JSONB (Sunday=0):**

```json
[
  null,
  {
    "start": "09:00",
    "end": "17:00",
    "breaks": [{ "start": "12:00", "end": "13:00" }]
  },
  {
    "start": "09:00",
    "end": "17:00",
    "breaks": [{ "start": "12:00", "end": "13:00" }]
  },
  {
    "start": "09:00",
    "end": "17:00",
    "breaks": [{ "start": "12:00", "end": "13:00" }]
  },
  {
    "start": "09:00",
    "end": "17:00",
    "breaks": [{ "start": "12:00", "end": "13:00" }]
  },
  {
    "start": "09:00",
    "end": "17:00",
    "breaks": [{ "start": "12:00", "end": "13:00" }]
  },
  null
]
```

#### CALENDAR_EXCEPTION

| Field       | Type      | Description       | Notes              |
| ----------- | --------- | ----------------- | ------------------ |
| id          | UUID      | Primary key       |                    |
| calendar_id | FK        | Calendar          |                    |
| name        | string    | Exception name    | "Christmas"        |
| start_date  | date      | Start             |                    |
| end_date    | date      | End               |                    |
| is_working  | boolean   | Working exception | FALSE = holiday    |
| work_times  | JSONB     | Custom hours      | If is_working=TRUE |
| recurrence  | JSONB     | Repeat pattern    | Optional           |
| created_at  | timestamp |                   |                    |

---

### 2.5 Task

#### TASK

| Field                 | Type      | Description                  | Notes                                        |
| --------------------- | --------- | ---------------------------- | -------------------------------------------- |
| id                    | UUID      | Primary key                  |                                              |
| project_id            | FK        | Project                      |                                              |
| parent_task_id        | FK        | Parent task                  | WBS hierarchy                                |
| wbs_code              | string    | WBS code                     | "1.2.3"                                      |
| outline_level         | integer   | Depth                        | 1-based                                      |
| order_index           | integer   | Sort order                   | Within siblings                              |
| name                  | string    | Task name                    | Max 500                                      |
| notes                 | text      | Task notes                   |                                              |
| is_milestone          | boolean   | Milestone                    | Zero duration                                |
| is_summary            | boolean   | Summary task                 | Has children                                 |
| is_critical           | boolean   | Critical path                | Calculated                                   |
| calendar_id           | FK        | Task calendar                | Optional override                            |
| **Duration & Work**   |
| duration              | integer   | Duration (minutes)           | Default 480 (8h)                             |
| work                  | integer   | Total work (minutes)         | Effort                                       |
| actual_duration       | integer   | Actual duration              |                                              |
| actual_work           | integer   | Actual work                  |                                              |
| remaining_duration    | integer   | Remaining                    |                                              |
| remaining_work        | integer   | Remaining work               |                                              |
| **Dates**             |
| start_date            | date      | Scheduled start              |                                              |
| finish_date           | date      | Scheduled finish             |                                              |
| actual_start          | date      | Actual start                 |                                              |
| actual_finish         | date      | Actual finish                |                                              |
| **Progress**          |
| percent_complete      | decimal   | Progress %                   | 0-100                                        |
| percent_work_complete | decimal   | Work progress %              | 0-100                                        |
| **Scheduling**        |
| task_type             | enum      | Scheduling type              | FIXED_UNITS, FIXED_DURATION, FIXED_WORK      |
| effort_driven         | boolean   | Effort driven                |                                              |
| constraint_type       | enum      | Constraint                   | ASAP, ALAP, MSO, MFO, SNET, SNLT, FNET, FNLT |
| constraint_date       | date      | Constraint date              |                                              |
| deadline              | date      | Soft deadline                | Warning indicator                            |
| **Slack**             |
| total_slack           | integer   | Total slack (min)            | Calculated                                   |
| free_slack            | integer   | Free slack (min)             | Calculated                                   |
| **Priority**          |
| priority              | integer   | Priority                     | 0-1000, default 500                          |
| **Cost**              |
| fixed_cost            | decimal   | Fixed cost                   |                                              |
| fixed_cost_accrual    | enum      | Accrual                      | START, END, PRORATED                         |
| total_cost            | decimal   | Total cost                   | Calculated                                   |
| actual_cost           | decimal   | Actual cost                  |                                              |
| remaining_cost        | decimal   | Remaining cost               |                                              |
| **Earned Value**      |
| bcws                  | decimal   | Budgeted Cost Work Scheduled | Planned Value                                |
| bcwp                  | decimal   | Budgeted Cost Work Performed | Earned Value                                 |
| acwp                  | decimal   | Actual Cost Work Performed   | Actual Cost                                  |
| **Meta**              |
| external_id           | string    | Import ID                    | For XML import                               |
| is_deleted            | boolean   | Soft delete                  |                                              |
| deleted_at            | timestamp |                              |                                              |
| created_at            | timestamp |                              |                                              |
| updated_at            | timestamp |                              |                                              |

#### TASK_BASELINE

| Field           | Type      | Description       | Notes |
| --------------- | --------- | ----------------- | ----- |
| id              | UUID      | Primary key       |       |
| task_id         | FK        | Task              |       |
| baseline_number | integer   | Baseline #        | 0-10  |
| duration        | integer   | Snapshot duration |       |
| work            | integer   | Snapshot work     |       |
| start_date      | date      | Snapshot start    |       |
| finish_date     | date      | Snapshot finish   |       |
| cost            | decimal   | Snapshot cost     |       |
| created_at      | timestamp |                   |       |

**Unique:** (task_id, baseline_number)

---

### 2.6 Dependency

#### DEPENDENCY

| Field          | Type      | Description      | Notes               |
| -------------- | --------- | ---------------- | ------------------- |
| id             | UUID      | Primary key      |                     |
| project_id     | FK        | Project          |                     |
| predecessor_id | FK        | Predecessor task |                     |
| successor_id   | FK        | Successor task   |                     |
| type           | enum      | Link type        | FS, FF, SS, SF      |
| lag            | integer   | Lag (minutes)    | Can be negative     |
| lag_format     | enum      | Lag format       | DURATION or PERCENT |
| is_disabled    | boolean   | Disabled         | Keep but ignore     |
| created_at     | timestamp |                  |                     |

**Unique:** (predecessor_id, successor_id)
**Check:** predecessor_id != successor_id

---

### 2.7 Resource

#### RESOURCE

| Field          | Type      | Description      | Notes                |
| -------------- | --------- | ---------------- | -------------------- |
| id             | UUID      | Primary key      |                      |
| project_id     | FK        | Project          |                      |
| name           | string    | Resource name    |                      |
| initials       | string    | Initials         | Max 10               |
| email          | string    | Email            |                      |
| type           | enum      | Resource type    | WORK, MATERIAL, COST |
| material_label | string    | Unit label       | "tons", "gallons"    |
| max_units      | decimal   | Max allocation   | 1.0 = 100%           |
| calendar_id    | FK        | Calendar         |                      |
| group_name     | string    | Group            |         |
| code           | string    | Resource code    |                      |
| is_generic     | boolean   | Generic resource | Placeholder          |
| is_active      | boolean   | Active           |                      |
| standard_rate  | decimal   | Hourly rate      |                      |
| overtime_rate  | decimal   | OT rate          |                      |
| cost_per_use   | decimal   | Per-use cost     |                      |
| accrue_at      | enum      | Accrual          | START, END, PRORATED |
| user_id        | FK        | Linked user      | Optional             |
| external_id    | string    | Import ID        |                      |
| created_at     | timestamp |                  |                      |
| updated_at     | timestamp |                  |                      |

#### RESOURCE_RATE

| Field          | Type      | Description    | Notes           |
| -------------- | --------- | -------------- | --------------- |
| id             | UUID      | Primary key    |                 |
| resource_id    | FK        | Resource       |                 |
| rate_table     | char      | Table A-E      | Like MS Project |
| effective_date | date      | Effective from |                 |
| standard_rate  | decimal   | Rate           |                 |
| overtime_rate  | decimal   | OT rate        |                 |
| cost_per_use   | decimal   | Per-use        |                 |
| created_at     | timestamp |                |                 |

**Unique:** (resource_id, rate_table, effective_date)

#### RESOURCE_AVAILABILITY

| Field       | Type      | Description  | Notes             |
| ----------- | --------- | ------------ | ----------------- |
| id          | UUID      | Primary key  |                   |
| resource_id | FK        | Resource     |                   |
| start_date  | date      | Period start |                   |
| end_date    | date      | Period end   | NULL = indefinite |
| units       | decimal   | Availability | 1.0 = 100%        |
| created_at  | timestamp |              |                   |

---

### 2.8 Assignment

#### ASSIGNMENT

| Field                 | Type      | Description    | Notes                   |
| --------------------- | --------- | -------------- | ----------------------- |
| id                    | UUID      | Primary key    |                         |
| task_id               | FK        | Task           |                         |
| resource_id           | FK        | Resource       |                         |
| units                 | decimal   | Allocation     | 1.0 = 100%              |
| work                  | integer   | Work (minutes) |                         |
| actual_work           | integer   | Actual work    |                         |
| remaining_work        | integer   | Remaining      |                         |
| start_date            | date      | Start          | May differ from task    |
| finish_date           | date      | Finish         |                         |
| actual_start          | date      | Actual start   |                         |
| actual_finish         | date      | Actual finish  |                         |
| work_contour          | enum      | Distribution   | FLAT, BACK_LOADED, etc. |
| contour_data          | JSONB     | Custom contour | If CONTOURED            |
| cost                  | decimal   | Cost           | Calculated              |
| actual_cost           | decimal   | Actual         |                         |
| remaining_cost        | decimal   | Remaining      |                         |
| rate_table            | char      | Rate table     | A-E                     |
| percent_work_complete | decimal   | Progress       | 0-100                   |
| is_confirmed          | boolean   | Confirmed      | Timesheet approval      |
| created_at            | timestamp |                |                         |
| updated_at            | timestamp |                |                         |

**Unique:** (task_id, resource_id)

**Work Contours:** FLAT, BACK_LOADED, FRONT_LOADED, DOUBLE_PEAK, EARLY_PEAK, LATE_PEAK, BELL, TURTLE, CONTOURED

#### ASSIGNMENT_BASELINE

| Field           | Type      | Description     | Notes |
| --------------- | --------- | --------------- | ----- |
| id              | UUID      | Primary key     |       |
| assignment_id   | FK        | Assignment      |       |
| baseline_number | integer   | Baseline #      |  |
| work            | integer   | Snapshot work   |       |
| start_date      | date      | Snapshot start  |       |
| finish_date     | date      | Snapshot finish |       |
| cost            | decimal   | Snapshot cost   |       |
| created_at      | timestamp |                 |       |

---

### 2.9 Time Tracking

#### TIME_ENTRY

| Field            | Type      | Description    | Notes                                |
| ---------------- | --------- | -------------- | ------------------------------------ |
| id               | UUID      | Primary key    |                                      |
| user_id          | FK        | Who logged     |                                      |
| task_id          | FK        | Task           |                                      |
| assignment_id    | FK        | Assignment     | Optional                             |
| work_date        | date      | Date worked    |                                      |
| regular_work     | integer   | Regular (min)  |                                      |
| overtime_work    | integer   | Overtime (min) |                                      |
| notes            | text      | Description    |                                      |
| is_billable      | boolean   | Billable       |                                      |
| billing_status   | enum      | Billing        | UNBILLED, BILLED, NON_BILLABLE       |
| status           | enum      | Approval       | DRAFT, SUBMITTED, APPROVED, REJECTED |
| approved_by_id   | FK        | Approver       |                                      |
| approved_at      | timestamp | When approved  |                                      |
| rejection_reason | text      | If rejected    |                                      |
| created_at       | timestamp |                |                                      |
| updated_at       | timestamp |                |                                      |

---

### 2.10 Collaboration

#### COMMENT

| Field             | Type      | Description     | Notes             |
| ----------------- | --------- | --------------- | ----------------- |
| id                | UUID      | Primary key     |                   |
| entity_type       | string    | Entity type     | 'task', 'project' |
| entity_id         | UUID      | Entity ID       | Polymorphic       |
| author_id         | FK        | Author          |                   |
| content           | text      | Comment text    |                   |
| parent_comment_id | FK        | Reply to        | Threading         |
| mentions          | UUID[]    | Mentioned users | Array             |
| is_edited         | boolean   | Was edited      |                   |
| edited_at         | timestamp | Edit time       |                   |
| is_deleted        | boolean   | Soft delete     |                   |
| deleted_at        | timestamp |                 |                   |
| created_at        | timestamp |                 |                   |

#### ATTACHMENT

| Field            | Type      | Description   | Notes                        |
| ---------------- | --------- | ------------- | ---------------------------- |
| id               | UUID      | Primary key   |                              |
| entity_type      | string    | Entity type   | 'task', 'project', 'comment' |
| entity_id        | UUID      | Entity ID     | Polymorphic                  |
| uploaded_by_id   | FK        | Uploader      |                              |
| file_name        | string    | Original name |                              |
| file_size        | bigint    | Size (bytes)  |                              |
| mime_type        | string    | MIME type     |                              |
| storage_path     | string    | Storage path  | S3 or local                  |
| storage_provider | string    | Provider      | 'local', 's3'                |
| description      | text      | Description   |                              |
| is_deleted       | boolean   | Soft delete   |                              |
| deleted_at       | timestamp |               |                              |
| created_at       | timestamp |               |                              |

#### NOTIFICATION

| Field         | Type      | Description       | Notes     |
| ------------- | --------- | ----------------- | --------- |
| id            | UUID      | Primary key       |           |
| user_id       | FK        | Recipient         |           |
| type          | string    | Notification type | See below |
| title         | string    | Title             |           |
| message       | text      | Message           |           |
| entity_type   | string    | Related entity    |           |
| entity_id     | UUID      | Entity ID         |           |
| actor_id      | FK        | Who triggered     |           |
| is_read       | boolean   | Read status       |           |
| read_at       | timestamp | When read         |           |
| email_sent    | boolean   | Email sent        |           |
| email_sent_at | timestamp | When sent         |           |
| created_at    | timestamp |                   |           |

**Notification Types:** task_assigned, task_updated, mentioned, comment_added, deadline_approaching, invitation_received

---

### 2.11 AI

#### AI_CONVERSATION

| Field            | Type      | Description        | Notes            |
| ---------------- | --------- | ------------------ | ---------------- |
| id               | UUID      | Primary key        |                  |
| project_id       | FK        | Project context    |                  |
| user_id          | FK        | User               |                  |
| title            | string    | Conversation title | Auto or user-set |
| context_snapshot | JSONB     | Cached context     | Optional         |
| created_at       | timestamp |                    |                  |
| updated_at       | timestamp |                    |                  |

#### AI_MESSAGE

| Field           | Type      | Description     | Notes                   |
| --------------- | --------- | --------------- | ----------------------- |
| id              | UUID      | Primary key     |                         |
| conversation_id | FK        | Conversation    |                         |
| role            | enum      | Message role    | user, assistant, system |
| content         | text      | Message content |                         |
| model           | string    | Model used      | For assistant           |
| tokens_in       | integer   | Input tokens    |                         |
| tokens_out      | integer   | Output tokens   |                         |
| latency_ms      | integer   | Response time   |                         |
| finish_reason   | string    | Stop reason     |                         |
| tool_calls      | JSONB     | Tool calls      |                         |
| tool_results    | JSONB     | Tool results    |                         |
| created_at      | timestamp |                 |                         |

#### AI_USAGE

| Field          | Type      | Description     | Notes                        |
| -------------- | --------- | --------------- | ---------------------------- |
| id             | UUID      | Primary key     |                              |
| user_id        | FK        | User            |                              |
| feature        | string    | Feature used    | chat, estimation, suggestion |
| model          | string    | Model           |                              |
| tokens_in      | integer   | Input tokens    |                              |
| tokens_out     | integer   | Output tokens   |                              |
| estimated_cost | decimal   | Cost (USD)      |                              |
| usage_date     | date      | For aggregation |                              |
| created_at     | timestamp |                 |                              |

---

### 2.12 Audit

#### ACTIVITY_LOG

| Field       | Type      | Description  | Notes                               |
| ----------- | --------- | ------------ | ----------------------------------- |
| id          | UUID      | Primary key  |                                     |
| project_id  | FK        | Project      |                                     |
| user_id     | FK        | Actor        |                                     |
| action      | string    | Action       | created, updated, deleted, restored |
| entity_type | string    | Entity type  |                                     |
| entity_id   | UUID      | Entity ID    |                                     |
| entity_name | string    | For display  | After delete                        |
| changes     | JSONB     | What changed |                                     |
| ip_address  | inet      | Client IP    |                                     |
| user_agent  | string    | Browser      |                                     |
| created_at  | timestamp |              |                                     |

---

## 3. Functional Requirements - V1.0 MVP

### 3.1 Authentication & User Management

| ID        | Requirement                  | Priority | API Endpoint              |
| --------- | ---------------------------- | -------- | ------------------------- |
| FR-AU-001 | Register with email/password | Must     | POST /auth/register       |
| FR-AU-002 | Login with email/password    | Must     | POST /auth/login          |
| FR-AU-003 | Login with Google OAuth      | Must     | GET /auth/oauth/google    | - check other auth providers
| FR-AU-004 | Logout (revoke token)        | Must     | POST /auth/logout         |
| FR-AU-005 | Password reset via email     | Should   | POST /auth/password-reset |
| FR-AU-006 | Update profile               | Should   | PATCH /users/me           |
| FR-AU-007 | JWT with refresh tokens      | Must     | POST /auth/refresh        |
| FR-AU-008 | Session management           | Should   | GET /users/me/sessions    |

### 3.2 Project Management

| ID        | Requirement           | Priority | API Endpoint                 |
| --------- | --------------------- | -------- | ---------------------------- |
| FR-PM-001 | Create project        | Must     | POST /projects               |
| FR-PM-002 | Edit project          | Must     | PATCH /projects/:id          |
| FR-PM-003 | Delete project (soft) | Must     | DELETE /projects/:id         |
| FR-PM-004 | List user's projects  | Must     | GET /projects                |
| FR-PM-005 | Project dashboard     | Must     | GET /projects/:id/dashboard  |
| FR-PM-006 | Set project status    | Should   | PATCH /projects/:id          |
| FR-PM-007 | Duplicate project     | Could    | POST /projects/:id/duplicate |
| FR-PM-008 | Set default calendar  | Should   | PATCH /projects/:id          |

### 3.3 Task Management

| ID        | Requirement                       | Priority | API Endpoint                       |
| --------- | --------------------------------- | -------- | ---------------------------------- |
| FR-TM-001 | Create task                       | Must     | POST /projects/:id/tasks           |
| FR-TM-002 | Edit task                         | Must     | PATCH /projects/:id/tasks/:taskId  |
| FR-TM-003 | Delete task (soft)                | Must     | DELETE /projects/:id/tasks/:taskId |
| FR-TM-004 | Create hierarchy (indent/outdent) | Must     | POST /tasks/:taskId/indent         |
| FR-TM-005 | Auto-generate WBS codes           | Must     | Automatic                          |
| FR-TM-006 | Reorder tasks (drag/drop)         | Must     | PATCH /projects/:id/tasks/reorder  |
| FR-TM-007 | Set duration                      | Must     | PATCH /tasks/:taskId               |
| FR-TM-008 | Set as milestone                  | Must     | PATCH /tasks/:taskId               |
| FR-TM-009 | Set constraint type               | Should   | PATCH /tasks/:taskId               |
| FR-TM-010 | Set task type (scheduling)        | Should   | PATCH /tasks/:taskId               |
| FR-TM-011 | Update progress                   | Must     | PATCH /tasks/:taskId               |
| FR-TM-012 | Add notes                         | Should   | PATCH /tasks/:taskId               |
| FR-TM-013 | Summary tasks auto-calculate      | Must     | Automatic                          |
| FR-TM-014 | Bulk operations                   | Should   | POST /tasks/bulk                   |
| FR-TM-015 | Set work (effort)                 | Should   | PATCH /tasks/:taskId               |
| FR-TM-016 | Track actual dates                | Should   | PATCH /tasks/:taskId               |

### 3.4 Dependency Management

| ID        | Requirement          | Priority | API Endpoint                    |
| --------- | -------------------- | -------- | ------------------------------- |
| FR-DM-001 | Create FS dependency | Must     | POST /projects/:id/dependencies |
| FR-DM-002 | Create FF dependency | Should   | POST /projects/:id/dependencies |
| FR-DM-003 | Create SS dependency | Should   | POST /projects/:id/dependencies |
| FR-DM-004 | Create SF dependency | Could    | POST /projects/:id/dependencies |
| FR-DM-005 | Set lag time         | Should   | POST /projects/:id/dependencies |
| FR-DM-006 | Delete dependency    | Must     | DELETE /dependencies/:depId     |
| FR-DM-007 | Prevent circular     | Must     | Validation                      |
| FR-DM-008 | Disable dependency   | Should   | PATCH /dependencies/:depId      |

### 3.5 Scheduling Engine

| ID        | Requirement                | Priority | API Endpoint                             |
| --------- | -------------------------- | -------- | ---------------------------------------- |
| FR-SE-001 | Calculate successor dates  | Must     | POST /projects/:id/schedule/calculate    |
| FR-SE-002 | Calculate critical path    | Must     | GET /projects/:id/schedule/critical-path |
| FR-SE-003 | Calculate slack/float      | Should   | Automatic                                |
| FR-SE-004 | Respect ASAP constraint    | Must     | Automatic                                |
| FR-SE-005 | Respect ALAP constraint    | Should   | Automatic                                |
| FR-SE-006 | Respect date constraints   | Should   | Automatic                                |
| FR-SE-007 | Auto-recalculate on change | Must     | Automatic                                |
| FR-SE-008 | Forward scheduling         | Must     | Automatic                                |

### 3.6 Gantt Chart

| ID        | Requirement               | Priority | API Endpoint |
| --------- | ------------------------- | -------- | ------------ |
| FR-GC-001 | Display task bars         | Must     | Frontend     |
| FR-GC-002 | Bar position = dates      | Must     | Frontend     |
| FR-GC-003 | Bar length = duration     | Must     | Frontend     |
| FR-GC-004 | Show hierarchy            | Must     | Frontend     |
| FR-GC-005 | Show dependencies         | Must     | Frontend     |
| FR-GC-006 | Show progress             | Must     | Frontend     |
| FR-GC-007 | Show milestones           | Must     | Frontend     |
| FR-GC-008 | Show summary tasks        | Must     | Frontend     |
| FR-GC-009 | Timeline header           | Must     | Frontend     |
| FR-GC-010 | Zoom levels               | Must     | Frontend     |
| FR-GC-011 | Horizontal scroll         | Must     | Frontend     |
| FR-GC-012 | Vertical scroll           | Must     | Frontend     |
| FR-GC-013 | Today line                | Must     | Frontend     |
| FR-GC-014 | Critical path highlight   | Should   | Frontend     |
| FR-GC-015 | Click to select           | Must     | Frontend     |
| FR-GC-016 | Double-click for details  | Must     | Frontend     |
| FR-GC-017 | Drag to change dates      | Could    | Frontend     |
| FR-GC-018 | Drag edges for duration   | Could    | Frontend     |
| FR-GC-019 | Drag to create dependency | Could    | Frontend     |
| FR-GC-020 | Context menu              | Should   | Frontend     |

### 3.7 Calendar Management

| ID        | Requirement                 | Priority | API Endpoint                   |
| --------- | --------------------------- | -------- | ------------------------------ |
| FR-CA-001 | Create calendar             | Must     | POST /projects/:id/calendars   |
| FR-CA-002 | Edit work week              | Must     | PATCH /calendars/:id           |
| FR-CA-003 | Add exception (holiday)     | Must     | POST /calendars/:id/exceptions |
| FR-CA-004 | Delete exception            | Must     | DELETE /exceptions/:id         |
| FR-CA-005 | Calendar inheritance        | Should   | PATCH /calendars/:id           |
| FR-CA-006 | Assign calendar to task     | Should   | PATCH /tasks/:taskId           |
| FR-CA-007 | Assign calendar to resource | Should   | PATCH /resources/:id           |

### 3.8 Resource Management

| ID        | Requirement              | Priority | API Endpoint                     |
| --------- | ------------------------ | -------- | -------------------------------- |
| FR-RM-001 | Create work resource     | Must     | POST /projects/:id/resources     |
| FR-RM-002 | Create material resource | Should   | POST /projects/:id/resources     |
| FR-RM-003 | Create cost resource     | Could    | POST /projects/:id/resources     |
| FR-RM-004 | Edit resource            | Must     | PATCH /resources/:id             |
| FR-RM-005 | Delete resource          | Must     | DELETE /resources/:id            |
| FR-RM-006 | Set rates                | Must     | POST /resources/:id/rates        |
| FR-RM-007 | Set availability         | Should   | POST /resources/:id/availability |
| FR-RM-008 | Link to user             | Should   | PATCH /resources/:id             |
| FR-RM-009 | Resource groups          | Should   | PATCH /resources/:id             |

### 3.9 Assignment Management

| ID        | Requirement             | Priority | API Endpoint                              |
| --------- | ----------------------- | -------- | ----------------------------------------- |
| FR-AS-001 | Assign resource to task | Must     | POST /tasks/:taskId/assignments           |
| FR-AS-002 | Set allocation units    | Must     | PATCH /assignments/:id                    |
| FR-AS-003 | Remove assignment       | Must     | DELETE /assignments/:id                   |
| FR-AS-004 | Set work contour        | Should   | PATCH /assignments/:id                    |
| FR-AS-005 | Track actual work       | Should   | PATCH /assignments/:id                    |
| FR-AS-006 | View resource workload  | Must     | GET /resources/:id/workload               |
| FR-AS-007 | Over-allocation warning | Should   | GET /projects/:id/resources/overallocated |

### 3.10 Baseline Management

| ID        | Requirement                 | Priority | API Endpoint                             |
| --------- | --------------------------- | -------- | ---------------------------------------- |
| FR-BL-001 | Save baseline               | Must     | POST /projects/:id/baselines             |
| FR-BL-002 | Name baseline               | Must     | POST /projects/:id/baselines             |
| FR-BL-003 | Multiple baselines (0-10)   | Should   | POST /projects/:id/baselines             |
| FR-BL-004 | View baseline data          | Must     | GET /projects/:id/baselines/:num         |
| FR-BL-005 | Compare current vs baseline | Should   | GET /projects/:id/baselines/:num/compare |
| FR-BL-006 | Delete baseline             | Should   | DELETE /baselines/:id                    |

### 3.11 Time Tracking

| ID        | Requirement            | Priority | API Endpoint                        |
| --------- | ---------------------- | -------- | ----------------------------------- |
| FR-TT-001 | Log time entry         | Must     | POST /time-entries                  |
| FR-TT-002 | Edit time entry        | Must     | PATCH /time-entries/:id             |
| FR-TT-003 | Delete time entry      | Must     | DELETE /time-entries/:id            |
| FR-TT-004 | View my timesheet      | Must     | GET /users/me/time-entries          |
| FR-TT-005 | View task time entries | Should   | GET /tasks/:id/time-entries         |
| FR-TT-006 | Approval workflow      | Should   | PATCH /time-entries/:id/approve     |
| FR-TT-007 | Timesheet summary      | Should   | GET /projects/:id/timesheet-summary |

### 3.12 AI Features

| ID        | Requirement               | Priority | API Endpoint                     |
| --------- | ------------------------- | -------- | -------------------------------- |
| FR-AI-001 | Chat about project        | Must     | POST /projects/:id/ai/chat       |
| FR-AI-002 | Query tasks               | Must     | POST /projects/:id/ai/chat       |
| FR-AI-003 | Query status              | Must     | POST /projects/:id/ai/chat       |
| FR-AI-004 | Actions with confirmation | Should   | POST /projects/:id/ai/chat       |
| FR-AI-005 | Task estimation           | Must     | POST /projects/:id/ai/estimate   |
| FR-AI-006 | Show reasoning            | Should   | POST /projects/:id/ai/estimate   |
| FR-AI-007 | Bulk estimate             | Should   | POST /projects/:id/ai/estimate   |
| FR-AI-008 | Suggestions               | Should   | GET /projects/:id/ai/suggestions |
| FR-AI-009 | Streaming responses       | Must     | POST /projects/:id/ai/chat       |

### 3.13 Collaboration

| ID        | Requirement              | Priority | API Endpoint                      |
| --------- | ------------------------ | -------- | --------------------------------- |
| FR-CO-001 | Invite to project        | Must     | POST /projects/:id/members/invite |
| FR-CO-002 | Set member role          | Must     | PATCH /members/:id                |
| FR-CO-003 | Remove member            | Must     | DELETE /members/:id               |
| FR-CO-004 | View members             | Must     | GET /projects/:id/members         |
| FR-CO-005 | Real-time updates        | Must     | WebSocket                         |
| FR-CO-006 | Presence (who's editing) | Should   | WebSocket                         |
| FR-CO-007 | Activity log             | Should   | GET /projects/:id/activity        |
| FR-CO-008 | Comments on tasks        | Should   | POST /tasks/:id/comments          |
| FR-CO-009 | @mentions                | Should   | POST /tasks/:id/comments          |
| FR-CO-010 | File attachments         | Should   | POST /tasks/:id/attachments       |
| FR-CO-011 | Notifications            | Should   | GET /notifications                |

### 3.14 Import/Export

| ID        | Requirement                | Priority | API Endpoint                 |
| --------- | -------------------------- | -------- | ---------------------------- |
| FR-IE-001 | Export to CSV              | Must     | GET /projects/:id/export/csv |
| FR-IE-002 | Import from CSV            | Should   | POST /projects/:id/import    |
| FR-IE-003 | Export to MS Project XML   | Should   | GET /projects/:id/export/xml |
| FR-IE-004 | Import from MS Project XML | Should   | POST /projects/:id/import    |
| FR-IE-005 | Export Gantt as PNG        | Could    | GET /projects/:id/export/png |

---

## 4. Functional Requirements - Future Versions

### 4.1 V1.2 - Advanced AI

| ID        | Requirement                                    |
| --------- | ---------------------------------------------- |
| FR-AI-020 | AI Project Planner (generate from description) |
| FR-AI-021 | AI Risk Detector                               |
| FR-AI-022 | AI Schedule Optimizer                          |
| FR-AI-023 | AI Report Generator                            |
| FR-AI-024 | AI Dependency Suggester                        |
| FR-AI-025 | Learning from historical data                  |

### 4.2 V2.0 - Enterprise

| ID        | Requirement                      |
| --------- | -------------------------------- |
| FR-EN-001 | Multi-tenant (organizations)     |
| FR-EN-002 | SSO/SAML authentication          |
| FR-EN-003 | Advanced audit logging           |
| FR-EN-004 | Custom roles/permissions         |
| FR-EN-005 | API rate limiting (per org)      |
| FR-EN-006 | Integrations (Jira, Slack, etc.) |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement                      | Target      |
| -------------------------------- | ----------- |
| Page load time                   | < 2 seconds |
| Gantt render (500 tasks)         | < 1 second  |
| Gantt render (2000 tasks)        | < 3 seconds |
| API response (CRUD)              | < 200ms     |
| Schedule calculation (500 tasks) | < 500ms     |
| AI chat response start           | < 2 seconds |
| WebSocket latency                | < 100ms     |

### 5.2 Scalability (V1.0 Targets)

| Metric                | Target |
| --------------------- | ------ |
| Concurrent users      | 50+    |
| Tasks per project     | 2000+  |
| Projects per user     | 100+   |
| Resources per project | 100+   |

### 5.3 Security

| Requirement                    | Priority |
| ------------------------------ | -------- |
| HTTPS only                     | Must     |
| JWT authentication             | Must     |
| Password hashing (bcrypt)      | Must     |
| SQL injection prevention (ORM) | Must     |
| XSS prevention                 | Must     |
| CSRF protection                | Must     |
| Rate limiting (auth)           | Must     |
| Input validation (Pydantic)    | Must     |
| RBAC enforcement               | Must     |

### 5.4 Availability

| Requirement             | Target    |
| ----------------------- | --------- |
| Uptime                  | 99% (MVP) |
| Health check endpoint   | Must      |
| Graceful error handling | Must      |
| Database backups        | Daily     |

### 5.5 Browser Support

| Browser            | Support |
| ------------------ | ------- |
| Chrome (latest 2)  | Must    |
| Firefox (latest 2) | Must    |
| Safari (latest 2)  | Should  |
| Edge (latest 2)    | Should  |

---

## 6. Constraints

### 6.1 Technical Constraints

- Backend: Python 3.12+, FastAPI
- Frontend: React 18+, TypeScript, Vite, Tailwind CSS, Shadcn UI
- Database: PostgreSQL 18+
- Cache: Redis 7+
- Deployment: AWS (ECS or EC2)
- AI: Claude API (primary), OpenAI (fallback) Ollama(local)

### 6.2 Timeline Constraints

- Total development time: 10 weeks
- Must be deployable on AWS
- Must demonstrate advanced FastAPI/React features/WebSockets/AI features

### 6.3 Resource Constraints

- Solo developer 
- Limited budget (AWS free tier + minimal)

---

## 7. Glossary

| Term          | Definition                                                   |
| ------------- | ------------------------------------------------------------ |
| WBS           | Work Breakdown Structure - hierarchical task decomposition   |
| Critical Path | Longest dependency chain determining project end date        |
| Slack/Float   | Time a task can slip without affecting project end           |
| Milestone     | Zero-duration task marking a significant point               |
| Summary Task  | Parent task that rolls up child task data                    |
| ASAP          | As Soon As Possible - earliest scheduling                    |
| ALAP          | As Late As Possible - latest scheduling                      |
| MSO           | Must Start On - hard start constraint                        |
| MFO           | Must Finish On - hard finish constraint                      |
| FS            | Finish-to-Start - successor starts when predecessor finishes |
| FF            | Finish-to-Finish - both tasks finish together                |
| SS            | Start-to-Start - both tasks start together                   |
| SF            | Start-to-Finish - predecessor starts when successor finishes |
| Lag           | Delay between dependent tasks                                |
| BCWS          | Budgeted Cost of Work Scheduled (Planned Value)              |
| BCWP          | Budgeted Cost of Work Performed (Earned Value)               |
| ACWP          | Actual Cost of Work Performed                                |
| RBAC          | Role-Based Access Control                                    |

---

## Document History

| Version | Date       | Author    | Changes                              |
| ------- | ---------- | --------- | ------------------------------------ |
| 1.0     | 2026-02-05 | Ermir | Initial draft                        |
| 2.0     | 2026-02-05 | Ermir | Scoped to V2.0 MVP                   |
| 3.0     | 2026-02-06 | Ermir | Aligned with database-schema.md v3.0 |
