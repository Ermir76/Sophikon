# Testing Constitution

Last updated: 2026-03-10
Owner: Backend + Frontend architecture

## 0) Mission

Prevent regressions and prove correctness. Tests are not a count — they are evidence.
A bad test is worse than no test: it gives false confidence.

This document is the source of truth for test quality governance.

## 1) Current Problem Statement

The test suite has volume but uneven quality:
- Some tests verify behavior precisely (comments, auth, dependencies — good)
- Some tests check only status codes without asserting business outcomes (scheduling — weak)
- Some domains have zero service-level unit tests (scheduling, auth, rollup, hierarchy, calendar)
- Setup is repeated inline instead of using shared helpers (utilization, scheduling — noisy)
- No formal rules for when a test is "good enough"

Because of this, a passing test suite does not guarantee correct business logic.

## 2) Quality Rules (Non-Negotiable)

### Rule 1: Every test must assert a business outcome, not just a status code

```python
# ❌ BAD — proves nothing about correctness
async def test_calculate_schedule(client):
    resp = await client.post(f"/api/v1/projects/{pid}/schedule/calculate")
    assert resp.status_code == 200

# ✅ GOOD — proves the business rule works
async def test_calculate_schedule_fs_chain(client):
    resp = await client.post(f"/api/v1/projects/{pid}/schedule/calculate")
    assert resp.status_code == 200

    a = await _get_task(client, pid, a_id)
    b = await _get_task(client, pid, b_id)
    assert b["start_date"] > a["finish_date"]         # FS: B starts after A finishes
    assert b["total_slack"] == 0                       # Both on critical path
```

### Rule 2: One test = one behavior

Do not test create + list + reply + mention in one function.
Each test name must describe one specific behavior being verified.

```python
# ❌ BAD — too many concerns
async def test_task_create_list_update_delete(client):
    ...

# ✅ GOOD — one behavior per test
async def test_create_task_success(client): ...
async def test_create_task_viewer_forbidden(client): ...
async def test_create_task_invalid_duration(client): ...
```

**Exception:** Integration flow tests deliberately chain steps to verify multi-step business processes. These must have a clear docstring explaining the full scenario.

### Rule 3: Assert specific values, not just "something exists"

```python
# ❌ BAD — proves "something" happened but not "the right thing"
assert data["tasks_updated"] >= 3
assert len(data["critical_path_task_ids"]) >= 2
assert data["project_finish_date"] is not None

# ✅ GOOD — proves the exact expected outcome
assert data["tasks_updated"] == 3
assert set(data["critical_path_task_ids"]) == {a_id, b_id, c_id}
assert data["project_finish_date"] == "2024-01-03"
```

**Exception:** When the exact value depends on non-deterministic factors (e.g. timestamps), use `>=` or `is not None` but add a comment explaining why.

### Rule 4: Setup must be extracted into helpers

Each test file should have private `_setup_*` helpers at the top. If you find yourself writing `client.post("/api/v1/auth/register", ...)` inside more than one test in the same file, extract it.

```python
# ❌ BAD — inline setup repeated in every test
async def test_foo(client):
    await client.post("/api/v1/auth/register", json={...})
    org = await client.post("/api/v1/organizations", json={...})
    proj = await client.post("/api/v1/projects", json={...})
    ...

# ✅ GOOD — shared helper
async def _setup(client, suffix: str) -> str:
    """Register, create org + project. Returns project_id."""
    ...

async def test_foo(client):
    proj_id = await _setup(client, "foo")
    ...
```

### Rule 5: Every error test must assert the error code, not just the status

```python
# ❌ BAD — knows it failed but not why
assert resp.status_code == 400

# ✅ GOOD — proves the correct error path was hit
assert resp.status_code == 400
assert resp.json()["error"]["code"] == "CIRCULAR_DEPENDENCY"
```

### Rule 6: RBAC tests must cover the full role matrix

For every write endpoint, test **at minimum**:
- `owner` → ✅ allowed
- `manager` → ✅ or ❌ depending on business rule
- `member` → ❌ forbidden (for destructive ops) or ✅ (for create ops)
- `viewer` → ❌ always forbidden for writes

Do not skip roles. If a role is allowed, test it. If forbidden, test it.

### Rule 7: Integration flow tests must have a docstring explaining the scenario

```python
# ✅ GOOD
async def test_full_scheduling_flow(client):
    """
    Full flow: tasks → deps → calculate → verify dates/critical path/slack.

    A (1d) → B (1d) → C (1d)
    After calculation: A starts Mon 1/1, B starts Tue 1/2, C starts Wed 1/3.
    All are on the critical path with 0 slack.
    """
```

### Rule 8: Service-level tests must isolate business logic from HTTP

Service tests call the service function directly, not through the API.
They test the logic, not the routing.

```python
# ❌ BAD — "service test" that actually tests via HTTP
async def test_scheduling_service(client):
    resp = await client.post(f"/api/v1/projects/{pid}/schedule/calculate")

# ✅ GOOD — calls the function directly
async def test_forward_pass_fs_chain(session):
    result = await scheduling_service.calculate_schedule(session, project)
    task_a = result.schedule_data[a_id]
    assert task_a.early_start == date(2024, 1, 1)
    assert task_a.early_finish == date(2024, 1, 1)
```

### Rule 9: No magic numbers without context

```python
# ❌ BAD — what is 2100? What is 480?
await _create_task(client, pid, "A", duration=2100)
await _create_task(client, pid, "B", duration=480)

# ✅ GOOD — explain the meaning
await _create_task(client, pid, "A", duration=2100)  # ~5 working days
await _create_task(client, pid, "B", duration=480)   # 1 working day (8h × 60min)
```

### Rule 10: Cleanup must be automatic, never manual

Tests must not depend on execution order. The savepoint-rollback infrastructure handles cleanup after every test. Never write manual cleanup steps.

```python
# ❌ BAD — manual cleanup
async def test_foo(client, session):
    ...
    await session.execute(delete(Task).where(Task.project_id == pid))

# ✅ GOOD — savepoint handles it automatically
async def test_foo(client):
    ...  # no cleanup needed, savepoint rollback handles it
```

## 3) Layer Contract

### What each test layer must prove

| Layer | Tests | Must Assert | Must NOT Assert |
|-------|-------|-------------|-----------------|
| **API unit** | HTTP contract + auth gate | Status code, response shape, error codes, cookie behavior | Internal DB state (use service/integration layer for that) |
| **Service unit** | Business logic correctness | Return values, side effects (DB mutations via direct session), exceptions raised | HTTP status codes, response schemas |
| **Repository unit** | Query correctness | Returned rows, joins, pagination math, filtering | Business rules, HTTP anything |
| **Integration flow** | Multi-step cascading correctness | End-to-end data state after a sequence of operations | Individual function return values (use unit tests for that) |
| **Frontend unit** | Component render + hook behavior | Rendered output, hook state transitions, store mutations | Real API calls (must be mocked) |
| **Frontend E2E** | Full user journey | Visual outcomes, navigation, form submission | Internal state (use unit tests for that) |

### Dependency direction

```
API unit tests → (may use) → helpers that call endpoints
Service unit tests → (call directly) → service functions
Repository tests → (call directly) → repo functions
Integration tests → (may use) → helpers that chain endpoint calls
```

Never: service tests that call endpoints. Never: API tests that import service internals.

## 4) File Organization

```
tests/
├── conftest.py                          # Global fixtures (client, session, mocks)
├── fixtures/                            # Shared helpers (e.g. add_project_member)
├── unit/
│   ├── api/v1/test_{endpoint}.py        # One file per endpoint group
│   ├── service/test_{service}.py        # One file per service module
│   ├── repository/test_{repo}.py        # One file per repo module
│   ├── core/test_{module}.py            # Infrastructure tests
│   ├── schema/test_{schema}.py          # Schema validation
│   └── migrations/test_{migration}.py   # Migration correctness
├── integration/
│   ├── flows/test_{domain}_flows.py     # Multi-step business flows
│   ├── persistence/test_{domain}.py     # DB round-trip correctness
│   └── realtime/                        # WS + notification flows
└── e2e/
    └── ...                              # Full API E2E (future)
```

## 5) Naming Convention

### Files

```
test_{module_name}.py              # Unit tests
test_{domain}_flows.py             # Integration flow tests
test_{domain}_service.py           # Service-level tests
```

### Functions

```
test_{action}_{expected_outcome}                     # Happy path
test_{action}_{error_condition}                      # Error path
test_{action}_forbidden_{role}                       # RBAC test
test_{action}_{edge_case_description}                # Edge case

# Examples:
test_create_task_success
test_create_task_viewer_forbidden
test_create_task_invalid_duration
test_create_task_with_parent
test_indent_first_task_rejected
test_circular_dependency_transitive
test_summary_rollup_all_children_complete
```

### Docstrings

Every test function should have either:
1. A one-line docstring describing the behavior, OR
2. A multi-line docstring for complex integration flows

```python
async def test_create_task_success(client):
    """Create — valid payload → 201 with correct fields."""

async def test_full_scheduling_flow(client):
    """
    Full flow: tasks → deps → calculate → verify dates/critical path/slack.

    A (1d) → B (1d) → C (1d)
    After calculation: A starts Mon 1/1, B starts Tue 1/2, C starts Wed 1/3.
    """
```

## 6) Frontend Test Rules

### Component Tests (Vitest + React Testing Library)

```typescript
// ✅ GOOD — tests what the user sees
it("renders resource table with two rows", () => {
  render(<ResourcesPage />);
  expect(screen.getByText("Dev A")).toBeInTheDocument();
  expect(screen.getByText("Dev B")).toBeInTheDocument();
});

// ❌ BAD — tests implementation details
it("calls setResources with correct data", () => {
  expect(mockSetResources).toHaveBeenCalledWith([...]);
});
```

### Hook Tests

```typescript
// ✅ GOOD — tests the behavior of the hook
it("returns loading state while fetching", () => {
  const { result } = renderHook(() => useTasks(projectId));
  expect(result.current.isLoading).toBe(true);
});
```

### Store Tests

```typescript
// ✅ GOOD — tests state transitions
it("toggles AI panel open and closed", () => {
  const { result } = renderHook(() => useAiPanelStore());
  act(() => result.current.toggle());
  expect(result.current.isOpen).toBe(true);
  act(() => result.current.toggle());
  expect(result.current.isOpen).toBe(false);
});
```

### E2E Tests (Playwright)

```typescript
// ✅ GOOD — tests real user flow with visible outcomes
test("creates a task and sees it in the list", async ({ page }) => {
  await page.fill('[data-testid="task-name-input"]', "Design mockups");
  await page.click('[data-testid="create-task-button"]');
  await expect(page.getByText("Design mockups")).toBeVisible();
});
```

## 7) Review Checklist

Before merging test code, verify:

1. [ ] Each test function asserts a specific **business outcome**, not just a status code
2. [ ] Test name clearly describes the **one behavior** being verified
3. [ ] **Error code** is asserted on error paths, not just the status code
4. [ ] Setup is **extracted** into helpers, not repeated inline
5. [ ] No magic numbers without **inline comments** explaining their meaning
6. [ ] RBAC tests cover all **relevant roles** for the endpoint
7. [ ] Service tests call the service **directly**, not through HTTP
8. [ ] Assertions use **exact values** where deterministic outcomes exist
9. [ ] Integration flow tests have **docstrings** explaining the full scenario
10. [ ] No manual cleanup — savepoint rollback handles it

## 8) AI Assistant Contract

When an assistant writes or modifies tests:
1. Follow this constitution first.
2. Never write tests that only assert status codes.
3. Never bundle unrelated assertions into one test function.
4. Explain which quality rule each test satisfies when asked.
5. When auditing test quality, evaluate against these 10 rules, not just count.

## 9) Known Violations (To Fix)

These existing tests violate the constitution and should be updated:

| File | Violation | Rule Broken |
|------|-----------|-------------|
| `test_scheduling.py` L79 | `assert data["tasks_updated"] >= 3` — vague assertion | Rule 3 |
| `test_scheduling.py` L80 | `assert data["project_finish_date"] is not None` — doesn't verify date | Rule 3 |
| `test_scheduling.py` L119 | Repeats full registration inline instead of using `_setup_project` | Rule 4 |
| `test_scheduling.py` L147 | `assert data["tasks_updated"] >= 1` — should be `== 1` | Rule 3 |
| `test_utilization.py` L6-30 | Full inline setup instead of helper | Rule 4 |
| `test_scheduling_flows.py` L292 | `assert c_data["total_slack"] >= 0` — should be `> 0` specifically | Rule 3 |

## 10) Golden Rule

If a test can pass even when the business logic is wrong, delete it and write a better one.
