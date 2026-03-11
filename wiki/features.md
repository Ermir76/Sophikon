# Features

## Legend

| Symbol | Meaning               |
| ------ | --------------------- |
| ✅      | Implemented & working |
| 🔲      | Planned               |
| ⚙️      | Schema-only (model exists, no API/UI) |

---

## V1.0 "Foundation" — University MVP

### Authentication & Users

| Feature                              | Status |
| ------------------------------------ | ------ |
| User registration (email/password)   | ✅      |
| Login with JWT (access + refresh)    | ✅      |
| Email verification (send + confirm)  | ✅      |
| Password reset flow                  | ✅      |
| Cookie-based tokens (path-scoped)    | ✅      |
| Rate limiting (SlowAPI)              | ✅      |
| OAuth (Google)                       | 🔲      |
| Password max_length (bcrypt DoS fix) | ✅      |
| Swagger docs disabled in production  | ✅      |

### Multi-Tenancy & Organizations

| Feature                              | Status |
| ------------------------------------ | ------ |
| Organization CRUD                    | ✅      |
| Organization membership & roles      | ✅      |
| Auto-create personal org on register | ✅      |
| Org switcher (multi-org users)       | ✅      |
| Data isolation per organization      | ✅      |
| Org roles: owner, admin, member      | ✅      |

### Project Management

| Feature                              | Status |
| ------------------------------------ | ------ |
| Project CRUD (within org)            | ✅      |
| Project overview page                | ✅      |
| Project settings                     | ✅      |
| Project member management (invite, remove, RBAC) | ✅ |
| Project invitation accept flow (email link) | ✅ |
| Project activity feed                | ✅      |
| RBAC enforcement (owner, manager, member, viewer) | ✅ |
| RBAC-filtered sidebar               | ✅      |

### Task Management

| Feature                              | Status |
| ------------------------------------ | ------ |
| Task CRUD with hierarchy (WBS)       | ✅      |
| WBS code auto-generation             | ✅      |
| Indent/outdent (parent reassignment) | ✅      |
| Drag-drop reordering                 | ✅      |
| Bulk operations (create, update, delete) | ✅  |
| Soft-delete cascades to children     | ✅      |
| Inline editing in table              | ✅      |
| Task detail panel                    | ✅      |
| Milestones                           | ✅      |
| Task constraints (ASAP, ALAP, MSO, MFO, etc.) | ✅ |
| Scheduling types (Fixed Duration/Work/Units)   | ✅ |
| Task progress (% complete)           | ✅      |
| Task notes                           | ✅      |

### Dependencies

| Feature                              | Status |
| ------------------------------------ | ------ |
| Finish-to-Start (FS)                | ✅      |
| Other types (FF, SS, SF)            | ✅      |
| Lag time                            | ✅      |
| Dependency creation UI              | ✅      |
| Circular dependency prevention      | ✅ (partial) |

### Scheduling Engine

| Feature                              | Status |
| ------------------------------------ | ------ |
| Forward scheduling algorithm         | ✅      |
| Critical path calculation            | ✅      |
| Slack/float calculation              | ✅      |
| Constraint handling                  | ✅      |
| Recalculate on changes              | ✅      |
| Manual vs auto scheduling toggle     | ✅      |

### Gantt Chart

| Feature                              | Status |
| ------------------------------------ | ------ |
| Task bars (custom canvas)            | ✅      |
| Dependency arrows                    | ✅      |
| Timeline zoom (day/week/month)       | ✅      |
| Scroll synchronization (table+chart) | ✅      |
| Today line                           | ✅      |
| Milestone display (diamonds)         | ✅      |
| Progress bar on tasks                | ✅      |
| Critical path highlighting           | ✅      |
| Drag to move/resize                  | 🔲      |

### Resource Management

| Feature                              | Status |
| ------------------------------------ | ------ |
| Resource CRUD (work, material, cost) | ✅      |
| Resource assignment to tasks         | ✅      |
| Resource utilization view            | ✅      |
| Over-allocation detection/warning    | ✅      |
| Resource workload endpoint           | ✅      |

### Calendars

| Feature                              | Status |
| ------------------------------------ | ------ |
| Work calendars (CRUD)                | ✅      |
| Calendar exceptions (holidays)       | ✅      |
| Calendar inheritance (base calendar) | ✅      |
| Calendar-aware scheduling            | ✅      |
| Calendar management UI (frontend)    | 🔲 Stub — "coming soon" placeholder |
| Visual calendar view (frontend)      | 🔲 Planned |

### AI Features

| Feature                              | Status |
| ------------------------------------ | ------ |
| AI Chat (SSE streaming)             | ✅      |
| AI Task Estimation                   | ✅      |
| AI Suggestions                       | ✅      |
| Standalone AI microservice           | ✅      |
| Mock mode for development            | ✅      |
| Live LLM mode (Anthropic/OpenAI/Gemini) | ✅ (configurable) |

### Collaboration & Real-time

| Feature                              | Status |
| ------------------------------------ | ------ |
| Comments (polymorphic, threaded)     | ✅      |
| WebSocket real-time project updates  | ✅      |
| WebSocket user notifications         | ✅      |
| In-app notifications inbox           | ✅      |
| Activity log                         | ✅      |
| Notification settings                | ✅      |

### Infrastructure

| Feature                              | Status |
| ------------------------------------ | ------ |
| Docker Compose (full stack)          | ✅      |
| AWS deployment documented            | ✅      |
| CI/CD (GitHub Actions)               | ✅      |
| Pre-commit hooks (Ruff + ESLint)     | ✅      |
| SSL/HTTPS (Let's Encrypt)            | ✅ (documented) |

### Not Yet Implemented (V1.0 scope)

| Feature                              | Target  |
| ------------------------------------ | ------- |
| MS Project XML import/export         | Week 8  |
| CSV import/export                    | Week 8  |
| Baseline save/compare                | Week 8  |
| Landing page SEO                     | Week 2  |

---

## V1.1 "Resources" — Planned

Resource leveling, cost tracking, baselines, advanced reports.

## V1.2 "Intelligence" — Planned

AI Project Planner, AI Risk Detector, AI Schedule Optimizer, AI Report Generator, integrations (Slack, email, webhooks), mobile-responsive improvements.

## V2.0 "Enterprise" — Future

SSO/SAML, LDAP, audit logging, data retention, white-label, field-level permissions, GraphQL API.

---

*Evidence: [`docs/ROADMAP.md`](../docs/ROADMAP.md), [`docs/03-implementation/project-plan.md`](../docs/03-implementation/project-plan.md), codebase endpoints and services*
