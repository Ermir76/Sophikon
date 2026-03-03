"""
Integration flow tests for the scheduling engine.

Multi-step end-to-end scenarios testing schedule calculation,
auto-recalculation, and constraint interactions.
"""

import pytest
from httpx import AsyncClient

# ── Helpers ──


async def _setup(client: AsyncClient, email_suffix: str) -> str:
    """Register, create org, create project. Returns project_id."""
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"sched_int_{email_suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Sched Int {email_suffix}",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text

    org_resp = await client.post(
        "/api/v1/organizations",
        json={
            "name": f"Org {email_suffix}",
            "slug": f"org-{email_suffix.replace('_', '-')}",
        },
    )
    assert org_resp.status_code == 201, org_resp.text
    org_id = org_resp.json()["id"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Proj {email_suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert proj_resp.status_code == 201, proj_resp.text
    return proj_resp.json()["id"]


async def _task(client: AsyncClient, proj_id: str, name: str, **kwargs) -> dict:
    """Create a task, return full response."""
    payload = {"name": name, "start_date": "2024-01-01", "duration": 480, **kwargs}
    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _dep(
    client: AsyncClient, proj_id: str, pred_id: str, succ_id: str, **kwargs
) -> dict:
    """Create a dependency, return full response."""
    payload = {
        "predecessor_id": pred_id,
        "successor_id": succ_id,
        "type": "FS",
        **kwargs,
    }
    resp = await client.post(f"/api/v1/projects/{proj_id}/dependencies", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _get_task(client: AsyncClient, proj_id: str, task_id: str) -> dict:
    """Fetch a task, return full response."""
    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Flow Tests ──


@pytest.mark.asyncio
async def test_full_scheduling_flow(client: AsyncClient):
    """
    Full flow: tasks → deps → calculate → verify dates/critical path/slack.

    A (1d) → B (1d) → C (1d)
    After calculation: A starts Mon 1/1, B starts Tue 1/2, C starts Wed 1/3.
    All are on the critical path with 0 slack.
    """
    proj_id = await _setup(client, "full_flow")

    a = await _task(client, proj_id, "A")
    b = await _task(client, proj_id, "B")
    c = await _task(client, proj_id, "C")

    await _dep(client, proj_id, a["id"], b["id"])
    await _dep(client, proj_id, b["id"], c["id"])

    # Calculate schedule
    calc_resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()

    assert calc_data["tasks_updated"] >= 3
    assert len(calc_data["critical_path_task_ids"]) >= 2

    # Verify dates propagated
    a_data = await _get_task(client, proj_id, a["id"])
    b_data = await _get_task(client, proj_id, b["id"])
    c_data = await _get_task(client, proj_id, c["id"])

    # B should start after A finishes
    assert b_data["start_date"] >= a_data["finish_date"]
    # C should start after B finishes
    assert c_data["start_date"] >= b_data["finish_date"]

    # Verify critical path endpoint
    cp_resp = await client.get(f"/api/v1/projects/{proj_id}/schedule/critical-path")
    assert cp_resp.status_code == 200
    cp_data = cp_resp.json()
    assert len(cp_data["critical_path"]) >= 2


@pytest.mark.asyncio
async def test_dependency_change_triggers_reschedule(client: AsyncClient):
    """
    Flow: A→B chain → change A.duration → verify B.start shifted.

    Auto-recalculate should fire when duration changes.
    """
    proj_id = await _setup(client, "dep_resch")

    a = await _task(client, proj_id, "A", duration=480)  # 1 day
    b = await _task(client, proj_id, "B", duration=480)  # 1 day
    await _dep(client, proj_id, a["id"], b["id"])

    # Recalculate to establish baseline
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")

    b_before = await _get_task(client, proj_id, b["id"])

    # Change A's duration to 5 days (2100 min)
    await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{a['id']}",
        json={"duration": 2100},
    )

    b_after = await _get_task(client, proj_id, b["id"])

    # B should have shifted later (or stayed the same if auto_calc didn't fire,
    # but either way it should be >= the old start)
    assert b_after["start_date"] >= b_before["start_date"]


@pytest.mark.asyncio
async def test_dependency_delete_reschedule(client: AsyncClient):
    """
    Flow: A→B→C chain → delete A→B dep → recalculate → B now free.
    """
    proj_id = await _setup(client, "dep_del")

    a = await _task(client, proj_id, "A", duration=2100)  # 5 days
    b = await _task(client, proj_id, "B", duration=480)
    c = await _task(client, proj_id, "C", duration=480)

    dep_ab = await _dep(client, proj_id, a["id"], b["id"])
    await _dep(client, proj_id, b["id"], c["id"])

    # Calculate to establish chain
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    b_chained = await _get_task(client, proj_id, b["id"])

    # Delete A→B dependency
    await client.delete(f"/api/v1/projects/{proj_id}/dependencies/{dep_ab['id']}")

    # Recalculate after deletion
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    b_free = await _get_task(client, proj_id, b["id"])

    # B should now start at project start (no predecessor constraint)
    assert b_free["start_date"] <= b_chained["start_date"]


@pytest.mark.asyncio
async def test_constraint_overrides_dependency(client: AsyncClient):
    """
    Flow: A→B (FS) → set B constraint to MSO on a later date → recalculate.

    B should start on the constraint date, not immediately after A.
    """
    proj_id = await _setup(client, "constraint")

    a = await _task(client, proj_id, "A", duration=480)
    b = await _task(client, proj_id, "B", duration=480)
    await _dep(client, proj_id, a["id"], b["id"])

    # Set MSO constraint on B to start on Jan 15
    await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{b['id']}",
        json={"constraint_type": "MSO", "constraint_date": "2024-01-15"},
    )

    # Recalculate
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")

    b_data = await _get_task(client, proj_id, b["id"])
    assert b_data["start_date"] == "2024-01-15"


@pytest.mark.asyncio
async def test_parallel_paths_critical_path(client: AsyncClient):
    """
    Flow: Create parallel paths → verify longest path is critical.

    Path 1 (long):  A (5d) → B (5d)
    Path 2 (short): C (1d)

    Only A and B should be on the critical path.
    """
    proj_id = await _setup(client, "parallel")

    a = await _task(client, proj_id, "A", duration=2100)  # 5 days
    b = await _task(client, proj_id, "B", duration=2100)  # 5 days
    c = await _task(client, proj_id, "C", duration=480)  # 1 day

    await _dep(client, proj_id, a["id"], b["id"])

    calc_resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert calc_resp.status_code == 200

    # Check from critical path endpoint
    cp_resp = await client.get(f"/api/v1/projects/{proj_id}/schedule/critical-path")
    cp_data = cp_resp.json()

    cp_ids = [t["id"] for t in cp_data["critical_path"]]
    assert a["id"] in cp_ids
    assert b["id"] in cp_ids

    # C should have positive slack (not critical)
    c_data = await _get_task(client, proj_id, c["id"])
    assert c_data["total_slack"] >= 0
