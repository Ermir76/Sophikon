import pytest
from httpx import AsyncClient


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
