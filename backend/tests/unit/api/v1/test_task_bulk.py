import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.project_members import add_project_member


@pytest.mark.asyncio
async def test_bulk_create_tasks_success(client: AsyncClient):
    """Bulk create — success — creates multiple tasks."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bc_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "BC Ok",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BC", "slug": "org-bc"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BC",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    payload = {
        "tasks": [
            {"name": "Bulk 1", "start_date": "2024-01-01", "duration": 480},
            {"name": "Bulk 2", "start_date": "2024-01-02", "duration": 480},
            {"name": "Bulk 3", "start_date": "2024-01-03", "duration": 480},
        ]
    }

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 3
    assert len(data["errors"]) == 0
    assert data["tasks"][0]["name"] == "Bulk 1"
    assert data["tasks"][1]["name"] == "Bulk 2"
    assert data["tasks"][2]["name"] == "Bulk 3"


@pytest.mark.asyncio
async def test_bulk_create_tasks_invalid_parent(client: AsyncClient):
    """Bulk create — partial success with invalid parent."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bc_inv_p@x.com",
            "password": "StrongPassword123!",
            "full_name": "BC Inv P",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BC P", "slug": "org-bc-p"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BC P",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    fake_id = str(uuid.uuid4())
    payload = {
        "tasks": [
            {"name": "Valid Task", "start_date": "2024-01-01", "duration": 480},
            {
                "name": "Invalid Parent Task",
                "start_date": "2024-01-01",
                "duration": 480,
                "parent_task_id": fake_id,
            },
        ]
    }

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["name"] == "Valid Task"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["index"] == 1


@pytest.mark.asyncio
async def test_bulk_create_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Bulk create — viewer role — 403."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bc_v_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "BC VO",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BC V", "slug": "org-bc-v"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BC V",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bc_v_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "BC VU",
        },
    )
    await add_project_member(session, proj_id, "bc_v_u@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "bc_v_u@x.com", "password": "StrongPassword123!"},
    )

    payload = {
        "tasks": [{"name": "Bulk Viewer", "start_date": "2024-01-01", "duration": 480}]
    }
    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bulk_update_tasks_success(client: AsyncClient):
    """Bulk update — success."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU Ok",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BU", "slug": "org-bu"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BU",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    payload = {
        "tasks": [
            {"id": t1_id, "data": {"name": "T1 Updated"}},
            {"id": t2_id, "data": {"name": "T2 Updated"}},
        ]
    }

    resp = await client.patch(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 2
    assert data["failed"] == 0
    assert len(data["errors"]) == 0

    # Verify
    t1_check = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{t1_id}")).json()
    assert t1_check["name"] == "T1 Updated"


@pytest.mark.asyncio
async def test_bulk_update_syncs_duration_progress_fields_for_leaf_tasks(
    client: AsyncClient,
):
    """Bulk update — leaf duration progress fields are recalculated."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_dur@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU Dur",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BU Dur", "slug": "org-bu-dur"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BU Dur",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    payload = {
        "tasks": [
            {"id": t1_id, "data": {"percent_complete": 50}},
            {"id": t2_id, "data": {"duration": 600, "percent_complete": 25}},
        ]
    }
    resp = await client.patch(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 2
    assert data["failed"] == 0

    t1 = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{t1_id}")).json()
    assert t1["actual_duration"] == 240
    assert t1["remaining_duration"] == 240

    t2 = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{t2_id}")).json()
    assert t2["actual_duration"] == 150
    assert t2["remaining_duration"] == 450


@pytest.mark.asyncio
async def test_bulk_update_tasks_nonexistent(client: AsyncClient):
    """Bulk update — nonexistent task partial success."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_non@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU Non",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BU Non", "slug": "org-bu-non"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BU Non",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    fake_id = str(uuid.uuid4())

    payload = {
        "tasks": [
            {"id": t1_id, "data": {"name": "T1 Updated"}},
            {"id": fake_id, "data": {"name": "Ghost Updated"}},
        ]
    }

    resp = await client.patch(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["index"] == 1


@pytest.mark.asyncio
async def test_bulk_update_rejects_computed_fields_on_summary_task(client: AsyncClient):
    """Bulk update — summary rollup fields are rejected per task."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_sum@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU Sum",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BU Sum", "slug": "org-bu-sum"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BU Sum",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    parent_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    leaf_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Leaf", "start_date": "2024-01-02", "duration": 480},
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Child",
            "start_date": "2024-01-03",
            "duration": 480,
            "parent_task_id": parent_id,
        },
    )

    payload = {
        "tasks": [
            {"id": parent_id, "data": {"percent_complete": 75}},
            {"id": leaf_id, "data": {"name": "Leaf Updated"}},
        ]
    }

    resp = await client.patch(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert "auto-calculate percent_complete" in data["errors"][0]["message"]

    leaf = (await client.get(f"/api/v1/projects/{proj_id}/tasks/{leaf_id}")).json()
    assert leaf["name"] == "Leaf Updated"


@pytest.mark.asyncio
async def test_bulk_update_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Bulk update — viewer role — 403."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_v_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU VO",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BU V", "slug": "org-bu-v"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BU V",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bu_v_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "BU VU",
        },
    )
    await add_project_member(session, proj_id, "bu_v_u@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "bu_v_u@x.com", "password": "StrongPassword123!"},
    )

    payload = {"tasks": [{"id": t1_id, "data": {"name": "T1 Updated"}}]}
    resp = await client.patch(f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bulk_delete_tasks_success(client: AsyncClient):
    """Bulk delete — success."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bd_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "BD Ok",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BD", "slug": "org-bd"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BD",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    payload = {"task_ids": [t1_id, t2_id]}

    resp = await client.request(
        "DELETE", f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 2
    assert data["failed"] == 0
    assert len(data["errors"]) == 0

    # Verify
    t1_check = await client.get(f"/api/v1/projects/{proj_id}/tasks/{t1_id}")
    assert t1_check.status_code == 404


@pytest.mark.asyncio
async def test_bulk_delete_tasks_nonexistent(client: AsyncClient):
    """Bulk delete — nonexistent task partial success."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bd_non@x.com",
            "password": "StrongPassword123!",
            "full_name": "BD Non",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BD Non", "slug": "org-bd-non"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BD Non",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]
    fake_id = str(uuid.uuid4())

    payload = {"task_ids": [t1_id, fake_id]}

    resp = await client.request(
        "DELETE", f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["index"] == 1


@pytest.mark.asyncio
async def test_bulk_delete_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Bulk delete — viewer role — 403."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bd_v_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "BD VO",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org BD V", "slug": "org-bd-v"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj BD V",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    t1_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bd_v_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "BD VU",
        },
    )
    await add_project_member(session, proj_id, "bd_v_u@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "bd_v_u@x.com", "password": "StrongPassword123!"},
    )

    payload = {"task_ids": [t1_id]}
    resp = await client.request(
        "DELETE", f"/api/v1/projects/{proj_id}/tasks/bulk", json=payload
    )
    assert resp.status_code == 403
