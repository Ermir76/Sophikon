"""
API tests for resource utilization endpoints.

GET    /projects/{project_id}/utilization/{resource_id}      - Resource utilization
GET    /projects/{project_id}/utilization                     - Project utilization summary
GET    /projects/{project_id}/utilization/over-allocations    - Over-allocation detection
"""

import uuid

import pytest
from httpx import AsyncClient

# ── Helpers ──


async def _setup(client: AsyncClient, suffix: str) -> str:
    """Register, create org + project. Returns project_id."""
    slug_suffix = suffix.lower().replace("_", "-")

    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"util_{slug_suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Util {suffix}",
        },
    )
    assert register_resp.status_code == 201, register_resp.text

    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org Util {suffix}", "slug": f"org-util-{slug_suffix}"},
    )
    assert org_resp.status_code == 201, org_resp.text
    org_id = org_resp.json()["id"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Proj Util {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert proj_resp.status_code == 201, proj_resp.text
    return proj_resp.json()["id"]


async def _setup_with_resource(
    client: AsyncClient, suffix: str, max_units: float = 1.0
) -> tuple[str, str]:
    """Register, create org + project + resource. Returns (project_id, resource_id)."""
    proj_id = await _setup(client, suffix)
    res_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": f"Dev {suffix}", "max_units": max_units},
    )
    assert res_resp.status_code == 201, res_resp.text
    return proj_id, res_resp.json()["id"]


async def _create_task_and_assign(
    client: AsyncClient,
    proj_id: str,
    res_id: str,
    task_name: str,
    units: float,
    start: str = "2024-03-01",
    finish: str = "2024-03-05",
    duration: int = 2400,  # 5 working days
) -> str:
    """Create a task and assign a resource to it. Returns task_id."""
    task_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": task_name, "start_date": start, "duration": duration},
    )
    assert task_resp.status_code == 201, task_resp.text
    task_id = task_resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": res_id,
            "units": units,
            "start_date": start,
            "finish_date": finish,
        },
    )
    return task_id


# ── GET /utilization/{resource_id} ──


@pytest.mark.asyncio
async def test_resource_utilization_success(client: AsyncClient):
    """Utilization — single resource at 50% → daily allocations show 0.5 units, not over-allocated."""
    proj_id, res_id = await _setup_with_resource(client, "success")

    await _create_task_and_assign(
        client,
        proj_id,
        res_id,
        "Task 1",
        units=0.5,
    )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/{res_id}",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resource_id"] == res_id
    assert data["resource_name"] == "Dev success"
    assert len(data["daily_allocations"]) == 5
    # Each day should show exactly 0.5 units allocated
    for day in data["daily_allocations"]:
        assert float(day["allocated_units"]) == 0.5
        assert day["is_over_allocated"] is False


@pytest.mark.asyncio
async def test_resource_utilization_not_found(client: AsyncClient):
    """Utilization — non-existent resource → 404 with NOT_FOUND error code."""
    proj_id = await _setup(client, "nf")

    rand_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/{rand_id}",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


# ── GET /utilization (project summary) ──


@pytest.mark.asyncio
async def test_project_utilization_summary(client: AsyncClient):
    """Project utilization — returns all 2 resources (200)."""
    proj_id = await _setup(client, "summary")

    # Create 2 resources
    await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Dev A"},
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Dev B"},
    )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["resources"]) == 2


# ── GET /utilization/over-allocations ──


@pytest.mark.asyncio
async def test_over_allocation_detection(client: AsyncClient):
    """Over-allocation — 2 tasks × 75% on same resource (total 150% > 100%) → detected."""
    proj_id, res_id = await _setup_with_resource(client, "oalloc")

    # Assign same resource to 2 overlapping tasks at 75% each (total = 150% > 100%)
    await _create_task_and_assign(
        client,
        proj_id,
        res_id,
        "Task A",
        units=0.75,
    )
    await _create_task_and_assign(
        client,
        proj_id,
        res_id,
        "Task B",
        units=0.75,
    )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/over-allocations",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] > 0
    # Every day should be over-allocated (0.75 + 0.75 = 1.5 > 1.0)
    for item in data["items"]:
        assert item["resource_name"] == "Dev oalloc"
        assert float(item["allocated_units"]) == 1.5
        assert float(item["exceeds_by"]) == 0.5


@pytest.mark.asyncio
async def test_no_over_allocation(client: AsyncClient):
    """Over-allocation — 1 task at 50% on resource (max 100%) → 0 over-allocations."""
    proj_id, res_id = await _setup_with_resource(client, "no_oalloc")

    await _create_task_and_assign(
        client,
        proj_id,
        res_id,
        "Task OK",
        units=0.5,
        start="2024-03-01",
        finish="2024-03-03",
    )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/over-allocations",
        params={"start_date": "2024-03-01", "end_date": "2024-03-03"},
    )
    assert resp.status_code == 200
    assert resp.json()["total_count"] == 0
