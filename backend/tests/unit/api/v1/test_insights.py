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
        json={
            "name": "Task A",
            "start_date": "2024-01-01",
            "duration": 480,  # 1 working day
        },
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

    # Force over-allocation signal (1.5 units > 1.0 max).
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
    """Dashboard — returns KPIs, health, trend, and activity for seeded project."""
    org_id, _ = await _seed_project_with_data(
        client, email="ins_dash@x.com", slug="org-ins-dash"
    )

    resp = await client.get(
        f"/api/v1/organizations/{org_id}/insights/dashboard",
        params={"window_preset": "30d"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Verify all top-level sections exist AND contain correct values
    # A newly created project defaults to PLANNING; the KPI intentionally counts
    # only ACTIVE status projects, so this remains 0 unless setup explicitly
    # transitions project status to ACTIVE.
    assert data["kpis"]["active_projects"] == 0
    assert data["kpis"]["completed_projects"] == 0
    assert data["kpis"]["task_completion_pct"] == 0
    assert data["kpis"]["overdue_tasks"] == 1
    assert "project_health" in data
    assert isinstance(data["project_health"], list)
    assert "trend" in data
    assert isinstance(data["trend"], list)
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)
    assert len(data["recent_activity"]) >= 1  # at least 1 activity from task creation


@pytest.mark.asyncio
async def test_insights_custom_window_requires_dates(client: AsyncClient):
    """Dashboard — custom window preset without dates → 422 validation error."""
    org_id, _ = await _seed_project_with_data(
        client, email="ins_val@x.com", slug="org-ins-val"
    )

    org_resp = await client.get(
        f"/api/v1/organizations/{org_id}/insights/dashboard",
        params={"window_preset": "custom"},
    )
    assert org_resp.status_code == 422
    assert org_resp.json()["error"]["code"] == "VALIDATION_ERROR"
