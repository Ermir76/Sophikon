"""
Integration flow tests for resource cleanup and assignment integrity.
"""

import pytest
from httpx import AsyncClient


async def _setup_project(client: AsyncClient, suffix: str) -> str:
    """Register user, create org/project, return project_id."""
    slug_suffix = suffix.lower().replace("_", "-")

    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"resource_flow_{slug_suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Resource Flow {suffix}",
        },
    )
    assert register_resp.status_code == 201, register_resp.text

    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org Resource {suffix}", "slug": f"org-resource-{slug_suffix}"},
    )
    assert org_resp.status_code == 201, org_resp.text
    org_id = org_resp.json()["id"]

    project_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Project Resource {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_resp.status_code == 201, project_resp.text
    return project_resp.json()["id"]


async def _create_resource(
    client: AsyncClient,
    project_id: str,
    *,
    name: str,
    max_units: float = 1.0,
) -> str:
    resp = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={
            "name": name,
            "max_units": max_units,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_task(
    client: AsyncClient,
    project_id: str,
    *,
    name: str,
    start_date: str = "2024-03-01",
    duration: int = 480,  # 1 working day (8h * 60min)
) -> str:
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": name,
            "start_date": start_date,
            "duration": duration,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_assignment(
    client: AsyncClient,
    project_id: str,
    task_id: str,
    resource_id: str,
    *,
    units: float = 1.0,
    start_date: str = "2024-03-01",
    finish_date: str = "2024-03-01",
) -> str:
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": units,
            "start_date": start_date,
            "finish_date": finish_date,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_delete_resource_removes_all_assignments(client: AsyncClient):
    """
    Deleting a resource removes its assignments (FK cascade) for all tasks.
    """
    project_id = await _setup_project(client, "delete_cascade")
    resource_id = await _create_resource(client, project_id, name="Cascade Resource")
    task_id = await _create_task(client, project_id, name="Cascade Task")
    await _create_assignment(client, project_id, task_id, resource_id)

    before = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments"
    )
    assert before.status_code == 200
    assert len(before.json()) == 1

    delete_resp = await client.delete(
        f"/api/v1/projects/{project_id}/resources/{resource_id}"
    )
    assert delete_resp.status_code == 204

    after = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments"
    )
    assert after.status_code == 200
    assert after.json() == []

    missing_resource = await client.get(
        f"/api/v1/projects/{project_id}/resources/{resource_id}"
    )
    assert missing_resource.status_code == 404


@pytest.mark.asyncio
async def test_delete_resource_with_utilization_data_succeeds(client: AsyncClient):
    """
    Resource deletion succeeds even when utilization endpoints report active usage.
    """
    project_id = await _setup_project(client, "delete_utilization")
    resource_id = await _create_resource(client, project_id, name="Utilized Resource")
    task_id = await _create_task(client, project_id, name="Utilized Task")
    await _create_assignment(
        client,
        project_id,
        task_id,
        resource_id,
        units=0.75,
        start_date="2024-03-01",
        finish_date="2024-03-03",
    )

    util_before = await client.get(
        f"/api/v1/projects/{project_id}/utilization/{resource_id}",
        params={"start_date": "2024-03-01", "end_date": "2024-03-03"},
    )
    assert util_before.status_code == 200
    assert float(util_before.json()["peak_units"]) == 0.75

    delete_resp = await client.delete(
        f"/api/v1/projects/{project_id}/resources/{resource_id}"
    )
    assert delete_resp.status_code == 204

    summary_after = await client.get(
        f"/api/v1/projects/{project_id}/utilization",
        params={"start_date": "2024-03-01", "end_date": "2024-03-03"},
    )
    assert summary_after.status_code == 200
    assert summary_after.json()["resources"] == []

    over_alloc_after = await client.get(
        f"/api/v1/projects/{project_id}/utilization/over-allocations",
        params={"start_date": "2024-03-01", "end_date": "2024-03-03"},
    )
    assert over_alloc_after.status_code == 200
    assert over_alloc_after.json()["total_count"] == 0


@pytest.mark.asyncio
async def test_deactivate_resource_blocks_new_assignments(client: AsyncClient):
    """
    Deactivated resource cannot be used for creating new assignments.
    """
    project_id = await _setup_project(client, "deactivate_blocks")
    resource_id = await _create_resource(client, project_id, name="Inactive Resource")
    task_id = await _create_task(client, project_id, name="Task For Inactive Resource")

    deactivate_resp = await client.patch(
        f"/api/v1/projects/{project_id}/resources/{resource_id}",
        json={"is_active": False},
    )
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.json()["is_active"] is False

    assign_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 0.5,
            "start_date": "2024-03-01",
            "finish_date": "2024-03-01",
        },
    )
    assert assign_resp.status_code == 400
    assert assign_resp.json()["error"]["code"] == "INVALID_OPERATION"

    list_default = await client.get(f"/api/v1/projects/{project_id}/resources")
    assert list_default.status_code == 200
    assert list_default.json()["items"] == []

    list_including_inactive = await client.get(
        f"/api/v1/projects/{project_id}/resources",
        params={"include_inactive": True},
    )
    assert list_including_inactive.status_code == 200
    assert len(list_including_inactive.json()["items"]) == 1
