import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dependency_cascade_delete(client: AsyncClient):
    """
    Integration: Create dependency -> delete predecessor task -> dependency gone (or 404).
    """
    # 1. Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dep_cascade@example.com",
            "password": "StrongPassword123!",
            "full_name": "Dep Cascade",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Dep Cascade", "slug": "org-dep-cascade"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Dep Cascade",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # 2. Create Tasks
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Predecessor", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]

    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Successor", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    # 3. Create Dependency
    dep_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    assert dep_resp.status_code == 201
    dep_id = dep_resp.json()["id"]

    # 4. Delete Predecessor Task
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{tid1}")

    # 5. Verify Dependency is Gone
    # Assuming direct access via GET /api/v1/dependencies/{id} or
    # check via list (list should be empty)

    # Check via list
    list_resp = await client.get(f"/api/v1/projects/{proj_id}/dependencies")
    items = list_resp.json()["items"]
    assert len(items) == 0

    # Optional: Check direct access if endpoint exists (likely does based on other tests)
    # Based on test_dependencies.py (not fully visible but implied CRUD),
    # we can try patch/delete to see if 404.
    patch_resp = await client.patch(
        f"/api/v1/projects/{proj_id}/dependencies/{dep_id}",
        json={"type": "SS"},
    )
    assert patch_resp.status_code == 404
