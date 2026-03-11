# Test Quality Audit — Violations & Fixes

> Every violation of the Testing Constitution, with location, rule broken, and fix.
>
> **Do this BEFORE writing any new test code.**
>
> Audited: 2026-03-10

---

## Priority Legend

- 🔴 **Must fix** — assertion is meaningless (Rule 1, 3)
- 🟡 **Should fix** — noisy but assertions are OK (Rule 4, 5, 9)
- 🟢 **Minor** — cosmetic or low-impact (Rule 7, 9)

---

## File 1: `tests/unit/api/v1/test_scheduling.py`

**Severity: 🔴 Worst file — almost every assertion is vague**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 79 | `assert data["tasks_updated"] >= 3` | R3 | `assert data["tasks_updated"] == 3` |
| 80 | `assert data["project_finish_date"] is not None` | R3 | `assert data["project_finish_date"] == "2024-01-03"` |
| 112 | `assert data["tasks_updated"] == 0` | ✅ | OK |
| 113 | `assert data["critical_path_task_ids"] == []` | ✅ | OK |
| 147 | `assert data["tasks_updated"] >= 1` | R3 | `assert data["tasks_updated"] == 1` |
| 235 | `assert len(data["critical_path"]) >= 2` | R3 | `assert len(data["critical_path"]) == 2` |
| 86-108 | Inline setup (test 2) — doesn't use `_setup_project` helper | R4 | Use `_setup_project` |
| 117-148 | Inline setup (test 3) — doesn't use `_setup_project` helper | R4 | Use `_setup_project` |
| 150-192 | Inline setup (test 4) — doesn't use `_setup_project` helper | R4 | Use `_setup_project` |
| 198-245 | Inline setup (test 5) — doesn't use `_setup_project` helper | R4 | Use `_setup_project` |
| 41 | `duration=480` no comment | R9 | Add `# 1 working day (8h × 60min)` |

**Action:** Rewrite all 5 tests. Use `_setup_project` for all, assert exact values.

---

## File 2: `tests/unit/api/v1/test_utilization.py`

**Severity: 🟡 Good assertions, but setup is repeated 5 times**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 6-36 | 30-line inline setup in test 1 | R4 | Extract `_setup_project_with_resource(client, suffix)` |
| 73-104 | 30-line inline setup in test 2 | R4 | Use shared helper |
| 108-143 | 30-line inline setup in test 3 | R4 | Use shared helper |
| 146-175 | 30-line inline setup in test 4 | R4 | Use shared helper |
| 226-256 | 30-line inline setup in test 5 | R4 | Use shared helper |
| 104 | `assert resp.status_code == 404` (no error code check) | R5 | Add `assert resp.json()["error"]["code"] == "NOT_FOUND"` |

**Action:** Extract one `_setup(client, suffix) -> (proj_id,)` helper and one `_setup_with_resource(client, suffix) -> (proj_id, res_id)` helper. Keep all existing assertions (they are good — exact float values).

---

## File 3: `tests/integration/flows/test_scheduling_flows.py`

**Severity: 🔴 Vague assertions on critical business logic**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 118 | `assert calc_data["tasks_updated"] >= 3` | R3 | `== 3` |
| 119 | `assert len(calc_data["critical_path_task_ids"]) >= 2` | R3 | `== 3` (A, B, C are all critical in a single chain) |
| 127 | `assert b_data["start_date"] >= a_data["finish_date"]` | R3 | `assert b_data["start_date"] == "2024-01-02"` |
| 129 | `assert c_data["start_date"] >= b_data["finish_date"]` | R3 | `assert c_data["start_date"] == "2024-01-03"` |
| 135 | `assert len(cp_data["critical_path"]) >= 2` | R3 | `== 3` |
| 203 | `assert b_after["start_date"] >= b_before["start_date"]` | R3 | Should assert the exact new start date after reschedule |
| 292 | `assert c_data["total_slack"] >= 0` | R3 | `> 0` (C must have positive slack — `>= 0` is always true for all tasks) |

**Action:** Tighten all assertions to exact values. The scheduling engine is deterministic given a project start date and calendar, so exact dates can be computed.

---

## File 4: `tests/unit/api/v1/test_insights.py`

**Severity: 🔴 Almost useless — tests structure, not values**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 74 | `assert "kpis" in data` | R1 | Assert actual KPI values: `assert data["kpis"]["active_projects"] == 1` |
| 75 | `assert "project_health" in data` | R1 | Assert health breakdown values |
| 76 | `assert "trend" in data` | R1 | Assert trend has expected data points |
| 77 | `assert "recent_activity" in data` | R1 | Assert activity count matches setup |
| 78 | `assert data["kpis"]["active_projects"] >= 0` | R3 | `== 1` (we created exactly 1 project) |
| 91 | `assert org_resp.status_code == 422` | R5 | Add error code assertion |

**Action:** Rewrite test_dashboard_insights_success to assert actual values. The setup creates 1 project with 1 overdue task and 1 over-allocated resource — assert those exact KPIs.

---

## File 5: `tests/integration/flows/test_auth_flows.py`

**Severity: 🟢 Minor — one vague assertion**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 35 | `assert len(items) >= 1` | R3 | `== 1` (just registered → exactly 1 personal org) |

---

## File 6: `tests/unit/service/test_ai_service.py`

**Severity: 🟢 Minor**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 175 | `assert len(conversations) >= 1` | R3 | `== 1` (we created exactly 1 conversation) |

---

## File 7: `tests/unit/migrations/test_seed_industry_portfolio.py`

**Severity: 🟢 Minor — seed script creates variable counts**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 44 | `assert len(orgs) >= 1` | R3 | Acceptable — seed produces variable data. Add comment: `# seed creates N industry orgs` |
| 94 | `assert len(orgs) >= 1` | R3 | Same — add comment |

---

## File 8: `tests/unit/api/v1/test_organizations.py`

**Severity: 🟢 Minor**

| Line | Current Code | Rule | Fix |
|------|-------------|------|-----|
| 93 | `assert data1["total"] >= 6  # 5 created + 1 personal` | R3 | `== 6` (the comment already explains the count!) |
| 138 | `assert data["id"] is not None` | R3 | Use `isinstance(data["id"], str) and len(data["id"]) == 36` or just remove (if ID exists, the 201 status proves creation) |

---

## File 9: Various files — status-code-only error assertions

**Severity: 🟡 — these know the endpoint rejected the request but don't prove WHY**

Priority subset (most impactful — write endpoints that could have multiple failure reasons):

| File | Line | Current | Fix |
|------|------|---------|-----|
| `test_tasks.py` | 335 | `assert resp.status_code == 400` | Add `assert resp.json()["error"]["code"] == "NOT_FOUND"` (invalid parent task) |
| `test_tasks.py` | 1225 | `assert resp.status_code == 400` | Add error code (indent first task) |
| `test_tasks.py` | 1376 | `assert resp.status_code == 400` | Add error code (outdent root task) |
| `test_tasks.py` | 1652 | `assert resp.status_code == 400` | Add error code (reorder both after+before) |
| `test_project_members.py` | 202 | `assert demote_last_owner.status_code == 400` | Add error code (last owner protection) |
| `test_project_members.py` | 440 | `assert invalid_response.status_code == 400` | Add error code (invalid token) |

**Note:** Status-code-only on 403 (forbidden) and 404 (not found) is *acceptable* because there's almost always only one reason for those. Status-code-only on 400 is *not acceptable* because 400 could mean many different things.

---

## Summary — Execution Order

| Step | File(s) | Violations | Effort | Impact |
|------|---------|-----------|--------|--------|
| **1** | `test_scheduling.py` | 🔴 5 vague assertions + 4 inline setups | ~30 min | High — core business logic |
| **2** | `test_scheduling_flows.py` | 🔴 7 vague assertions | ~20 min | High — integration correctness |
| **3** | `test_insights.py` | 🔴 5 structural-only checks | ~15 min | Medium — proves nothing currently |
| **4** | `test_utilization.py` | 🟡 5 repeated setups + 1 missing error code | ~20 min | Medium — readability |
| **5** | `test_tasks.py` (6 spots) | 🟡 6 missing error codes on 400s | ~10 min | Low — minor |
| **6** | `test_project_members.py` (3 spots) | 🟡 3 missing error codes on 400s | ~5 min | Low — minor |
| **7** | `test_auth_flows.py`, `test_ai_service.py`, `test_organizations.py` | 🟢 3 vague `>= N` assertions | ~5 min | Low — cosmetic |

**Total effort: ~2 hours to fix all violations.**

Do steps 1-3 first (the 🔴 items). Those are the ones where the test suite currently gives false confidence.
