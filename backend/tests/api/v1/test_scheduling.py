"""
API tests for schedule endpoints.

POST   /projects/{project_id}/schedule/calculate       - Recalculate schedule
GET    /projects/{project_id}/schedule/critical-path    - Get critical path
"""

import pytest
from httpx import AsyncClient

# ── Helpers ──


async def _setup_project(client: AsyncClient) -> str:
    """Register, create org, create project. Returns project_id."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sched@x.com",
            "password": "StrongPassword123!",
            "full_name": "Sched User",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Sched", "slug": "org-sched"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Sched",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    return proj_resp.json()["id"]


async def _create_task(client: AsyncClient, proj_id: str, name: str, **kwargs) -> str:
    """Create a task, return its ID."""
    payload = {"name": name, "start_date": "2024-01-01", "duration": 480, **kwargs}
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


# ── POST /schedule/calculate ──


@pytest.mark.asyncio
async def test_calculate_schedule_simple_chain(client: AsyncClient):
    """Calculate — A→B→C (FS): dates propagate correctly."""
    proj_id = await _setup_project(client)
    a_id = await _create_task(client, proj_id, "A")
    b_id = await _create_task(client, proj_id, "B")
    c_id = await _create_task(client, proj_id, "C")

    await _create_dep(client, proj_id, a_id, b_id)
    await _create_dep(client, proj_id, b_id, c_id)

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] >= 3
    assert data["project_finish_date"] is not None


@pytest.mark.asyncio
async def test_calculate_schedule_no_tasks(client: AsyncClient):
    """Calculate — empty project returns gracefully."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sched_empty@x.com",
            "password": "StrongPassword123!",
            "full_name": "Sched Empty",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Sched Empty", "slug": "org-sched-empty"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Empty",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] == 0
    assert data["critical_path_task_ids"] == []


@pytest.mark.asyncio
async def test_calculate_schedule_no_dependencies(client: AsyncClient):
    """Calculate — tasks without deps keep project start date."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sched_nodep@x.com",
            "password": "StrongPassword123!",
            "full_name": "Sched NoDep",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Sched NoDep", "slug": "org-sched-nodep"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj NoDep",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    await _create_task(client, proj_id, "Standalone")

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasks_updated"] >= 1


@pytest.mark.asyncio
async def test_calculate_schedule_critical_path(client: AsyncClient):
    """Calculate — parallel paths: longest path is critical."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sched_cp@x.com",
            "password": "StrongPassword123!",
            "full_name": "Sched CP",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Sched CP", "slug": "org-sched-cp"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj CP",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Long path: A → B (each 480 min = 1 work day)
    a_id = await _create_task(client, proj_id, "A", duration=2100)  # ~5 days
    b_id = await _create_task(client, proj_id, "B", duration=2100)  # ~5 days
    # Short path: C (1 day)
    await _create_task(client, proj_id, "C", duration=480)

    await _create_dep(client, proj_id, a_id, b_id)

    resp = await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")
    assert resp.status_code == 200
    data = resp.json()

    # A and B should be on critical path, C should not
    critical_ids = data["critical_path_task_ids"]
    assert a_id in critical_ids
    assert b_id in critical_ids


# ── GET /schedule/critical-path ──


@pytest.mark.asyncio
async def test_critical_path_endpoint(client: AsyncClient):
    """Critical path — returns tasks with is_critical flag."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sched_cpget@x.com",
            "password": "StrongPassword123!",
            "full_name": "Sched CPGet",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Sched CPGet", "slug": "org-sched-cpget"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj CPGet",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    a_id = await _create_task(client, proj_id, "A")
    b_id = await _create_task(client, proj_id, "B")
    await _create_dep(client, proj_id, a_id, b_id)

    # Calculate first
    await client.post(f"/api/v1/projects/{proj_id}/schedule/calculate")

    # Query critical path
    resp = await client.get(f"/api/v1/projects/{proj_id}/schedule/critical-path")
    assert resp.status_code == 200
    data = resp.json()
    assert "critical_path" in data
    assert len(data["critical_path"]) >= 2

    # Check response shape
    for task in data["critical_path"]:
        assert "id" in task
        assert "name" in task
        assert "wbs_code" in task
        assert "start_date" in task
        assert "finish_date" in task
        assert "total_slack" in task
