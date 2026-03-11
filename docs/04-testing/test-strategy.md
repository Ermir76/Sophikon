# Test Strategy

> Sophikon testing plan: current coverage, identified gaps, and prioritized action items.
>
> Last audited: 2026-03-10

---

## 1. Testing Architecture

### Test Pyramid

```
         ╱╲
        ╱ E2E╲           Playwright (FE) — 8 specs
       ╱──────╲          Backend E2E — empty (stub only)
      ╱ Integr. ╲        7 flow files + 1 persistence file
     ╱────────────╲      25 integration tests
    ╱    Unit       ╲    44 backend files, 41 frontend files
   ╱─────────────────╲   ~250+ unit tests
  ╱____________________╲
```

### Infrastructure

| Concern           | Solution                                                               |
| ----------------- | ---------------------------------------------------------------------- |
| Backend runner    | pytest + pytest-asyncio (async mode=auto)                              |
| DB isolation      | Savepoint-based rollback — real PostgreSQL, no in-memory DB            |
| Email mocking     | Global `autouse` fixture mocks `_get_mail_client` to prevent real SMTP |
| WebSocket mocking | Global `autouse` fixture neutralizes ws manager start/publish          |
| Rate limit        | Global `autouse` fixture disables SlowAPI for all tests                |
| Frontend runner   | Vitest (unit/component)                                                |
| Frontend E2E      | Playwright                                                             |
| Fixtures          | `conftest.py` provides `client` (AsyncClient via ASGI) and `session`   |

---

## 2. Current Coverage by Domain

### Backend — API Layer (`tests/unit/api/v1/`)

| Domain              | File                           | Tests | Happy | Error | RBAC | Edge |
| ------------------- | ------------------------------ | ----- | ----- | ----- | ---- | ---- |
| **Auth**            | `test_auth.py`                 | 15    | ✅    | ✅    | —    | ⚠️   |
| **Email Verify**    | `test_email_verification.py`   | ~5    | ✅    | ✅    | —    | ⚠️   |
| **Organizations**   | `test_organizations.py`        | 21    | ✅    | ✅    | ✅   | ✅   |
| **Org Members**     | `test_organization_members.py` | ~10   | ✅    | ✅    | ✅   | ⚠️   |
| **Projects**        | `test_projects.py`             | 30    | ✅    | ✅    | ✅   | ✅   |
| **Project Members** | `test_project_members.py`      | 11    | ✅    | ✅    | ✅   | ✅   |
| **Tasks**           | `test_tasks.py`                | 38    | ✅    | ✅    | ✅   | ✅   |
| **Task Bulk**       | `test_task_bulk.py`            | ~10   | ✅    | ✅    | ✅   | ⚠️   |
| **Dependencies**    | `test_dependencies.py`         | 20    | ✅    | ✅    | ✅   | ✅   |
| **Scheduling**      | `test_scheduling.py`           | 5     | ✅    | ⚠️    | —    | ❌   |
| **Resources**       | `test_resources.py`            | 17    | ✅    | ✅    | ✅   | ⚠️   |
| **Assignments**     | `test_assignments.py`          | 17    | ✅    | ✅    | ✅   | ✅   |
| **Utilization**     | `test_utilization.py`          | 5     | ✅    | ✅    | —    | ⚠️   |
| **Calendars**       | `test_calendars.py`            | 13    | ✅    | ✅    | —    | ⚠️   |
| **Comments**        | `test_comments.py`             | 9     | ✅    | ✅    | ✅   | ✅   |
| **Notifications**   | `test_notifications.py`        | 7     | ✅    | ✅    | ✅   | ⚠️   |
| **AI**              | `test_ai.py`                   | 5     | ✅    | —     | ✅   | ⚠️   |
| **WebSocket**       | `test_ws.py`                   | 11    | ✅    | ✅    | ✅   | ✅   |
| **Activity**        | `test_activity.py`             | ~3    | ✅    | —     | —    | ⚠️   |
| **Insights**        | `test_insights.py`             | ~3    | ✅    | —     | —    | ⚠️   |

**Legend:** ✅ Good coverage · ⚠️ Partial · ❌ Missing

### Backend — Service Layer (`tests/unit/service/`)

| Service                         | Test File                            | Tests | Coverage Quality              |
| ------------------------------- | ------------------------------------ | ----- | ----------------------------- |
| `activity_log_service`          | `test_activity_log_service.py`       | 2     | ⚠️ Minimal                    |
| `ai_service`                    | `test_ai_service.py`                 | 9     | ✅ Good                       |
| `assignment_service`            | `test_assignment_service.py`         | 2     | ⚠️ Notification only          |
| `calendar_utils`                | `test_calendar_utils.py`             | 15+   | ✅ Good                       |
| `comment_service`               | `test_comment_service.py`            | 5     | ✅ Good                       |
| `email_service`                 | `test_email_service.py`              | 3     | ✅ Good                       |
| `insights_service`              | `test_insights_service.py`           | 6     | ✅ Good                       |
| `notification_service`          | `test_notification_service.py`       | 1     | ⚠️ Minimal                    |
| `notification_tasks`            | `test_notification_tasks.py`         | 2     | ✅ Good                       |
| `project_member_service`        | `test_project_member_service.py`     | 3     | ✅ Good                       |
| `project_service`               | `test_project_service.py`            | 2     | ⚠️ Minimal                    |
| `realtime_service`              | `test_realtime_service.py`           | 5     | ✅ Good                       |
| `ws_protocol`                   | `test_ws_protocol.py`                | 8     | ✅ Good                       |
| `ws_session_service`            | `test_ws_session_service.py`         | 5     | ✅ Good                       |
| `service_layer_architecture`    | `test_service_layer_architecture.py` | 1     | ✅ Architectural import guard |
| **auth_service**                | ❌ None                              | 0     | ❌ Tested via API only        |
| **calendar_service**            | ❌ None                              | 0     | ❌ No dedicated tests         |
| **dependency_service**          | ❌ None                              | 0     | ❌ Tested via API only        |
| **organization_service**        | ❌ None                              | 0     | ❌ Tested via API only        |
| **organization_member_service** | ❌ None                              | 0     | ❌ Tested via API only        |
| **resource_service**            | ❌ None                              | 0     | ❌ Tested via API only        |
| **scheduling_service**          | ❌ None                              | 0     | ❌ Critical gap               |
| **task_bulk_service**           | ❌ None                              | 0     | ❌ Tested via API only        |
| **task_hierarchy_service**      | ❌ None                              | 0     | ❌ Tested via API only        |
| **task_rollup_service**         | ❌ None                              | 0     | ❌ Via integration only       |
| **task_service**                | ⚠️ Integration only                  | 3     | ⚠️ Persistence focus          |
| **utilization_service**         | ❌ None                              | 0     | ❌ Tested via API only        |

### Backend — Integration Flows (`tests/integration/flows/`)

| Flow File                  | Tests | What It Covers                                                                            |
| -------------------------- | ----- | ----------------------------------------------------------------------------------------- |
| `test_auth_flows.py`       | 3     | Personal org creation, token rotation, atomic failure                                     |
| `test_task_flows.py`       | 6     | WBS inheritance, parent cascade, indent/outdent, summary rollup, ancestor rollup, reorder |
| `test_scheduling_flows.py` | 6     | Full CPM flow, RBAC, dep change/delete reschedule, constraint override, parallel paths    |
| `test_project_flows.py`    | 2     | Non-member access, soft delete cascade                                                    |
| `test_org_flows.py`        | 2     | Invite visibility, remove member visibility                                               |
| `test_dependency_flows.py` | 1     | Cascade delete                                                                            |
| `test_assignment_flows.py` | 2     | Duplicate blocked, cross-project blocked                                                  |

### Frontend — Unit Tests (Vitest)

| Feature           | Test Files | Components | Hooks | Store | Service | Pages |
| ----------------- | ---------- | ---------- | ----- | ----- | ------- | ----- |
| **AI**            | 4          | ✅ 1       | ✅ 1  | ✅ 1  | ✅ 1    | —     |
| **Auth**          | 3          | —          | ✅ 1  | ✅ 1  | —       | ✅ 1  |
| **Dashboard**     | 1          | —          | ✅ 1  | —     | —       | —     |
| **Notifications** | 3          | —          | ✅ 2  | ✅ 1  | —       | —     |
| **Organizations** | 2          | —          | ✅ 1  | ✅ 1  | —       | —     |
| **Projects**      | 7          | ✅ 3       | ✅ 4  | ✅ 1  | —       | ✅ 3  |
| **Tasks**         | 10         | ✅ 5       | ✅ 4  | —     | —       | ✅ 1  |
| **Resources**     | 1          | —          | ✅ 1  | —     | —       | —     |
| **Shared**        | 2          | —          | —     | —     | ✅ 1    | —     |
| **Gantt**         | ❌ **0**   | —          | —     | —     | —       | —     |
| **Calendar**      | ❌ **0**   | —          | —     | —     | —       | —     |
| **Reports**       | ❌ **0**   | —          | —     | —     | —       | —     |

### Frontend — E2E Tests (Playwright)

| Spec File              | Covers                                     |
| ---------------------- | ------------------------------------------ |
| `auth.spec.ts`         | Login, register, logout, session           |
| `org-flow.spec.ts`     | Create org, switch org, org settings       |
| `org-members.spec.ts`  | Invite, role change, remove member         |
| `project-flow.spec.ts` | Create project, project overview, settings |
| `task-flow.spec.ts`    | Create task, hierarchy, inline edit, bulk  |
| `ai-panel.spec.ts`     | Open AI panel, send message, stream        |
| `nav-layout.spec.ts`   | Sidebar, breadcrumbs, responsive layout    |
| `error-states.spec.ts` | 404 page, error boundary, network errors   |

---

## 3. Identified Gaps

### 🔴 Critical Gaps (Must-Fix for V1.0)

#### G-01: Scheduling Engine Has No Unit-Level Tests

**Risk:** The scheduling engine (`scheduling_service.py`, 647 lines) is the most complex and business-critical code but has zero dedicated service-level unit tests. The 5 API tests and 6 integration tests only cover basic FS chains and one parallel-paths scenario.

**Missing tests:**

- [ ] Each constraint type individually: MSO, MFO, SNET, SNLT, FNET, FNLT, ALAP
- [ ] SS, FF, SF dependency types (only FS is tested end-to-end)
- [ ] Negative lag (lead time) producing correct early starts
- [ ] Mixed dependency types on same successor (e.g., FS + SS from different predecessors)
- [ ] Topological sort with disconnected subgraphs
- [ ] Backward pass correctness (LS/LF values)
- [ ] Slack calculation accuracy (total_slack and free_slack)
- [ ] Summary tasks excluded from CPM but rolled up correctly
- [ ] Empty project (0 tasks) → project_finish_date = start_date
- [ ] Single task, no dependencies → ES=project start, total_slack=0
- [ ] Calendar exceptions affecting scheduling (holidays)

**Recommended file:** `tests/unit/service/test_scheduling_service.py`

---

#### G-02: Auth Service Has No Dedicated Unit Tests

**Risk:** Auth logic (password hashing, token generation, refresh rotation, bcrypt DoS protection) is tested only through API-level tests which don't isolate business logic from HTTP concerns.

**Missing tests:**

- [ ] Password hashing + verification (bcrypt rounds)
- [ ] Password max_length enforcement (bcrypt DoS prevention)
- [ ] Access token generation with correct claims and expiry
- [ ] Refresh token rotation: old token invalidated after use
- [ ] Refresh token reuse detection (stolen token scenario)
- [ ] Expired access token → raises AuthenticationError
- [ ] Expired refresh token → raises AuthenticationError
- [ ] User with `is_active=False` → rejected

**Recommended file:** `tests/unit/service/test_auth_service.py`

---

#### G-03: Task Rollup Service Has No Dedicated Tests

**Risk:** Summary task rollup (`task_rollup_service.py`) computes aggregated dates, duration, progress, and cost for parent tasks based on children. Errors cascade up the entire WBS tree.

**Missing tests:**

- [ ] `apply_summary_rollup` — start=min(children.start), finish=max(children.finish)
- [ ] Duration recalculation in working minutes using calendar
- [ ] Progress weighted by duration: `∑(child.percent × child.duration) / ∑(child.duration)`
- [ ] Cost aggregation: fixed_cost, total_cost, BCWS, BCWP, ACWP
- [ ] `clear_summary_rollup` — resets to single-day leaf task
- [ ] `sync_leaf_duration_progress` — actual_duration, remaining_duration derivation
- [ ] `validate_summary_rollup_edit` — rejects writes to computed fields on summary tasks
- [ ] Edge: parent with single child
- [ ] Edge: parent with all children at 100% complete
- [ ] Edge: parent with zero-duration milestone children

**Recommended file:** `tests/unit/service/test_task_rollup_service.py`

---

### 🟡 Important Gaps (Should-Fix for V1.0)

#### G-04: Calendar Service Has No Tests

**Missing tests:**

- [ ] Create calendar with custom work week
- [ ] Calendar inheritance (child inherits base calendar)
- [ ] Exception overlap detection (two exceptions on same date)
- [ ] Delete calendar that is referenced by a project/resource
- [ ] Set calendar on project → scheduling uses that calendar
- [ ] `get_effective_work_week` merges base + override

**Recommended file:** `tests/unit/service/test_calendar_service.py`

---

#### G-05: Frontend Gantt Chart Has Zero Tests

**Risk:** The Gantt chart is a custom canvas renderer — the most complex frontend component. Zero tests exist.

**Missing tests:**

- [ ] `useGantt` hook: fetch tasks + dependencies, timeline zoom state
- [ ] Gantt bar positioning: x-coordinate from start_date, width from duration
- [ ] Dependency arrow rendering: FS, SS, FF, SF arrow paths
- [ ] Timeline zoom: day ↔ week ↔ month switching
- [ ] Critical path highlighting: critical tasks rendered differently
- [ ] Milestone diamond rendering
- [ ] Scroll synchronization with task table

**Recommended files:**

- `features/gantt/hooks/useGantt.test.ts`
- `features/gantt/utils/gantt-calculations.test.ts`

---

#### G-06: Utilization Service Edge Cases

**Missing tests:**

- [ ] Resource with `max_units=0` — every assignment is over-allocated
- [ ] Date range where `end_date < start_date` → error or empty result
- [ ] Zero assignments in range → all daily allocations = 0
- [ ] Overlapping assignments from same resource to different tasks
- [ ] Day-boundary edge: assignment start_date = range end_date

**Recommended file:** `tests/unit/service/test_utilization_service.py`

---

#### G-07: Task Hierarchy Service Has No Tests

**Missing tests:**

- [ ] `indent_task` — moves task under previous sibling, updates WBS
- [ ] `outdent_task` — moves task up one level, re-parents children
- [ ] Indent first task in list → rejected (no sibling above)
- [ ] Outdent root task → rejected (already at top)
- [ ] Indent/outdent preserves child subtrees
- [ ] Reorder across parents → WBS codes regenerated correctly
- [ ] Deep nesting (5+ levels) → correct outline_level computation

**Recommended file:** `tests/unit/service/test_task_hierarchy_service.py`

---

#### G-08: Missing Cross-Domain Integration Flows

| Flow                                            | Priority | Status     |
| ----------------------------------------------- | -------- | ---------- |
| Calendar exception → scheduling reschedule      | High     | ❌         |
| Resource deletion → assignment cleanup          | High     | ❌         |
| Notification delivery after comment mention     | Medium   | ⚠️ Partial |
| Project soft delete → all children soft deleted | High     | ✅ Exists  |
| Member removal → access revoked immediately     | Medium   | ❌         |
| AI chat → context includes latest tasks         | Low      | ⚠️ Partial |
| Bulk task create → summary rollup cascade       | High     | ❌         |
| Invitation accept → org membership auto-added   | Medium   | ✅ Exists  |

---

#### G-09: Frontend Missing Feature Tests

| Feature   | What to Test                                        | Priority |
| --------- | --------------------------------------------------- | -------- |
| Calendar  | useCalendar hook, CalendarPage render               | Medium   |
| Reports   | useReports hook, ReportsPage render                 | Low      |
| Resources | ResourcesPage component, utilization view rendering | Medium   |
| Dashboard | DashboardPage component, metric card rendering      | Low      |

---

### 🟢 Nice-to-Have (V1.1+)

#### G-10: Security-Focused Tests

- [ ] SQL injection via task name, project name, org slug
- [ ] XSS payload in comment `content` field
- [ ] CORS header validation (only allowed origins get `Access-Control-Allow-Origin`)
- [ ] CSRF protection with SameSite cookie
- [ ] Rate limit enforcement (re-enable limiter in specific test)
- [ ] Excessive request body size (>1MB JSON)
- [ ] UUID format validation on path params (random string → 422, not 500)

#### G-11: Concurrency Tests

- [ ] Concurrent task creation on same project (tests `lock_project_row`)
- [ ] Concurrent scheduling recalculation (should serialize)
- [ ] Two users accepting same invitation simultaneously
- [ ] Concurrent WBS code regeneration → no duplicate codes

#### G-12: Performance / Stress Tests

- [ ] Project with 500 tasks → schedule calculates in <5s
- [ ] Project with 100 tasks + 200 dependencies → no timeout
- [ ] Resource utilization over 365-day range → acceptable response time
- [ ] Bulk create 50 tasks → response time <3s

---

## 4. Action Plan

### Phase 1: Critical Engine Tests (Week 1)

Create `tests/unit/service/test_scheduling_service.py` — **highest priority**

```python
# Recommended test structure:
class TestForwardPass:
    """Test Early Start / Early Finish calculation."""
    async def test_single_task_no_deps_starts_at_project_start(...)
    async def test_fs_chain_two_tasks(...)
    async def test_ss_dependency_starts_same_day(...)
    async def test_ff_dependency_computes_start_from_finish(...)
    async def test_sf_dependency_reverses_logic(...)
    async def test_lag_adds_working_days(...)
    async def test_negative_lag_subtracts_working_days(...)

class TestBackwardPass:
    """Test Late Start / Late Finish calculation."""
    async def test_terminal_task_lf_equals_project_finish(...)
    async def test_backward_pass_propagates_lf(...)

class TestSlack:
    """Test total and free slack."""
    async def test_critical_task_has_zero_slack(...)
    async def test_non_critical_task_has_positive_slack(...)
    async def test_free_slack_vs_total_slack(...)

class TestConstraints:
    """Test all 8 constraint types."""
    async def test_asap_is_default(...)
    async def test_alap_shifts_to_late_start(...)
    async def test_mso_forces_exact_start(...)
    async def test_mfo_derives_start_from_finish(...)
    async def test_snet_takes_later_of_dep_and_constraint(...)
    async def test_snlt_caps_late_finish(...)
    async def test_fnet_pushes_start_if_needed(...)
    async def test_fnlt_caps_late_finish(...)

class TestCriticalPath:
    """Test critical path identification."""
    async def test_single_path_all_critical(...)
    async def test_parallel_paths_longest_is_critical(...)
    async def test_diamond_pattern(...)

class TestSummaryRollup:
    """Test summary task date aggregation."""
    async def test_summary_inherits_min_start_max_finish(...)
    async def test_nested_summaries_propagate(...)
```

### Phase 2: Auth & Rollup Service Tests (Week 1-2)

1. Create `tests/unit/service/test_auth_service.py` — token rotation, bcrypt DoS, password rules
2. Create `tests/unit/service/test_task_rollup_service.py` — date/duration/progress/cost aggregation
3. Create `tests/unit/service/test_calendar_service.py` — inheritance, exceptions

### Phase 3: Fill Frontend Gaps (Week 2)

1. Add Gantt tests: `features/gantt/hooks/useGantt.test.ts`
2. Add Calendar tests: `features/calendar/hooks/useCalendar.test.ts`
3. Add Resources component tests

### Phase 4: Cross-Domain Integration Flows (Week 2-3)

1. `tests/integration/flows/test_calendar_scheduling_flows.py` — calendar exception → reschedule
2. `tests/integration/flows/test_resource_cleanup_flows.py` — resource delete → assignments
3. `tests/integration/flows/test_bulk_rollup_flows.py` — bulk create → summary cascade
4. `tests/integration/flows/test_notification_flows.py` — comment mention → notification delivery

### Phase 5: Security & Concurrency (Week 3-4)

1. `tests/unit/api/v1/test_security.py` — injection, XSS, CORS, rate limit
2. `tests/integration/test_concurrency.py` — row locking, race conditions

---

## 5. Testing Conventions

### File Naming

```
tests/
├── unit/
│   ├── api/v1/test_{endpoint_file}.py     # API contract tests
│   ├── service/test_{service_name}.py     # Business logic isolation
│   ├── repository/test_{repo_name}.py     # Query behavior tests
│   ├── core/test_{core_module}.py         # Infrastructure tests
│   ├── schema/test_{schema_name}.py       # Schema validation tests
│   └── migrations/test_{migration}.py     # Migration correctness
├── integration/
│   ├── flows/test_{domain}_flows.py       # Multi-step business flows
│   ├── persistence/test_{domain}.py       # DB round-trip tests
│   └── realtime/                          # WS + notification flows
└── e2e/
    └── README.md                          # Future: full API E2E
```

### Test Function Naming

```python
# Pattern: test_{action}_{expected_outcome}[_{condition}]
async def test_create_task_success(...)
async def test_create_task_viewer_forbidden(...)
async def test_create_task_invalid_duration(...)
async def test_delete_parent_cascades_to_children(...)
```

### What Each Layer Tests

| Layer             | Tests                                   | Mocks                                | DB?               |
| ----------------- | --------------------------------------- | ------------------------------------ | ----------------- |
| **API unit**      | HTTP status, response shape, auth, RBAC | Services (optional — we use real DB) | ✅ Real           |
| **Service unit**  | Business rules, edge cases, errors      | Repository calls, external services  | ✅ Real or mocked |
| **Repository**    | Query correctness, joins, pagination    | None (pure DB)                       | ✅ Real           |
| **Integration**   | Multi-step flows, cascade effects       | External services only               | ✅ Real           |
| **Frontend unit** | Render, hooks, store mutations          | API calls (MSW or mock)              | ❌                |
| **Frontend E2E**  | Full user workflows                     | Backend (real or MSW)                | ❌                |

### Coverage Targets

| Category            | Current (est.) | Target (V1.0) | Target (V1.1) |
| ------------------- | -------------- | ------------- | ------------- |
| Backend API         | ~85%           | 90%           | 95%           |
| Backend Services    | ~45%           | 75%           | 85%           |
| Backend Integration | ~60%           | 75%           | 85%           |
| Frontend Unit       | ~50%           | 65%           | 75%           |
| Frontend E2E        | ~40%           | 55%           | 70%           |

---

## 6. Running Tests

### Backend

```bash
cd backend

# All tests
uv run pytest

# Unit only
uv run pytest tests/unit

# Integration only
uv run pytest tests/integration

# Single domain
uv run pytest tests/unit/api/v1/test_tasks.py

# With coverage report
uv run pytest --cov=app --cov-report=html

# Verbose with print output
uv run pytest -vvs tests/unit/service/test_scheduling_service.py
```

### Frontend

```bash
cd frontend

# Unit tests
npm test

# With coverage
npm test -- --coverage

# Single file
npm test -- features/gantt/hooks/useGantt.test.ts

# E2E
npm run test:e2e

# E2E single spec
npx playwright test tests/e2e/task-flow.spec.ts
```

---

## Appendix A: Full Test Inventory

### Backend Unit Tests (44 files, ~250+ tests)

**API Layer (20 files):**
`test_activity`, `test_ai`, `test_assignments`, `test_auth`, `test_calendars`, `test_comments`, `test_dependencies`, `test_deps`, `test_email_verification`, `test_insights`, `test_notifications`, `test_organization_members`, `test_organizations`, `test_project_members`, `test_projects`, `test_resources`, `test_scheduling`, `test_task_bulk`, `test_tasks`, `test_utilization`, `test_ws`

**Service Layer (15 files):**
`test_activity_log_service`, `test_ai_service`, `test_assignment_service`, `test_calendar_utils`, `test_comment_service`, `test_email_service`, `test_insights_service`, `test_notification_service`, `test_notification_tasks`, `test_project_member_service`, `test_project_service`, `test_realtime_service`, `test_service_layer_architecture`, `test_ws_protocol`, `test_ws_session_service`

**Other (9 files):**
`test_db_connection`, `test_health`, `test_user_notification_websocket_manager`, `test_websocket_manager`, `test_repository_layer`, `test_comment_entity_type_migration`, `test_comment_thread_integrity_migration`, `test_seed_industry_portfolio`

### Backend Integration Tests (8 files, 25 tests)

`test_auth_flows` (3), `test_task_flows` (6), `test_scheduling_flows` (6), `test_project_flows` (2), `test_org_flows` (2), `test_dependency_flows` (1), `test_assignment_flows` (2), `test_task_service` (3)

### Frontend Unit Tests (41 files)

See Section 2 table above.

### Frontend E2E Tests (8 specs)

`auth`, `org-flow`, `org-members`, `project-flow`, `task-flow`, `ai-panel`, `nav-layout`, `error-states`

---

_Source of truth: codebase audit performed 2026-03-10 against all `tests/` directories._
