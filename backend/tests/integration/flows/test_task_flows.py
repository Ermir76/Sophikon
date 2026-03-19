from datetime import date

import pytest
from httpx import AsyncClient

from app.service.calendar_utils import DEFAULT_WORK_WEEK, working_minutes_between


@pytest.mark.asyncio
async def test_wbs_inheritance(client: AsyncClient):
    """
    Integration: Create parent -> create child -> WBS code inherits parent prefix.
    """
    # 1. Register & Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wbs_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "WBS User",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org WBS", "slug": "org-wbs"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj WBS",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # 2. Create Parent Task
    p_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
    )
    parent_id = p_resp.json()["id"]
    parent_wbs = p_resp.json()["wbs_code"]  # e.g., "1"

    # 3. Create Child Task
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Child",
            "start_date": "2024-01-01",
            "duration": 480,
            "parent_task_id": parent_id,
        },
    )
    child_data = c_resp.json()

    # 4. Verify WBS
    # Should be "1.1" or similar
    assert child_data["wbs_code"].startswith(parent_wbs + ".")


@pytest.mark.asyncio
async def test_delete_parent_cascade(client: AsyncClient):
    """
    Integration: Delete parent task -> children also soft-deleted.
    """
    # 1. Setup (reusing user from previous test is risky due to state)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "task_del_cascade@example.com",
            "password": "StrongPassword123!",
            "full_name": "Task Cascade",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Task Cascade", "slug": "org-task-cascade"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Task Cascade",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # 2. Create Parent & Child
    p_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
    )
    parent_id = p_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Child",
            "start_date": "2024-01-01",
            "duration": 480,
            "parent_task_id": parent_id,
        },
    )
    child_id = c_resp.json()["id"]

    # 3. Delete Parent
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{parent_id}")

    # 4. Verify Child is 404
    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{child_id}")
    assert resp.status_code == 404


# --- Additional Integration Flows ---


@pytest.mark.asyncio
async def test_hierarchy_flow_indent_outdent(client: AsyncClient):
    """Integration: Indent and Outdent flow, verifying WBS codes."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "hier_flow@x.com",
            "password": "StrongPassword123!",
            "full_name": "Hier Flow",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Hier", "slug": "org-hier"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Hier",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t3_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T3", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    # Indent T2 under T1
    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/indent")
    assert resp.status_code == 200

    # Fetch all to verify WBS
    tasks = (await client.get(f"/api/v1/projects/{proj_id}/tasks")).json()["items"]
    wbs_map = {t["id"]: t["wbs_code"] for t in tasks}
    assert wbs_map[t1_id] == "1"
    assert wbs_map[t2_id] == "1.1"
    assert wbs_map[t3_id] == "2"

    # Outdent T2 back to root
    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/outdent")
    assert resp.status_code == 200

    tasks2 = (await client.get(f"/api/v1/projects/{proj_id}/tasks")).json()["items"]
    wbs_map2 = {t["id"]: t["wbs_code"] for t in tasks2}

    # T2 outdented from T1 — placed right after T1, T3 shifts
    assert wbs_map2[t1_id] == "1"
    assert wbs_map2[t2_id] == "2"
    assert wbs_map2[t3_id] == "3"


@pytest.mark.asyncio
async def test_summary_rollup_flow(client: AsyncClient):
    """Integration: Parent metrics roll up and deleting children resets parent summary flag."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "roll_flow@x.com",
            "password": "StrongPassword123!",
            "full_name": "Roll Flow",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Roll", "slug": "org-roll"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Roll",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    p_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    c1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={
                "name": "C1",
                "start_date": "2024-01-05",
                "duration": 480,
                "parent_task_id": p_id,
                "constraint_type": "SNET",
                "constraint_date": "2024-01-05",
            },
        )
    ).json()["id"]
    c2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={
                "name": "C2",
                "start_date": "2024-01-10",
                "duration": 480,
                "parent_task_id": p_id,
                "constraint_type": "SNET",
                "constraint_date": "2024-01-10",
            },
        )
    ).json()["id"]

    parent_check = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{p_id}")).json()
    assert parent_check["is_summary"] is True
    # The parent takes the min start date of its children
    assert parent_check["start_date"] == "2024-01-05"
    # Scheduling normalizes 480 minutes to a one-day task (same-day finish).
    # Parent rollup finish is the max child finish date after schedule calc.
    assert parent_check["finish_date"] == "2024-01-10"
    assert parent_check["duration"] == working_minutes_between(
        date(2024, 1, 5),
        date(2024, 1, 10),
        DEFAULT_WORK_WEEK,
        [],
    )

    await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{c1_id}",
        json={"percent_complete": 100},
    )
    await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{c2_id}",
        json={"percent_complete": 0},
    )

    parent_progress = (
        await client.get(f"/api/v1/projects/{proj_id}/tasks/{p_id}")
    ).json()
    assert parent_progress["percent_complete"] == "50.00"
    assert parent_progress["actual_duration"] == 480
    assert parent_progress["remaining_duration"] == 480

    # Delete children to test cascade summary reset
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{c1_id}")
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{c2_id}")

    # We flush & commit in soft_delete_task recursive deletes, check if summary status reverts
    parent_check2 = (
        await client.get(f"/api/v1/projects/{proj_id}/tasks/{p_id}")
    ).json()
    assert parent_check2["is_summary"] is False
    assert parent_check2["work"] == 0
    assert parent_check2["percent_complete"] == "0.00"
    assert parent_check2["actual_duration"] == 0
    assert parent_check2["remaining_duration"] == 0


@pytest.mark.asyncio
async def test_summary_rollup_updates_ancestors_on_child_update(client: AsyncClient):
    """Integration: Child updates refresh parent and grandparent rollups."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "roll_ancestor@x.com",
            "password": "StrongPassword123!",
            "full_name": "Roll Ancestor",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Org Roll Ancestor", "slug": "org-roll-ancestor"},
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Roll Ancestor",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    grandparent_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Grandparent", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    parent_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={
                "name": "Parent",
                "start_date": "2024-01-02",
                "duration": 480,
                "parent_task_id": grandparent_id,
            },
        )
    ).json()["id"]
    child_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={
                "name": "Child",
                "start_date": "2024-01-03",
                "duration": 480,
                "parent_task_id": parent_id,
                "constraint_type": "SNET",
                "constraint_date": "2024-01-03",
            },
        )
    ).json()["id"]

    await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{child_id}",
        json={"start_date": "2024-01-08", "constraint_date": "2024-01-08"},
    )

    parent = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{parent_id}")).json()
    grandparent = (
        await client.get(f"/api/v1/projects/{proj_id}/tasks/{grandparent_id}")
    ).json()

    assert parent["start_date"] == "2024-01-08"
    assert grandparent["start_date"] == "2024-01-08"


@pytest.mark.asyncio
async def test_reorder_flow(client: AsyncClient):
    """Integration: Reorder tasks and verify order sequence arrays."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reoflow@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Flow",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Reo F", "slug": "org-reof"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo F",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t3_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T3", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t3_id}/reorder",
        json={"after_task_id": t1_id},
    )
    assert resp.status_code == 200

    tasks = (await client.get(f"/api/v1/projects/{proj_id}/tasks")).json()["items"]
    order_map = {t["id"]: t["order_index"] for t in tasks}

    assert order_map[t1_id] == 1
    assert order_map[t3_id] == 2
    assert order_map[t2_id] == 3


@pytest.mark.asyncio
async def test_status_transition_flow(client: AsyncClient):
    """Integration: Create task (BACKLOG) → PATCH to TODO → PATCH to DONE → each transition persists."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "stat_flow@x.com",
            "password": "StrongPassword123!",
            "full_name": "Stat Flow",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Org Stat Flow", "slug": "org-stat-flow"},
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Stat Flow",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    # Create — defaults to BACKLOG
    task = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Status Task", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()
    task_id = task["id"]
    assert task["status"] == "BACKLOG"

    # Transition to TODO
    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"status": "TODO"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "TODO"

    # Verify persisted via GET
    fetched = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")).json()
    assert fetched["status"] == "TODO"

    # Transition to DONE
    resp2 = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"status": "DONE"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "DONE"

    # Verify persisted via list
    items = (await client.get(f"/api/v1/projects/{proj_id}/tasks")).json()["items"]
    task_in_list = next(t for t in items if t["id"] == task_id)
    assert task_in_list["status"] == "DONE"
