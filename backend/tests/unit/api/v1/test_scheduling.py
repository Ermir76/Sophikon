"""
API tests for schedule endpoints.

POST   /projects/{project_id}/schedule/calculate       - Recalculate schedule
GET    /projects/{project_id}/schedule/critical-path    - Get critical path
"""

import pytest
from httpx import AsyncClient

# ── Helpers ──


async def _setup_project(client: AsyncClient, suffix: str) -> str:
    """Register, create org, create project. Returns project_id."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"sched_{suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Sched {suffix}",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {suffix}", "slug": f"org-sched-{suffix}"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Proj {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",  # Monday
        },
    )
    return proj_resp.json()["id"]


async def _create_task(client: AsyncClient, proj_id: str, name: str, **kwargs) -> str:
    """Create a task, return its ID."""
    payload = {
        "name": name,
        "start_date": "2024-01-01",
        "duration": 480,  # 1 working day (8h × 60min)
        **kwargs,
    }
    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_dep(
    client: AsyncClient, proj_id: str, pred_id: str, succ_id: str, **kwargs
) -> str:
    """Create a dependency, return its ID."""
    payload = {
        "predecessor_id": pred_id,
        "successor_id": succ_id,
        "type": "FS",
        **kwargs,
    }
    resp = await client.post(f"/api/v1/projects/{proj_id}/dependencies", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _get_task(client: AsyncClient, proj_id: str, task_id: str) -> dict:
    """Fetch a single task by ID."""
    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── POST /schedule/calculate ──


@pytest.mark.asyncio
async def test_calculate_schedule_simple_chain(client: AsyncClient):
    """Calculate — A→B→C (FS): dates propagate in sequence, all 3 tasks updated."""
    proj_id = await _setup_project(client, "chain")
    a_id = await _create_task(client, proj_id, "A")  # 1 working day
    b_id = await _create_task(client, proj_id, "B")  # 1 working day
    c_id = await _create_task(client, proj_id, "C")  # 1 working day

    await _create_dep(client, proj_id, a_id, b_id)
    await _create_dep(client, proj_id, b_id, c_id)

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] == 3
    assert data["project_finish_date"] == "2024-01-03"  # Mon A, Tue B, Wed C

    # Verify dates propagated correctly
    a = await _get_task(client, proj_id, a_id)
    b = await _get_task(client, proj_id, b_id)
    c = await _get_task(client, proj_id, c_id)

    assert a["start_date"] == "2024-01-01"
    assert b["start_date"] == "2024-01-02"  # day after A
    assert c["start_date"] == "2024-01-03"  # day after B

    # All 3 form a single chain → all are on the critical path
    assert set(data["critical_path_task_ids"]) == {a_id, b_id, c_id}


@pytest.mark.asyncio
async def test_calculate_schedule_no_tasks(client: AsyncClient):
    """Calculate — empty project → 0 tasks updated, empty critical path."""
    proj_id = await _setup_project(client, "empty")

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] == 0
    assert data["critical_path_task_ids"] == []


@pytest.mark.asyncio
async def test_calculate_schedule_no_dependencies(client: AsyncClient):
    """Calculate — standalone task with no deps → starts at project start, 1 task updated."""
    proj_id = await _setup_project(client, "nodep")

    task_id = await _create_task(client, proj_id, "Standalone")  # 1 working day

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] == 1

    # Task should keep project start date
    task = await _get_task(client, proj_id, task_id)
    assert task["start_date"] == "2024-01-01"


@pytest.mark.asyncio
async def test_calculate_schedule_critical_path(client: AsyncClient):
    """Calculate — parallel paths: long chain A→B is critical, standalone C is not."""
    proj_id = await _setup_project(client, "cp")

    # Long path: A → B (each ~4.4 working days)
    a_id = await _create_task(client, proj_id, "A", duration=2100)  # ~4.4 working days
    b_id = await _create_task(client, proj_id, "B", duration=2100)  # ~4.4 working days
    # Short path: C (1 working day, no deps)
    c_id = await _create_task(client, proj_id, "C")  # 1 working day

    await _create_dep(client, proj_id, a_id, b_id)

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()

    # A and B should be on critical path, C should not
    assert a_id in data["critical_path_task_ids"]
    assert b_id in data["critical_path_task_ids"]
    assert c_id not in data["critical_path_task_ids"]

    # Verify C has positive slack (it's not critical)
    c = await _get_task(client, proj_id, c_id)
    assert c["total_slack"] > 0


# ── GET /schedule/critical-path ──


@pytest.mark.asyncio
async def test_critical_path_endpoint(client: AsyncClient):
    """Critical path — returns tasks with correct shape and slack values."""
    proj_id = await _setup_project(client, "cpget")

    a_id = await _create_task(client, proj_id, "A")  # 1 working day
    b_id = await _create_task(client, proj_id, "B")  # 1 working day
    await _create_dep(client, proj_id, a_id, b_id)

    # Calculate first
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")

    # Query critical path
    resp = await client.get(f"/api/v1/projects/{proj_id}/schedule/critical-path")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["critical_path"]) == 2

    # Check response shape for every critical task
    for task in data["critical_path"]:
        assert "id" in task
        assert "name" in task
        assert "wbs_code" in task
        assert "start_date" in task
        assert "finish_date" in task
        assert "total_slack" in task
        assert task["total_slack"] == 0  # Critical tasks have zero slack

    # Verify the correct tasks are on the critical path
    cp_ids = {t["id"] for t in data["critical_path"]}
    assert cp_ids == {a_id, b_id}
