"""
Opt-in backend performance smoke tests.

These are intentionally gated behind RUN_PERF_TESTS=1 to keep the default suite
fast and deterministic while still codifying performance expectations.
"""

import os
import time
import uuid

import pytest
from httpx import AsyncClient

PERF_ENABLED = os.getenv("RUN_PERF_TESTS") == "1"


async def _register(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _setup_project(client: AsyncClient, suffix: str) -> str:
    slug = suffix.lower().replace("_", "-")
    await _register(client, f"perf_{slug}@x.com", f"Perf {suffix}")
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": f"Perf Org {suffix}",
            "slug": f"perf-org-{slug}-{uuid.uuid4().hex[:6]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Perf Project {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


async def _bulk_create_tasks(
    client: AsyncClient,
    project_id: str,
    count: int,
    *,
    prefix: str,
) -> list[str]:
    created_ids: list[str] = []
    chunk_size = 50

    for chunk_start in range(0, count, chunk_size):
        tasks = []
        for i in range(chunk_start, min(chunk_start + chunk_size, count)):
            tasks.append(
                {
                    "name": f"{prefix} {i + 1}",
                    "start_date": "2024-01-01",
                    "duration": 480,  # 1 working day (8h * 60min)
                }
            )

        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks/bulk",
            json={"tasks": tasks},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["errors"] == []
        created_ids.extend(item["id"] for item in payload["tasks"])

    return created_ids


@pytest.mark.asyncio
@pytest.mark.skipif(not PERF_ENABLED, reason="Set RUN_PERF_TESTS=1 to run perf suite.")
async def test_schedule_500_tasks_completes_under_5_seconds(
    client: AsyncClient,
) -> None:
    """Performance target: 500-task schedule recalculation completes under 5s."""
    project_id = await _setup_project(client, "schedule-500")
    await _bulk_create_tasks(client, project_id, 500, prefix="Perf Task")

    start = time.perf_counter()
    response = await client.post(f"/api/v1/projects/{project_id}/schedule/calculate")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200, response.text
    assert elapsed < 5.0


@pytest.mark.asyncio
@pytest.mark.skipif(not PERF_ENABLED, reason="Set RUN_PERF_TESTS=1 to run perf suite.")
async def test_schedule_100_tasks_200_dependencies_no_timeout(
    client: AsyncClient,
) -> None:
    """Performance target: dense dependency graph recalculates without timeout."""
    project_id = await _setup_project(client, "dense-deps")
    task_ids = await _bulk_create_tasks(client, project_id, 100, prefix="Dense Task")

    # 200 dependencies: linear chain (99) + skip links (101).
    dep_pairs: list[tuple[str, str]] = []
    dep_pairs.extend((task_ids[i], task_ids[i + 1]) for i in range(99))
    dep_pairs.extend((task_ids[i], task_ids[i + 2]) for i in range(98))
    dep_pairs.extend((task_ids[i], task_ids[i + 3]) for i in range(3))

    assert len(dep_pairs) == 200
    for pred, succ in dep_pairs:
        dep_response = await client.post(
            f"/api/v1/projects/{project_id}/dependencies",
            json={
                "predecessor_id": pred,
                "successor_id": succ,
                "type": "FS",
            },
        )
        assert dep_response.status_code == 201, dep_response.text

    start = time.perf_counter()
    response = await client.post(f"/api/v1/projects/{project_id}/schedule/calculate")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200, response.text
    # "No timeout" pass-now threshold for local/dev hardware.
    assert elapsed < 15.0


@pytest.mark.asyncio
@pytest.mark.skipif(not PERF_ENABLED, reason="Set RUN_PERF_TESTS=1 to run perf suite.")
async def test_utilization_365_day_range_responds_quickly(client: AsyncClient) -> None:
    """Performance target: 365-day utilization query returns in acceptable time."""
    project_id = await _setup_project(client, "utilization-365")

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Perf Resource", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Perf Utilization Task",
            "start_date": "2024-01-01",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 0.8,
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    start = time.perf_counter()
    response = await client.get(
        f"/api/v1/projects/{project_id}/utilization/{resource_id}",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200, response.text
    assert elapsed < 3.0


@pytest.mark.asyncio
@pytest.mark.skipif(not PERF_ENABLED, reason="Set RUN_PERF_TESTS=1 to run perf suite.")
async def test_bulk_create_50_tasks_completes_under_3_seconds(
    client: AsyncClient,
) -> None:
    """Performance target: bulk create 50 tasks stays under 3s."""
    project_id = await _setup_project(client, "bulk-create-50")
    tasks = [
        {
            "name": f"Bulk Perf Task {i + 1}",
            "start_date": "2024-01-01",
            "duration": 480,
        }
        for i in range(50)
    ]

    start = time.perf_counter()
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/bulk",
        json={"tasks": tasks},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["tasks"]) == 50
    assert payload["errors"] == []
    assert elapsed < 3.0
