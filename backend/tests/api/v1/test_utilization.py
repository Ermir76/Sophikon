import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_resource_utilization_success(client: AsyncClient):
    """Utilization — single resource — returns daily allocations (200)."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "util_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Util Owner",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Util", "slug": "org-util"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Util",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create resource (max_units=1.0 = 100%)
    res_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Dev 1", "max_units": 1.0},
    )
    res_id = res_resp.json()["id"]

    # Create task
    task_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-03-01", "duration": 2400},
    )
    task_id = task_resp.json()["id"]

    # Assign resource to task
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": res_id,
            "units": 0.5,
            "start_date": "2024-03-01",
            "finish_date": "2024-03-05",
        },
    )

    # Get utilization
    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/{res_id}",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resource_id"] == res_id
    assert data["resource_name"] == "Dev 1"
    assert len(data["daily_allocations"]) == 5
    # Each day should show 0.5 units allocated
    for day in data["daily_allocations"]:
        assert float(day["allocated_units"]) == 0.5
        assert day["is_over_allocated"] is False


@pytest.mark.asyncio
async def test_resource_utilization_not_found(client: AsyncClient):
    """Utilization — non-existent resource — 404."""
    import uuid

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "util_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Util NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Util NF", "slug": "org-util-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Util NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/{rand_id}",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_project_utilization_summary(client: AsyncClient):
    """Project utilization — returns all resources (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "putil_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "PUtil Owner",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org PUtil", "slug": "org-putil"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj PUtil",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create 2 resources
    await client.post(f"/api/v1/projects/{proj_id}/resources", json={"name": "Dev A"})
    await client.post(f"/api/v1/projects/{proj_id}/resources", json={"name": "Dev B"})

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["resources"]) == 2


@pytest.mark.asyncio
async def test_over_allocation_detection(client: AsyncClient):
    """Over-allocation — detects when total units > max_units (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "oalloc_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "OAlloc Owner",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org OAlloc", "slug": "org-oalloc"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj OAlloc",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create resource (max_units=1.0 = 100%)
    res_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Dev Over", "max_units": 1.0},
    )
    res_id = res_resp.json()["id"]

    # Create 2 tasks with overlapping dates
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task A", "start_date": "2024-03-01", "duration": 2400},
    )
    t1_id = t1.json()["id"]

    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task B", "start_date": "2024-03-01", "duration": 2400},
    )
    t2_id = t2.json()["id"]

    # Assign same resource to both at 75% (total = 150% > 100%)
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t1_id}/assignments",
        json={
            "resource_id": res_id,
            "units": 0.75,
            "start_date": "2024-03-01",
            "finish_date": "2024-03-05",
        },
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t2_id}/assignments",
        json={
            "resource_id": res_id,
            "units": 0.75,
            "start_date": "2024-03-01",
            "finish_date": "2024-03-05",
        },
    )

    # Detect over-allocations
    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/over-allocations",
        params={"start_date": "2024-03-01", "end_date": "2024-03-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] > 0
    # Every day should be over-allocated (0.75 + 0.75 = 1.5 > 1.0)
    for item in data["items"]:
        assert item["resource_name"] == "Dev Over"
        assert float(item["allocated_units"]) == 1.5
        assert float(item["exceeds_by"]) == 0.5


@pytest.mark.asyncio
async def test_no_over_allocation(client: AsyncClient):
    """Over-allocation — no over-allocation when within limits (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "no_oalloc@x.com",
            "password": "StrongPassword123!",
            "full_name": "No OAlloc",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org No OAlloc", "slug": "org-no-oalloc"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj No OAlloc",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Resource with 100% capacity
    res_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Dev Fine", "max_units": 1.0},
    )
    res_id = res_resp.json()["id"]

    # One task at 50%
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task OK", "start_date": "2024-03-01", "duration": 2400},
    )
    t1_id = t1.json()["id"]

    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t1_id}/assignments",
        json={
            "resource_id": res_id,
            "units": 0.5,
            "start_date": "2024-03-01",
            "finish_date": "2024-03-03",
        },
    )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/utilization/over-allocations",
        params={"start_date": "2024-03-01", "end_date": "2024-03-03"},
    )
    assert resp.status_code == 200
    assert resp.json()["total_count"] == 0
