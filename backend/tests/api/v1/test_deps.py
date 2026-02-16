import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.user import User


@pytest.mark.asyncio
async def test_inactive_user_returns_403(client: AsyncClient, session: AsyncSession):
    """Test inactive user returns 403."""
    email = "inactive@x.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Inactive User",
        },
    )
    # Set inactive
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_active = False
    await session.commit()

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_assignment_with_deleted_task_returns_404(
    client: AsyncClient, session: AsyncSession
):
    """Test assignment with deleted task returns 404."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_task@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Task",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Task", "slug": "org-del-task"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Task",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    tid = t_resp.json()["id"]
    r_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Res 1", "type": "WORK"}
    )
    rid = r_resp.json()["id"]
    a_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    aid = a_resp.json()["id"]

    # Soft delete task
    result = await session.execute(select(Task).where(Task.id == tid))
    task = result.scalar_one()
    task.is_deleted = True
    await session.commit()

    resp = await client.patch(f"/api/v1/assignments/{aid}", json={"units": 0.5})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Assignment not found"


@pytest.mark.asyncio
async def test_assignment_with_deleted_project_returns_404(
    client: AsyncClient, session: AsyncSession
):
    """Test assignment with deleted project returns 404."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_proj@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Proj",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Proj", "slug": "org-del-proj"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Proj",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    tid = t_resp.json()["id"]
    r_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Res 1", "type": "WORK"}
    )
    rid = r_resp.json()["id"]
    a_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    aid = a_resp.json()["id"]

    # Soft delete project
    result = await session.execute(select(Project).where(Project.id == proj_id))
    project = result.scalar_one()
    project.is_deleted = True
    await session.commit()

    resp = await client.patch(f"/api/v1/assignments/{aid}", json={"units": 0.5})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Assignment not found"
