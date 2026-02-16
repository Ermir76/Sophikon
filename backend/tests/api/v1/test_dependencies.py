import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api.v1.conftest import add_project_member


@pytest.mark.asyncio
async def test_list_dependencies_success(client: AsyncClient):
    """List — returns project dependencies (200)."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_dep_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Dep O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org List Dep", "slug": "org-list-dep"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj List Dep",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Tasks
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    # Dep
    await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/dependencies")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_dependencies_pagination(client: AsyncClient):
    """List — pagination."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_dep_pag@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Dep Pag",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Dep Pag", "slug": "org-dep-pag"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Dep Pag",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    tasks = []
    for i in range(4):
        t = await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": f"T{i}", "start_date": "2024-01-01", "duration": 480},
        )
        tasks.append(t.json()["id"])

    for i in range(3):
        await client.post(
            f"/api/v1/projects/{proj_id}/dependencies",
            json={
                "predecessor_id": tasks[i],
                "successor_id": tasks[i + 1],
                "type": "FS",
            },
        )

    resp = await client.get(
        f"/api/v1/projects/{proj_id}/dependencies?page=1&per_page=2"
    )
    assert len(resp.json()["items"]) == 2

    resp2 = await client.get(
        f"/api/v1/projects/{proj_id}/dependencies?page=2&per_page=2"
    )
    assert len(resp2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_create_dependency_success(client: AsyncClient):
    """Create — success (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr Dep", "slug": "org-cr-dep"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Dep",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "FS"


@pytest.mark.asyncio
async def test_create_dependency_task_not_in_project(client: AsyncClient):
    """Create — task not in project — returns 400."""
    # Org 1
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_bad@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep Bad",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Dep Bad", "slug": "org-cr-dep-bad"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Dep Bad",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]

    # Proj 2
    p2 = await client.post(
        "/api/v1/projects",
        json={"name": "P2", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pid2 = p2.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{pid2}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    # Try create in Proj 1 using T2 (from Proj 2)
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_dependency_duplicate(client: AsyncClient):
    """Create — duplicate dependency — returns 409."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_dup@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep Dup",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Dep Dup", "slug": "org-cr-dep-dup"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Dep Dup",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_dependency_self_reference(client: AsyncClient):
    """Create — self-reference — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_self@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep Self",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Dep Self", "slug": "org-cr-dep-self"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Dep Self",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid1, "type": "FS"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_dependency_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Create — viewer role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr DepV", "slug": "org-cr-depv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr DepV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep VU",
        },
    )
    await add_project_member(session, proj_id, "cr_dep_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cr_dep_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_dependency_missing_fields(client: AsyncClient):
    """Create — missing required fields — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_dep_miss@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Dep Miss",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Dep Miss", "slug": "org-cr-dep-miss"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Dep Miss",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "type": "FS"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_dependency_success(client: AsyncClient):
    """Update — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_dep_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Dep O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Dep", "slug": "org-upd-dep"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Dep",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]
    d_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    did = d_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/dependencies/{did}", json={"type": "SS", "lag": 60}
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "SS"
    assert resp.json()["lag"] == 60


@pytest.mark.asyncio
async def test_update_dependency_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — viewer role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_dep_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Dep VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd DepV", "slug": "org-upd-depv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd DepV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]
    d_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    did = d_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_dep_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Dep VU",
        },
    )
    await add_project_member(session, proj_id, "upd_dep_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_dep_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/dependencies/{did}", json={"type": "SS"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_dependency_not_found(client: AsyncClient):
    """Update — non-existent dependency — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_dep_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Dep NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Dep NF", "slug": "org-upd-dep-nf"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Dep NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/dependencies/{rand_id}", json={"type": "SS"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_dependency_success_owner(client: AsyncClient):
    """Delete — owner — returns 204."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Dep", "slug": "org-del-dep"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Dep",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]
    d_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    did = d_resp.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{proj_id}/dependencies/{did}")
    assert resp.status_code == 204

    # Check 404
    d2 = await client.patch(
        f"/api/v1/projects/{proj_id}/dependencies/{did}", json={"type": "SS"}
    )
    assert d2.status_code == 404


@pytest.mark.asyncio
async def test_delete_dependency_success_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — manager — returns 204."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_mo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep MO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Dep M", "slug": "org-del-dep-m"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Dep M",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]
    d_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    did = d_resp.json()["id"]

    # Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_mu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep MU",
        },
    )
    await add_project_member(session, proj_id, "del_dep_mu@x.com", "manager")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_dep_mu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/dependencies/{did}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_dependency_forbidden_member(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — member role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_fo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep FO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Dep F", "slug": "org-del-dep-f"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Dep F",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    tid1 = t1.json()["id"]
    t2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    tid2 = t2.json()["id"]
    d_resp = await client.post(
        f"/api/v1/projects/{proj_id}/dependencies",
        json={"predecessor_id": tid1, "successor_id": tid2, "type": "FS"},
    )
    did = d_resp.json()["id"]

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_fu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep FU",
        },
    )
    await add_project_member(session, proj_id, "del_dep_fu@x.com", "member")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_dep_fu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/dependencies/{did}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_dependency_not_found(client: AsyncClient):
    """Delete — non-existent dependency — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_dep_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Dep NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Del Dep NF", "slug": "org-del-dep-nf"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Dep NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/v1/projects/{proj_id}/dependencies/{rand_id}")
    assert resp.status_code == 404
