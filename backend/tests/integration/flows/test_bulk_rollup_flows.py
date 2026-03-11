"""
Integration flow tests for bulk task operations and summary rollups.
"""

import pytest
from httpx import AsyncClient


async def _setup_project(client: AsyncClient, suffix: str) -> str:
    slug = suffix.lower().replace("_", "-")
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"bulk_rollup_{slug}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Bulk Rollup {suffix}",
        },
    )
    assert register_response.status_code == 201, register_response.text

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Bulk Org {suffix}", "slug": f"bulk-org-{slug}"},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Bulk Project {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


async def _create_task(
    client: AsyncClient,
    project_id: str,
    *,
    name: str,
    start_date: str = "2024-01-01",
    duration: int = 480,
    parent_task_id: str | None = None,
) -> str:
    payload = {
        "name": name,
        "start_date": start_date,
        "duration": duration,
        "parent_task_id": parent_task_id,
    }
    response = await client.post(f"/api/v1/projects/{project_id}/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get_task(client: AsyncClient, project_id: str, task_id: str) -> dict:
    response = await client.get(f"/api/v1/projects/{project_id}/tasks/{task_id}")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_bulk_create_under_parent_triggers_summary_rollup(
    client: AsyncClient,
) -> None:
    """Bulk-create children updates parent summary dates/work from child set."""
    project_id = await _setup_project(client, "create-parent-rollup")
    parent_id = await _create_task(client, project_id, name="Parent")

    bulk_create_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/bulk",
        json={
            "tasks": [
                {
                    "name": "Child A",
                    "start_date": "2024-01-08",
                    "duration": 480,  # 1 working day (8h * 60min)
                    "parent_task_id": parent_id,
                },
                {
                    "name": "Child B",
                    "start_date": "2024-01-09",
                    "duration": 480,  # 1 working day (8h * 60min)
                    "parent_task_id": parent_id,
                },
                {
                    "name": "Child C",
                    "start_date": "2024-01-10",
                    "duration": 480,  # 1 working day (8h * 60min)
                    "parent_task_id": parent_id,
                },
            ]
        },
    )
    assert bulk_create_response.status_code == 200, bulk_create_response.text
    payload = bulk_create_response.json()
    assert len(payload["tasks"]) == 3
    assert payload["errors"] == []

    child_rows = [
        await _get_task(client, project_id, item["id"]) for item in payload["tasks"]
    ]
    parent = await _get_task(client, project_id, parent_id)

    assert parent["is_summary"] is True
    assert parent["start_date"] == min(row["start_date"] for row in child_rows)
    assert parent["finish_date"] == max(row["finish_date"] for row in child_rows)
    assert parent["work"] == sum(row["work"] for row in child_rows)


@pytest.mark.asyncio
async def test_bulk_delete_last_children_clears_parent_summary(
    client: AsyncClient,
) -> None:
    """Deleting all children through bulk endpoint resets parent summary fields."""
    project_id = await _setup_project(client, "delete-parent-rollup")
    parent_id = await _create_task(client, project_id, name="Parent")

    bulk_create_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/bulk",
        json={
            "tasks": [
                {
                    "name": "Child 1",
                    "start_date": "2024-01-04",
                    "duration": 480,  # 1 working day (8h * 60min)
                    "parent_task_id": parent_id,
                },
                {
                    "name": "Child 2",
                    "start_date": "2024-01-05",
                    "duration": 480,  # 1 working day (8h * 60min)
                    "parent_task_id": parent_id,
                },
            ]
        },
    )
    assert bulk_create_response.status_code == 200, bulk_create_response.text
    child_ids = [item["id"] for item in bulk_create_response.json()["tasks"]]

    bulk_delete_response = await client.request(
        "DELETE",
        f"/api/v1/projects/{project_id}/tasks/bulk",
        json={"task_ids": child_ids},
    )
    assert bulk_delete_response.status_code == 200, bulk_delete_response.text
    delete_payload = bulk_delete_response.json()
    assert delete_payload["succeeded"] == 2
    assert delete_payload["failed"] == 0
    assert delete_payload["errors"] == []

    parent = await _get_task(client, project_id, parent_id)
    assert parent["is_summary"] is False
    assert parent["work"] == 0
    assert parent["percent_complete"] == "0.00"
    assert parent["actual_duration"] == 0
    assert parent["remaining_duration"] == 0


@pytest.mark.asyncio
async def test_bulk_update_duration_cascades_to_ancestors(
    client: AsyncClient,
) -> None:
    """Bulk-updating child duration propagates remaining duration through ancestors."""
    project_id = await _setup_project(client, "update-duration-cascade")

    grandparent_id = await _create_task(client, project_id, name="Grandparent")
    parent_id = await _create_task(
        client,
        project_id,
        name="Parent",
        start_date="2024-01-08",
        parent_task_id=grandparent_id,
    )
    child_id = await _create_task(
        client,
        project_id,
        name="Child",
        start_date="2024-01-08",
        duration=480,  # 1 working day (8h * 60min)
        parent_task_id=parent_id,
    )

    parent_before = await _get_task(client, project_id, parent_id)
    grandparent_before = await _get_task(client, project_id, grandparent_id)
    assert parent_before["remaining_duration"] == 480
    assert grandparent_before["remaining_duration"] == 480

    bulk_update_response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/bulk",
        json={
            "tasks": [
                {
                    "id": child_id,
                    "data": {"duration": 960},  # 2 working days (2 * 480min)
                }
            ]
        },
    )
    assert bulk_update_response.status_code == 200, bulk_update_response.text
    update_payload = bulk_update_response.json()
    assert update_payload["succeeded"] == 1
    assert update_payload["failed"] == 0
    assert update_payload["errors"] == []

    parent_after = await _get_task(client, project_id, parent_id)
    grandparent_after = await _get_task(client, project_id, grandparent_id)
    assert parent_after["remaining_duration"] == 960
    assert grandparent_after["remaining_duration"] == 960
