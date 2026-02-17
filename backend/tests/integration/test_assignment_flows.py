import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_duplicate_assignment_blocked(client: AsyncClient):
    """
    Integration: Assign resource to task -> duplicate blocked (409).
    """
    # 1. Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup_asn_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Dup Asn User",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Dup Asn", "slug": "org-dup-asn"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Dup Asn",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # 2. Create Task & Resource
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid = t_resp.json()["id"]

    r_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "R1", "type": "WORK"},
    )
    rid = r_resp.json()["id"]

    # 3. Assign First Time
    resp1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp1.status_code == 201

    # 4. Assign Second Time (Duplicate)
    resp2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 0.5,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_cross_project_assignment_blocked(client: AsyncClient):
    """
    Integration: Assign resource from different project -> blocked (400).
    """
    # 1. Setup Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cross_asn_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Cross Asn User",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cross Asn", "slug": "org-cross-asn"},
    )
    org_id = org_resp.json()["id"]

    # 2. Create Proj A & Task A
    pA = await client.post(
        "/api/v1/projects",
        json={"name": "Proj A", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pidA = pA.json()["id"]
    tA = await client.post(
        f"/api/v1/projects/{pidA}/tasks",
        json={"name": "Task A", "start_date": "2024-01-01", "duration": 480},
    )
    tidA = tA.json()["id"]

    # 3. Create Proj B & Resource B
    pB = await client.post(
        "/api/v1/projects",
        json={"name": "Proj B", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pidB = pB.json()["id"]
    rB = await client.post(
        f"/api/v1/projects/{pidB}/resources",
        json={"name": "Res B", "type": "WORK"},
    )
    ridB = rB.json()["id"]

    # 4. Try Assign Resource B to Task A
    # URL is for Proj A context
    resp = await client.post(
        f"/api/v1/projects/{pidA}/tasks/{tidA}/assignments",
        json={
            "resource_id": ridB,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 400
