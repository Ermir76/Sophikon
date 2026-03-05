import uuid

import pytest
from httpx import AsyncClient


async def _seed_project_with_data(client: AsyncClient, email: str, slug: str):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Insights User",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    org_id = org_resp.json()["id"]

    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Insights Project",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    project_id = proj_resp.json()["id"]

    task_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"name": "Task A", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = task_resp.json()["id"]

    # Force overdue task for KPI/risk signal.
    await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"finish_date": "2024-01-02", "percent_complete": 25},
    )

    resource_resp = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Res A", "max_units": 1.0},
    )
    resource_id = resource_resp.json()["id"]

    # Force over-allocation signal.
    await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.5,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )

    return org_id, project_id


@pytest.mark.asyncio
async def test_dashboard_insights_success(client: AsyncClient):
    org_id, _ = await _seed_project_with_data(
        client, email="ins_dash@x.com", slug="org-ins-dash"
    )

    resp = await client.get(
        f"/api/v1/organizations/{org_id}/insights/dashboard",
        params={"window_preset": "30d"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "project_health" in data
    assert "trend" in data
    assert "recent_activity" in data
    assert data["kpis"]["active_projects"] >= 0


@pytest.mark.asyncio
async def test_project_overview_insights_success(client: AsyncClient):
    _, project_id = await _seed_project_with_data(
        client, email="ins_proj@x.com", slug="org-ins-proj"
    )

    resp = await client.get(
        f"/api/v1/projects/{project_id}/insights/overview",
        params={"window_preset": "30d"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "schedule" in data
    assert "trend" in data
    assert "risk_items" in data
    assert "recent_activity" in data
    assert data["kpis"]["total_tasks"] >= 1


@pytest.mark.asyncio
async def test_insights_custom_window_requires_dates(client: AsyncClient):
    org_id, project_id = await _seed_project_with_data(
        client, email="ins_val@x.com", slug="org-ins-val"
    )

    org_resp = await client.get(
        f"/api/v1/organizations/{org_id}/insights/dashboard",
        params={"window_preset": "custom"},
    )
    assert org_resp.status_code == 422

    proj_resp = await client.get(
        f"/api/v1/projects/{project_id}/insights/overview",
        params={"window_preset": "custom"},
    )
    assert proj_resp.status_code == 422


@pytest.mark.asyncio
async def test_project_overview_insights_forbidden_non_member(client: AsyncClient):
    _, project_id = await _seed_project_with_data(
        client, email="ins_owner@x.com", slug="org-ins-owner"
    )

    # Different user without membership.
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ins_intruder@x.com",
            "password": "StrongPassword123!",
            "full_name": "Intruder",
        },
    )

    resp = await client.get(f"/api/v1/projects/{project_id}/insights/overview")
    assert resp.status_code == 403

    # Random UUID also should not leak details.
    random_project = str(uuid.uuid4())
    resp2 = await client.get(f"/api/v1/projects/{random_project}/insights/overview")
    assert resp2.status_code in (403, 404)
