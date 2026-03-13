# Test Strategy

> Sophikon testing plan: current coverage, identified gaps, and prioritized action items.
>
> Last audited: 2026-03-11

---

## 0. Recent Traceability (2026-03-11)

| Commit | Change | Evidence files | Validation (run by user) |
| --- | --- | --- | --- |
| `5ad6fd1` | Fixed nested-summary test determinism by setting explicit hierarchy depth in fixtures. | `backend/tests/unit/service/test_scheduling_service.py` | Targeted scheduling test passed (`test_nested_summaries_propagate_bottom_up`). |
| `f3e0021` | Hardened auth/scheduling edge behavior and expanded service-depth coverage + doc sync. | `backend/app/service/{auth_service,scheduling_service,task_rollup_service}.py`, `backend/tests/unit/service/{test_auth_service,test_task_rollup_service}.py`, `docs/04-testing/{test-implementation-plan,test-strategy}.md` | Service suite, affected API suites, and affected integration scheduling/task flow suites passed. |
| _(working tree)_ | Completed remaining backend checklist coverage: calendar/utilization pass-now depth, integration notification/bulk/resource flows, security hardening tests, and concurrency/performance suites. | `backend/tests/integration/{flows/test_{notification_flows,bulk_rollup_flows,resource_cleanup_flows}.py,test_{concurrency,performance}.py}`, `backend/tests/unit/{api/v1/test_security.py,service/test_{calendar_service,task_rollup_service,utilization_service}.py}`, `docs/04-testing/{test-implementation-plan,test-strategy}.md` | Pending user run (see handoff commands). |

---

## 1. Testing Architecture

### Test Pyramid

```
         ╱╲
        ╱ E2E╲           Playwright (FE) — 8 specs
       ╱──────╲          Backend E2E — empty (stub only)
      ╱ Integr. ╲        11 flow files + 1 persistence + 2 root suites
     ╱────────────╲      50+ integration tests
    ╱    Unit       ╲    50+ backend files, 41 frontend files
   ╱─────────────────╲   ~320+ backend unit tests (est.)
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
| `auth_service`                | `test_auth_service.py`              | 7     | ✅ Baseline added (Phase 1)  |
| `calendar_service`              | `test_calendar_service.py`           | 14    | ✅ Baseline + pass-now depth |
| `dependency_service`            | `test_dependency_service.py`         | 11    | ✅ Baseline added (Phase 1)  |
| **organization_service**        | ❌ None                              | 0     | ❌ Tested via API only        |
| **organization_member_service** | ❌ None                              | 0     | ❌ Tested via API only        |
| **resource_service**            | ❌ None                              | 0     | ❌ Tested via API only        |
| `scheduling_service`          | `test_scheduling_service.py`        | 7     | ✅ Baseline added (Phase 1)  |
| **task_bulk_service**           | ❌ None                              | 0     | ❌ Tested via API only        |
| `task_hierarchy_service`        | `test_task_hierarchy_service.py`     | 14    | ✅ Baseline added (Phase 1)  |
| `task_rollup_service`           | `test_task_rollup_service.py`       | 13    | ✅ Baseline + depth added    |
| **task_service**                | ⚠️ Integration only                  | 3     | ⚠️ Persistence focus          |
| `utilization_service`           | `test_utilization_service.py`        | 12    | ✅ Baseline + edge depth     |

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
| `test_calendar_scheduling_flows.py` | 3 | Calendar exception + default calendar switch rescheduling flows                         |
| `test_resource_cleanup_flows.py` | 3 | Resource delete/deactivate flows and assignment integrity                                |
| `test_notification_flows.py` | 5 | Mention/assignment notification delivery and read-all behavior                             |
| `test_bulk_rollup_flows.py` | 3 | Bulk create/delete/update summary rollup cascades                                         |

### Backend — Integration Concurrency/Performance (`tests/integration/`)

| File | Tests | Notes |
| ---- | ----- | ----- |
| `test_concurrency.py` | 4 | Race-window guards for create/schedule/invitation/WBS behavior |
| `test_performance.py` | 4 | Opt-in perf smoke tests (`RUN_PERF_TESTS=1`) |

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

### Phase 1 Update (2026-03-11)

- Critical gap reduction completed for:
  - `tests/unit/service/test_scheduling_service.py`
  - `tests/unit/service/test_auth_service.py`
  - `tests/unit/service/test_task_rollup_service.py`
- Additional baseline service coverage completed for:
  - `tests/unit/service/test_calendar_service.py`
  - `tests/unit/service/test_task_hierarchy_service.py`
  - `tests/unit/service/test_utilization_service.py`
  - `tests/unit/service/test_dependency_service.py`
- Baseline service-level coverage now exists for scheduling, auth, and rollup logic.
- Remaining items in G-01/G-02/G-03 are now depth-expansion follow-ups, not zero-coverage blockers.

### 🔴 Critical Gaps (Must-Fix for V1.0)

#### G-01: Scheduling Engine Needs Deeper Unit Coverage

**Risk:** The scheduling engine (`scheduling_service.py`, 647 lines) is the most complex and business-critical code. Core Phase 1 service-level depth is now covered; future additions are incremental hardening.

**Missing tests:**

Current phase status (built vs pending, updated 2026-03-11):

- [x] Each constraint type individually: MSO, MFO, SNET, SNLT, FNET, FNLT, ALAP
  Status: helper-level coverage now exists across all 8 constraint types.
- [x] SS, FF, SF dependency types (helper-level `_compute_dep_driven_date` coverage)
- [x] Negative lag (lead time) producing correct early starts
- [x] Mixed dependency types on same successor (e.g., FS + SS from different predecessors)
- [x] Topological sort with disconnected subgraphs
- [x] Backward pass correctness (LS/LF values)
- [x] Slack calculation accuracy (total_slack and free_slack)
- [x] Summary tasks excluded from CPM but rolled up correctly
- [x] Empty project (0 tasks) -> project_finish_date = start_date
- [x] Single task, no dependencies -> ES=project start, total_slack=0
- [x] Calendar exceptions affecting scheduling (holidays)

**Recommended file:** `tests/unit/service/test_scheduling_service.py`

---

#### G-02: Auth Service Needs Deeper Unit Coverage

**Risk:** Auth logic (password hashing, token generation, refresh rotation, bcrypt DoS protection) now has baseline service tests, but several security edge cases are still not covered.

**Missing tests:**

- [x] Password hashing + verification (bcrypt rounds)
- [x] Password max_length enforcement (bcrypt DoS prevention)
- [x] Access token generation with correct claims and expiry
- [x] Refresh token rotation: old token invalidated after use
- [x] Refresh token reuse detection (stolen token scenario)
- [x] Expired access token → raises AuthenticationError
- [x] Expired refresh token → raises AuthenticationError
- [x] User with `is_active=False` → rejected
- [x] Wrong password login -> rejected

**Recommended file:** `tests/unit/service/test_auth_service.py`

---

#### G-03: Task Rollup Service Needs Deeper Unit Coverage

**Risk:** Summary task rollup (`task_rollup_service.py`) now has baseline unit tests, but additional edge-case depth is still required.

**Missing tests:**

- [x] `apply_summary_rollup` -> start=min(children.start), finish=max(children.finish)
- [x] Duration recalculation in working minutes using calendar
- [x] Progress weighted by duration
- [x] Cost aggregation (actual/total/remaining)
- [x] `clear_summary_rollup` reset behavior for computed fields
- [x] `clear_summary_rollup` -> single-day leaf semantics
- [x] `sync_leaf_duration_progress` -> actual_duration/remaining_duration derivation
- [x] `validate_summary_rollup_edit` -> rejects writes to computed fields on summary tasks
- [x] Edge: parent with single child
- [x] Edge: parent with all children at 100% complete
- [x] Edge: parent with zero-duration milestone children

**Recommended file:** `tests/unit/service/test_task_rollup_service.py`

---

### 🟡 Important Gaps (Should-Fix for V1.0)

#### G-04: Calendar Service Needs Deeper Unit Coverage

**Risk:** Overlap enforcement remains pass-now permissive, but effective calendar merge runtime is now implemented and covered.

**Missing tests (depth follow-ups):**

- [x] Create calendar with custom work week
- [x] Calendar inheritance reference handling (`base_calendar_id`)
- [x] Delete calendar referenced by project/base relation (FK `SET NULL` behavior)
- [x] Exception overlap detection policy (same-date collisions)
  Status: pass-now coverage asserts overlaps are currently allowed.
- [x] Date-range exception filtering behavior
  Status: pass-now coverage asserts current calendar-scoped unfiltered listing.
- [x] Effective work-week merge semantics (base + child override) when runtime API exists
  Status: scheduler coverage now validates task-level effective base+child work-week and exception override behavior.

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

**Status (2026-03-11):** Baseline implemented in `tests/unit/service/test_utilization_service.py`.

**Remaining depth gaps:**

- [x] Resource with `max_units=0` — every assignment is over-allocated
- [x] Date range where `end_date < start_date` → error or empty result
  Status: pass-now coverage asserts empty result window (no service exception).
- [x] Zero assignments in range → all daily allocations = 0
- [x] Overlapping assignments from same resource to different tasks
- [x] Day-boundary edge: assignment start_date = range end_date

**Recommended file:** `tests/unit/service/test_utilization_service.py`

---

#### G-07: Task Hierarchy Service Needs Deeper Unit Coverage

**Status (2026-03-11):** Baseline implemented in `tests/unit/service/test_task_hierarchy_service.py`.

**Current baseline coverage:**

- [x] `indent_task` — moves task under previous sibling, updates WBS
- [x] `outdent_task` — moves task up one level, re-parents children
- [x] Indent first task in list → rejected (no sibling above)
- [x] Outdent root task → rejected (already at top)
- [x] Indent/outdent preserves child subtrees
- [x] Reorder across parents → WBS codes regenerated correctly
- [x] Deep nesting (5+ levels) → correct outline_level computation

**Recommended file:** `tests/unit/service/test_task_hierarchy_service.py`

---

#### G-08: Missing Cross-Domain Integration Flows

| Flow                                            | Priority | Status     |
| ----------------------------------------------- | -------- | ---------- |
| Calendar exception → scheduling reschedule      | High     | ✅ Exists  |
| Resource deletion → assignment cleanup          | High     | ✅ Exists  |
| Notification delivery after comment mention     | Medium   | ✅ Exists  |
| Project soft delete → all children soft deleted | High     | ✅ Exists  |
| Member removal → access revoked immediately     | Medium   | ✅ Exists  |
| AI chat → context includes latest tasks         | Low      | ⚠️ Partial |
| Bulk task create → summary rollup cascade       | High     | ✅ Exists  |
| Invitation accept → org membership auto-added   | Medium   | ✅ Exists  |

---

#### G-09: Frontend Missing Feature Tests

| Feature   | What to Test                                        | Priority |
| --------- | --------------------------------------------------- | -------- |
| Calendar  | CalendarPage list/create/default flow render/assertions | Medium   |
| Reports   | useReports hook, ReportsPage render                 | Low      |
| Resources | ResourcesPage component, utilization view rendering | Medium   |
| Dashboard | DashboardPage component, metric card rendering      | Low      |

---

### 🟢 Nice-to-Have (V1.1+)

#### G-10: Security-Focused Tests

- [x] SQL injection via task name, project name, org slug
- [x] XSS payload in comment `content` field
- [x] CORS header validation (only allowed origins get `Access-Control-Allow-Origin`)
- [x] CSRF protection with SameSite cookie
- [x] Rate limit enforcement (re-enable limiter in specific test)
  Status: pass-now handler-contract coverage (limiter disabled globally for deterministic tests).
- [x] Excessive request body size (>1MB JSON)
- [x] UUID format validation on path params (random string → 422, not 500)

#### G-11: Concurrency Tests

- [x] Concurrent task creation on same project (tests `lock_project_row`)
- [x] Concurrent scheduling recalculation (should serialize)
- [x] Two users accepting same invitation simultaneously
- [x] Concurrent WBS code regeneration → no duplicate codes

#### G-12: Performance / Stress Tests

- [x] Project with 500 tasks → schedule calculates in <5s
- [x] Project with 100 tasks + 200 dependencies → no timeout
- [x] Resource utilization over 365-day range → acceptable response time
- [x] Bulk create 50 tasks → response time <3s
  Status: implemented as opt-in perf suite (`RUN_PERF_TESTS=1`) to keep default CI stable.

#### G-13: Auth Expansion Test Gap (`FR-AU-003`, `FR-AU-005`, `FR-AU-006`)

**Risk:** Google OAuth, password reset, and profile update are security-critical flows and require a dedicated max-safe matrix before requirement closure.

Required coverage before marking these requirements implemented:

- Backend service tests for OAuth state checks, identity-link rules, and reset token lifecycle.
- Backend API tests for OAuth redirect/callback contract, reset privacy behavior, reset confirm errors, and `/users/me` patch validation.
- Integration/concurrency tests for single-use reset race behavior and provider callback end-to-end flow.
- Security tests for enumeration resistance, open-redirect rejection, rate limits, and oversized payload handling.
- Frontend unit/E2E tests for OAuth start, reset flow UX, and profile update persistence.

Execution checklist source of truth: FILE 16 in `docs/04-testing/test-implementation-plan.md`.

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
3. ✅ Created `tests/unit/service/test_calendar_service.py` — baseline inheritance/exception/FK behavior

### Phase 3: Fill Frontend Gaps (Week 2)

1. Add Gantt tests: `features/gantt/hooks/useGantt.test.ts`
2. Add Calendar tests: `features/calendar/hooks/useCalendar.test.ts`
3. Add Resources component tests

### Phase 4: Cross-Domain Integration Flows (Week 2-3)

1. ✅ `tests/integration/flows/test_calendar_scheduling_flows.py` — calendar exception → reschedule
2. ✅ `tests/integration/flows/test_resource_cleanup_flows.py` — resource delete → assignments
3. ✅ `tests/integration/flows/test_bulk_rollup_flows.py` — bulk create → summary cascade
4. ✅ `tests/integration/flows/test_notification_flows.py` — comment mention → notification delivery

### Phase 5: Security & Concurrency (Week 3-4)

1. ✅ `tests/unit/api/v1/test_security.py` — injection, XSS, CORS, cookie/UUID/size guardrails
2. ✅ `tests/integration/test_concurrency.py` — row locking and race-window checks
3. ✅ `tests/integration/test_performance.py` — opt-in performance suite (`RUN_PERF_TESTS=1`)

### Phase 6: Auth Expansion Max-Safe Set (Week 4-5)

1. Execute FILE 16 in `test-implementation-plan.md` for `FR-AU-003`, `FR-AU-005`, and `FR-AU-006`.
2. Keep requirement traceability status as not implemented/partial until FILE 16 backend coverage passes.
3. Promote to implemented only after API + service + integration + abuse-path tests are green.

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

### Backend Unit Tests (50+ files, ~320+ tests)

**API Layer (22 files):**
`test_activity`, `test_ai`, `test_assignments`, `test_auth`, `test_calendars`, `test_comments`, `test_dependencies`, `test_deps`, `test_email_verification`, `test_insights`, `test_notifications`, `test_organization_members`, `test_organizations`, `test_project_members`, `test_projects`, `test_resources`, `test_scheduling`, `test_security`, `test_task_bulk`, `test_tasks`, `test_utilization`, `test_ws`

**Service Layer (22 files):**
`test_activity_log_service`, `test_ai_service`, `test_assignment_service`, `test_auth_service`, `test_calendar_service`, `test_calendar_utils`, `test_comment_service`, `test_dependency_service`, `test_email_service`, `test_insights_service`, `test_notification_service`, `test_notification_tasks`, `test_project_member_service`, `test_project_service`, `test_realtime_service`, `test_scheduling_service`, `test_service_layer_architecture`, `test_task_hierarchy_service`, `test_task_rollup_service`, `test_utilization_service`, `test_ws_protocol`, `test_ws_session_service`

**Other (8 files):**
`test_db_connection`, `test_health`, `test_user_notification_websocket_manager`, `test_websocket_manager`, `test_repository_layer`, `test_comment_entity_type_migration`, `test_comment_thread_integrity_migration`, `test_seed_industry_portfolio`

### Backend Integration Tests (15 files, 50+ tests)

`test_auth_flows` (3), `test_task_flows` (6), `test_scheduling_flows` (6), `test_project_flows` (2), `test_org_flows` (2), `test_dependency_flows` (1), `test_assignment_flows` (2), `test_task_service` (3), `test_calendar_scheduling_flows` (3), `test_resource_cleanup_flows` (3), `test_notification_flows` (5), `test_bulk_rollup_flows` (3), `test_concurrency` (4), `test_performance` (4, opt-in)

### Frontend Unit Tests (41 files)

See Section 2 table above.

### Frontend E2E Tests (8 specs)

`auth`, `org-flow`, `org-members`, `project-flow`, `task-flow`, `ai-panel`, `nav-layout`, `error-states`

---

_Source of truth: codebase audit updated 2026-03-11 against all `tests/` directories._
