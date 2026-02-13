# Sophikon V1.0 - Implementation Plan

**Version:** 2.0
**Date:** 2026-02-13

---

## Project Overview

| Attribute    | Value                               |
| ------------ | ----------------------------------- |
| Project Name | Sophikon V1.0                       |
| Start Date   | February 2026                       |
| Target MVP   | April 2026 (8-10 weeks)             |
| Target V1.0  | July 2026                           |
| Tech Stack   | FastAPI + PostgreSQL + React + Vite |

---

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Project Setup & Core Backend

**Backend Tasks:**

- [x] Initialize FastAPI project structure
- [x] Create core config (settings, database connection)
- [x] Create main.py with FastAPI app + CORS
- [x] Set up PostgreSQL database
- [x] Configure SQLAlchemy ORM
- [x] Create Alembic migrations setup
- [x] Implement auth models (User, Role, RefreshToken, PasswordReset)
- [x] Implement core models (Project, Task, Resource, Assignment, Dependency)
- [x] Implement project collaboration models (ProjectMember, ProjectInvitation)
- [x] Implement calendar models (Calendar, CalendarException)
- [x] Implement baseline models (TaskBaseline, AssignmentBaseline)
- [x] Implement resource detail models (ResourceRate, ResourceAvailability)
- [x] Implement collaboration models (Comment, Attachment, Notification)
- [x] Implement time tracking model (TimeEntry)
- [x] Implement AI models (AIConversation, AIMessage, AIUsage)
- [x] Implement audit model (ActivityLog)
- [x] Set up authentication (JWT)
- [x] Create basic CRUD endpoints

**DevOps Tasks:**

- [x] Docker & docker-compose setup
- [x] Development environment documentation
- [x] CI/CD pipeline (GitHub Actions)
- [x] Pre-commit hooks (linting, formatting)

**Deliverables:**

- Running backend with basic API
- Database schema v1
- Docker development environment

---

### Week 2: Frontend Foundation

**Frontend Tasks:**

- [x] Initialize React + Vite + TypeScript project
- [x] Set up folder structure
- [x] Configure Tailwind CSS
- [x] Set up React Router
- [x] Implement authentication UI (login/register)
- [x] Create API client (Axios/fetch wrapper)
- [x] Set up state management (Zustand or Redux Toolkit)
- [x] Create base layout components
- [ ] Convert landing page mockup to production static HTML
- [ ] Landing page SEO (meta tags, Open Graph, structured data)

**Architecture Decision:** Landing page is a standalone static HTML file (not React). The React SPA lives under `/app/*`. Nginx routes: `/` → static landing, `/app/*` → React SPA, `/api/*` → FastAPI.

**Deliverables:**

- Static landing page (SEO-ready, no JS dependency)
- Running frontend SPA that connects to backend
- User can register/login
- Basic navigation structure

---

### Week 2.5: Multi-Tenancy & Navigation Architecture

**Why now:** Teacher's approval requires multi-tenancy ("users can be part of a company or group") and a permission system. Building this before Task CRUD ensures every feature is multi-tenant from the start, avoiding costly refactoring later.

**Backend:**

- [x] Organization model (`organization` table: id, name, slug, settings, created_at)
- [x] OrganizationMember model (`organization_member` table: id, org_id, user_id, role, joined_at)
- [x] Alembic migration: add `organization_id` FK to `project` table
- [ ] Alembic migration: auto-create personal org for existing users
- [x] Organization CRUD endpoints (create, update, list)
- [x] Organization member endpoints (invite, remove, list, change role)
- [x] Update `deps.py`: add `get_org_or_404()` dependency with org membership check
- [x] Update `project_service.py`: scope project queries by `organization_id`
- [ ] Update `auth_service.py`: auto-create personal org on user registration

**Frontend:**

- [ ] Restructure routing: global layout (`/dashboard`, `/projects`) vs project layout (`/projects/:id/tasks`)
- [ ] Org-aware sidebar: global mode (Dashboard, Projects) vs project mode (Tasks, Gantt, Resources)
- [ ] Org switcher component (if user belongs to multiple orgs)
- [ ] "Back to Projects" navigation when inside a project
- [ ] RBAC-filtered sidebar items (e.g., viewers don't see Resources)

**Deliverables:**

- Users belong to organizations
- Projects are scoped to organizations (data isolation)
- Sidebar switches between global and project navigation
- RBAC enforced at org and project level

---

## Phase 2: Core Features (Weeks 3-5)

### Week 3: Task Management

**Backend:**

- [ ] Task CRUD with hierarchy support (indent/outdent, summary roll-up)
- [ ] WBS code auto-generation and regeneration
- [ ] Task reordering API (drag-drop support)
- [ ] Dependency CRUD with validation (circular detection)
- [ ] Bulk operations (create, update, delete)
- [ ] Soft-delete cascades to children

**Frontend:**

- [ ] Projects list page (`/projects` — cards with status, progress)
- [ ] Create project dialog
- [ ] Task table view (spreadsheet-like, inside `/projects/:id/tasks`)
- [ ] Task detail panel/modal
- [ ] Inline editing in table
- [ ] Drag-drop for reordering
- [ ] Indent/outdent buttons
- [ ] Dependency creation UI

**Deliverables:**

- Full task CRUD working within org-scoped projects
- Hierarchical task display with WBS codes
- Dependencies can be created

---

### Week 4: Gantt Chart

**Frontend:**

- [ ] Evaluate/integrate Gantt library (options: Frappe Gantt, DHTMLX, custom)
- [ ] Gantt chart component with task bars
- [ ] Dependency arrows rendering
- [ ] Timeline header (zoom levels)
- [ ] Scroll synchronization (table + chart)
- [ ] Today line
- [ ] Milestone display
- [ ] Progress bar on tasks

**Backend:**

- [ ] Optimized endpoint for Gantt data
- [ ] Date calculation helpers

**Deliverables:**

- Working Gantt chart view
- Visual dependencies
- Basic interactivity (click to select)

---

### Week 5: Scheduling Engine

**Backend:**

- [ ] Forward scheduling algorithm
- [ ] Critical path calculation
- [ ] Slack/float calculation
- [ ] Constraint handling (ASAP, ALAP, MSO, etc.)
- [ ] Recalculate on dependency/date changes
- [ ] Scheduling API endpoint

**Frontend:**

- [ ] Critical path highlighting
- [ ] Slack display
- [ ] Auto-recalculate indicator
- [ ] Manual vs auto scheduling toggle

**Deliverables:**

- Automatic date calculation based on dependencies
- Critical path visible
- Schedule respects constraints

---

## Phase 3: Resources & AI MVP (Weeks 6-7)

### Week 6: Resource Management

**Backend:**

- [ ] Resource CRUD
- [ ] Assignment CRUD
- [ ] Resource utilization calculation
- [ ] Over-allocation detection
- [ ] Calendar model (basic)

**Frontend:**

- [ ] Resource sheet view
- [ ] Resource assignment UI (in task detail)
- [ ] Resource utilization view (basic)
- [ ] Over-allocation warning display

**Deliverables:**

- Resources can be created and assigned
- Utilization visible
- Over-allocation warnings

---

### Week 7: AI Integration MVP

**Backend:**

- [ ] AI service layer abstraction
- [ ] Claude API integration
- [ ] AI Chat endpoint (basic queries)
- [ ] AI Task Estimation endpoint
- [ ] Prompt templates system

**Frontend:**

- [ ] AI Chat panel component
- [ ] "Estimate with AI" button on tasks
- [ ] AI suggestion cards (basic)

**Deliverables:**

- Can chat with AI about project
- AI can estimate task durations
- Basic AI infrastructure in place

---

## Phase 4: Polish & MVP Release (Weeks 8-10)

### Week 8: Import/Export & Baseline

**Backend:**

- [ ] MS Project XML import (using library)
- [ ] MS Project XML export
- [ ] Baseline save/load
- [ ] Baseline comparison calculations

**Frontend:**

- [ ] Import file upload UI
- [ ] Export button/menu
- [ ] Baseline save dialog
- [ ] Baseline comparison in Gantt

**Deliverables:**

- Can import/export MS Project files
- Baseline functionality working

---

### Week 9: Collaboration & Polish

**Backend:**

- [ ] WebSocket setup for real-time updates
- [ ] Activity log implementation
- [ ] Notification delivery (in-app + email)

**Frontend:**

- [ ] Project member management UI (invite, change role, remove — uses org membership)
- [ ] Real-time updates (WebSocket)
- [ ] Notification center
- [ ] UI polish and consistency
- [ ] Loading states and error handling
- [ ] Keyboard shortcuts

**Deliverables:**

- Multi-user collaboration working (built on org/project RBAC from Week 2.5)
- Real-time sync
- Polished UI

---

### Week 10: Testing & MVP Launch

**Tasks:**

- [ ] End-to-end testing
- [ ] Performance testing (1000+ tasks)
- [ ] Security review
- [ ] Bug fixes
- [ ] Documentation (user guide, API docs)
- [ ] Production deployment setup
- [ ] MVP Launch!

**Deliverables:**

- Stable MVP ready for users
- Documentation complete
- Deployed to production

---

## Phase 5: V1.0 Features (Weeks 11-20)

### Advanced AI Features

- AI Project Planner (generate plan from description)
- AI Risk Detector
- AI Schedule Optimizer
- AI Report Generator

### Additional Features

- PERT/Network diagram view
- Advanced resource leveling
- Earned value tracking
- PDF export
- Advanced reporting
- Mobile-responsive improvements

### Enterprise Features

- SSO/SAML authentication
- Audit logging
- Advanced permissions
- API rate limiting
- Usage analytics

---

## Tech Stack Details

### Backend

```
Python 3.12+
├── FastAPI (web framework)
├── SQLAlchemy 2.0 (ORM)
├── Alembic (migrations)
├── PostgreSQL 16 (database)
├── Redis (caching, sessions)
├── Celery (background tasks)
├── Pydantic (validation)
├── python-jose (JWT)
├── httpx (HTTP client for AI APIs)
└── pytest (testing)
```

### Frontend

```
Node.js 20+
├── React 19 (UI library)
├── Vite (build tool)
├── TypeScript (language)
├── Tailwind CSS (styling)
├── React Router (navigation)
├── Zustand (state management)
├── TanStack Query (data fetching)
├── Frappe Gantt / custom (Gantt chart)
├── Radix UI (accessible components)
└── Vitest + Playwright (testing)
```

### Infrastructure

```
├── Docker & Docker Compose
├── GitHub Actions (CI/CD)
├── Nginx (reverse proxy)
├── Let's Encrypt (SSL)
└── AWS/GCP/Vercel (hosting)
```

---

## Team & Responsibilities

| Role               | Responsibilities                                 |
| ------------------ | ------------------------------------------------ |
| Backend Developer  | API, database, scheduling engine, AI integration |
| Frontend Developer | React UI, Gantt chart, state management          |
| Full-stack         | Both + DevOps                                    |
| AI/ML (optional)   | Advanced AI features, prompt engineering         |

---

## Risk Management

| Risk                            | Probability | Impact | Mitigation                                            |
| ------------------------------- | ----------- | ------ | ----------------------------------------------------- |
| Gantt chart complexity          | High        | High   | Evaluate libraries early, have fallback plan          |
| Scheduling algorithm bugs       | Medium      | High   | Thorough testing, reference MS Project behavior       |
| AI costs too high               | Medium      | Medium | Caching, usage limits, local LLM option               |
| Performance with large projects | Medium      | High   | Early performance testing, pagination, virtualization |
| MS Project compatibility issues | Medium      | Medium | Focus on common features, document limitations        |

---

## Success Criteria for MVP

- [ ] User can create account and login
- [ ] Users belong to organizations (multi-tenancy)
- [ ] Organization members can access org's projects (data isolation)
- [ ] RBAC enforced at org and project level
- [ ] User can create project with tasks (within an org)
- [ ] Tasks support hierarchy (WBS)
- [ ] Dependencies work correctly
- [ ] Gantt chart displays and is interactive
- [ ] Scheduling auto-calculates dates
- [ ] Resources can be assigned to tasks
- [ ] AI chat answers basic project questions
- [ ] Can import/export MS Project XML
- [ ] Real-time collaboration works
- [ ] Performance: 500+ tasks render smoothly

---

## Document History

| Version | Date       | Author | Changes                                                      |
| ------- | ---------- | ------ | ------------------------------------------------------------ |
| 1.0     | 2026-02-05 | Ermir  | Initial draft                                                |
| 2.0     | 2026-02-13 | Ermir  | Added multi-tenancy (Week 2.5), restructured navigation/RBAC |
