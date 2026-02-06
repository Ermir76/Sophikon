# Sophikon V1.0 - Version Roadmap

**Last Updated:** 2026-02-05

---

┌─────────────────────────────────────────────────────────────────────────┐
│  V1.0 "Foundation"  │  V1.1 "Resources"  │  V1.2 "Intelligence"  │ V2+ │
│  ─────────────────  │  ────────────────  │  ──────────────────   │     │
│  • Core PM          │  • Resources       │  • AI Planner         │  E  │
│  • Tasks + WBS      │  • Assignments     │  • AI Risk Detection  │  N  │
│  • Dependencies     │  • Utilization     │  • AI Optimizer       │  T  │
│  • Gantt Chart      │  • Calendars       │  • AI Reports         │  E  │
│  • AI Chat          │  • Leveling        │  • Learning from data │  R  │
│  • AI Estimation    │  • Cost Tracking   │  • Integrations       │  P  │
│  • Basic Collab     │  • Baselines       │  • Mobile App         │  R  │
│  • Import/Export    │  • Reports         │  • Offline Mode       │  I  │
│                     │                    │                       │  S  │
│  10 weeks           │  +6 weeks          │  +8 weeks             │  E  │
│  University MVP     │  Community         │  Community            │     │
└─────────────────────────────────────────────────────────────────────────┘

---

## V1.0 "Foundation" (University MVP)

**Timeline:** 10 weeks
**Goal:** Working PM tool with AI, deployed on AWS

### Core Features

#### Project Management

| Feature                     | Priority | Status  |
| --------------------------- | -------- | ------- |
| User registration & login   | Must     | Planned |
| OAuth (Google)              | Must     | Planned | - Check if we can use another OAuth provider
| Create/Edit/Delete projects | Must     | Planned |
| Project dashboard           | Must     | Planned |
| Project settings            | Should   | Planned |

#### Task Management

| Feature                                      | Priority | Status  |
| -------------------------------------------- | -------- | ------- |
| Task CRUD                                    | Must     | Planned |
| Task hierarchy (WBS)                         | Must     | Planned |
| Indent/Outdent tasks                         | Must     | Planned |
| Task reordering (drag & drop)                | Must     | Planned |
| Milestones                                   | Must     | Planned |
| Task constraints (ASAP, ALAP, MSO, MFO)      | Should   | Planned |
| Scheduling types (Fixed Duration/Work/Units) | Should   | Planned |
| Task progress (% complete)                   | Must     | Planned |
| Task notes                                   | Should   | Planned |

#### Dependencies

| Feature                        | Priority | Status  |
| ------------------------------ | -------- | ------- |
| Finish-to-Start (FS)           | Must     | Planned |
| Other types (FF, SS, SF)       | Should   | Planned |
| Lag time                       | Should   | Planned |
| Circular dependency prevention | Must     | Planned |
| Visual dependency creation     | Should   | Planned |

#### Scheduling Engine

| Feature                                | Priority | Status  |
| -------------------------------------- | -------- | ------- |
| Auto-calculate dates from dependencies | Must     | Planned |
| Critical path calculation              | Must     | Planned |
| Slack/float calculation                | Should   | Planned |
| Forward scheduling                     | Must     | Planned |
| Respect constraints                    | Must     | Planned |

#### Gantt Chart

| Feature                        | Priority | Status  |
| ------------------------------ | -------- | ------- |
| Display task bars              | Must     | Planned |
| Show hierarchy (indentation)   | Must     | Planned |
| Show dependencies (arrows)     | Must     | Planned |
| Show progress on bars          | Must     | Planned |
| Milestones as diamonds         | Must     | Planned |
| Timeline zoom (day/week/month) | Must     | Planned |
| Today line                     | Must     | Planned |
| Critical path highlighting     | Should   | Planned |
| Scroll synchronization         | Must     | Planned |
| Drag to move task              | Could    | Planned |
| Drag to resize duration        | Could    | Planned |

#### AI Features (V2.0)

| Feature                      | Priority | Status  |
| ---------------------------- | -------- | ------- |
| AI Chat - query project      | Must     | Planned |
| AI Chat - basic actions      | Should   | Planned |
| AI Task Estimation           | Must     | Planned |
| AI Smart Suggestions (basic) | Should   | Planned |

#### Collaboration

| Feature                            | Priority | Status  |
| ---------------------------------- | -------- | ------- |
| Invite users to project            | Must     | Planned |
| User roles (Owner, Editor, Viewer) | Must     | Planned |
| Real-time updates (WebSocket)      | Must     | Planned |
| Activity log                       | Should   | Planned |

#### Import/Export

| Feature                  | Priority | Status  |
| ------------------------ | -------- | ------- |
| Export CSV               | Must     | Planned |
| Import CSV               | Should   | Planned |
| Export MS Project XML    | Should   | Planned |
| Import MS Project XML    | Should   | Planned |
| Export PDF (Gantt image) | Could    | Planned |

#### Infrastructure

| Feature                     | Priority | Status  |
| --------------------------- | -------- | ------- |
| Docker setup                | Must     | Planned |
| AWS deployment (ECS or EC2) | Must     | Planned |
| PostgreSQL (RDS)            | Must     | Planned |
| Redis (ElastiCache)         | Must     | Planned |
| CI/CD (GitHub Actions)      | Must     | Planned |
| HTTPS/SSL                   | Must     | Planned |

### Tech Stack Showcase (V1.0)

#### FastAPI Features To Be Used

- [x] Async endpoints
- [x] Dependency Injection
- [x] Pydantic models & validation
- [x] OAuth2 + JWT authentication
- [x] WebSocket support
- [x] Background tasks (Celery)
- [x] SQLAlchemy async
- [x] Alembic migrations
- [x] File upload/download
- [x] Streaming responses (AI chat)
- [x] Middleware (CORS, logging)
- [x] Redis caching
- [x] pytest async testing
- [x] OpenAPI documentation

#### React Features To Be Used

- [x] TypeScript
- [x] Custom hooks
- [x] Context API
- [x] TanStack Query
- [x] Zustand state management
- [x] React Router (nested, protected)
- [x] Suspense + lazy loading
- [x] Error boundaries
- [x] useMemo/useCallback optimization
- [x] WebSocket integration
- [x] React Hook Form
- [x] Virtualization (large lists)
- [x] Drag and drop
- [x] Canvas/SVG rendering

---

## V1.1 "Resources" (Community Release)

**Timeline:** +6 weeks after V1.0
**Goal:** Full resource management, baselines, better tracking

### Features

#### Resource Management

| Feature                             | Priority |
| ----------------------------------- | -------- |
| Work resources (people)             | Must     |
| Material resources                  | Should   |
| Cost resources                      | Could    |
| Resource rates (standard, overtime) | Must     |
| Resource availability (max units)   | Must     |
| Resource calendar                   | Should   |
| Resource groups/teams               | Could    |

#### Assignments

| Feature                                  | Priority |
| ---------------------------------------- | -------- |
| Assign resource to task                  | Must     |
| Allocation units (%)                     | Must     |
| Work contours (flat, front-loaded, etc.) | Should   |
| Actual work tracking                     | Must     |
| Remaining work                           | Must     |

#### Resource Views

| Feature                      | Priority |
| ---------------------------- | -------- |
| Resource sheet               | Must     |
| Resource utilization view    | Must     |
| Over-allocation warnings     | Must     |
| Resource usage (time-phased) | Should   |

#### Calendars

| Feature                        | Priority |
| ------------------------------ | -------- |
| Custom calendars               | Must     |
| Calendar exceptions (holidays) | Must     |
| Calendar inheritance           | Should   |
| Working time modification      | Must     |

#### Baselines

| Feature                       | Priority |
| ----------------------------- | -------- |
| Save baseline                 | Must     |
| Multiple baselines (up to 10) | Should   |
| Baseline comparison in Gantt  | Must     |
| Variance calculations         | Must     |

#### Cost Tracking

| Feature                    | Priority |
| -------------------------- | -------- |
| Task fixed costs           | Should   |
| Resource costs calculation | Should   |
| Budget vs actual           | Could    |

#### Reports

| Feature                     | Priority |
| --------------------------- | -------- |
| Project summary report      | Must     |
| Task status report          | Must     |
| Resource utilization report | Should   |
| Export reports to PDF       | Should   |

---

## V1.2  "Intelligence" (AI-Focused Release)

**Timeline:** +8 weeks after V1.1
**Goal:** Advanced AI features, integrations

### AI Features

| Feature                                        | Priority |
| ---------------------------------------------- | -------- |
| AI Project Planner (generate from description) | Must     |
| AI Risk Detector (continuous monitoring)       | Must     |
| AI Schedule Optimizer                          | Should   |
| AI Report Generator (narrative reports)        | Must     |
| AI Dependency Suggester                        | Should   |
| AI Resource Optimizer                          | Should   |
| Learning from historical data                  | Could    |
| Custom AI model fine-tuning                    | Could    |

### Additional Views

| Feature                          | Priority |
| -------------------------------- | -------- |
| Network/PERT diagram             | Should   |
| Calendar view                    | Should   |
| Dashboard widgets (customizable) | Should   |
| Portfolio view (multi-project)   | Could    |

### Integrations

| Feature                | Priority |
| ---------------------- | -------- |
| Slack notifications    | Should   |
| Email notifications    | Must     |
| Webhook support        | Should   |
| Jira import            | Could    |
| Google Calendar sync   | Could    |
| Zapier/n8n integration | Could    |

### Mobile & Offline

| Feature                    | Priority |
| -------------------------- | -------- |
| Responsive mobile UI       | Must     |
| PWA support                | Should   |
| Offline mode (read)        | Could    |
| Offline mode (edit + sync) | Could    |

---

## V2.0 "Enterprise" (Future)

**Timeline:** 2027
**Goal:** Enterprise-ready features

### Features

- Multi-tenant architecture
- SSO/SAML authentication
- LDAP/Active Directory integration
- Advanced audit logging
- Data retention policies
- Custom branding/white-label
- Advanced permissions (field-level)
- API rate limiting (per tenant)
- SLA & support tiers
- On-premise deployment option
- Advanced security (SOC2, GDPR tools)
- Bulk operations API
- Advanced API (GraphQL option)

---

## V2.0 "Portfolio" (Future)

**Timeline:** 2027+
**Goal:** Program and portfolio management

### Features

- Multi-project portfolios
- Program management
- Cross-project dependencies
- Resource pool (shared across projects)
- Capacity planning
- Strategic alignment
- Executive dashboards
- What-if scenario planning
- Monte Carlo simulation
- Advanced analytics/BI

---

## Feature Parking Lot

Features considered but not scheduled:

| Feature                           | Reason         | Reconsider When         |
| --------------------------------- | -------------- | ----------------------- |
| Time tracking                     | Scope creep    | V3+ if requested        |
| Invoicing                         | Out of scope   | Never (use integration) |
| Native mobile apps                | Web-first      | V3+ if PWA insufficient |
| Desktop app (Electron)            | Web-first      | V3+ if requested        |
| Gantt baseline bars               | Complexity     | V2.1                    |
| Earned Value (EVM)                | Complex, niche | V3+                     |
| Custom fields                     | Complexity     | V2.2                    |
| Task dependencies across projects | Complexity     | V4                      |
| Recurring tasks                   | Complexity     | V2.2                    |
| Task splitting                    | Complexity     | V3+                     |

---

## Version Compatibility

| Version     | Database Migration                 | API Breaking Changes |
| ----------- | ---------------------------------- | -------------------- |
| V1.0 → V1.1 | Yes (additive)                     | No                   |
| V1.1 → V1.2 | Yes (additive)                     | Minor                |
| V1.x → V2.0 | Yes (may require migration script) | Possible             |

---

## How to Contribute

After V1.0 release:

1. Check [GitHub Issues](https://github.com/...) for "good first issue" label
2. Join discussions on feature proposals
3. Submit PRs against `develop` branch
4. Follow contribution guidelines

---

_This roadmap is subject to change based on community feedback and priorities._
