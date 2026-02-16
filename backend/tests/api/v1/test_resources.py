import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api.v1.conftest import add_project_member


@pytest.mark.asyncio
async def test_list_resources_success(client: AsyncClient):
    """List — success — returns project resources (200)."""
    # Setup Owner, Org, Project
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org List Res", "slug": "org-list-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj List Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create Resources
    await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Res 1", "type": "WORK"}
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Res 2", "type": "MATERIAL"},
    )

    # List
    resp = await client.get(f"/api/v1/projects/{proj_id}/resources")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    names = [r["name"] for r in items]
    assert "Res 1" in names
    assert "Res 2" in names


@pytest.mark.asyncio
async def test_list_resources_filters(client: AsyncClient):
    """List — filters — type and include_inactive."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "filt_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Filt Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Filt Res", "slug": "org-filt-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Filt Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create Resources
    await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Res Work", "type": "WORK"},
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Res Mat", "type": "MATERIAL"},
    )

    # Create inactive resource (update to inactive)
    cnt_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "Res Inactive", "type": "COST"},
    )
    res_id = cnt_resp.json()["id"]
    await client.patch(
        f"/api/v1/projects/{proj_id}/resources/{res_id}", json={"is_active": False}
    )

    # Filter Type=material
    resp = await client.get(f"/api/v1/projects/{proj_id}/resources?type=MATERIAL")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Res Mat"

    # Default (active only)
    resp = await client.get(f"/api/v1/projects/{proj_id}/resources")
    items = resp.json()["items"]
    names = [r["name"] for r in items]
    assert "Res Inactive" not in names

    # Include Inactive
    resp = await client.get(
        f"/api/v1/projects/{proj_id}/resources?include_inactive=true"
    )
    assert len(resp.json()["items"]) == 3


@pytest.mark.asyncio
async def test_list_resources_pagination(client: AsyncClient):
    """List — pagination."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pag_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Pag Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Pag Res", "slug": "org-pag-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Pag Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    for i in range(3):
        await client.post(
            f"/api/v1/projects/{proj_id}/resources", json={"name": f"Res {i}"}
        )

    resp = await client.get(f"/api/v1/projects/{proj_id}/resources?page=1&per_page=2")
    assert len(resp.json()["items"]) == 2

    resp2 = await client.get(f"/api/v1/projects/{proj_id}/resources?page=2&per_page=2")
    assert len(resp2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_create_resource_success(client: AsyncClient):
    """Create — success (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr Res", "slug": "org-cr-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources",
        json={"name": "New Res", "max_units": 1.0},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Res"
    assert data["project_id"] == proj_id


@pytest.mark.asyncio
async def test_create_resource_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Create — viewer — 403."""
    # Owner Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_res_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Res VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr ResV", "slug": "org-cr-resv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr ResV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_res_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Res VU",
        },
    )
    await add_project_member(session, proj_id, "cr_res_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cr_res_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Viewer Res"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_resource_missing_fields(client: AsyncClient):
    """Create — missing required fields — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_res_miss@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Res Miss",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Miss Res", "slug": "org-miss-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Miss Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Missing name
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"type": "WORK"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_resource_success(client: AsyncClient):
    """Get — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Get Res", "slug": "org-get-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Get Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Get Me"}
    )
    res_id = c_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == res_id


@pytest.mark.asyncio
async def test_get_resource_other_project(client: AsyncClient):
    """Get — resource from other project — 404."""
    # Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_res_oth@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Res Oth",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Oth Res", "slug": "org-oth-res"}
    )
    org_id = org_resp.json()["id"]

    # Proj 1
    p1 = await client.post(
        "/api/v1/projects",
        json={"name": "P1", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pid1 = p1.json()["id"]
    r1 = await client.post(f"/api/v1/projects/{pid1}/resources", json={"name": "R1"})
    rid1 = r1.json()["id"]

    # Proj 2
    p2 = await client.post(
        "/api/v1/projects",
        json={"name": "P2", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pid2 = p2.json()["id"]

    # Try get R1 via P2
    resp = await client.get(f"/api/v1/projects/{pid2}/resources/{rid1}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_resource_not_found(client: AsyncClient):
    """Get — non-existent — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_res_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Res NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Res NF", "slug": "org-res-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Res NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/projects/{proj_id}/resources/{rand_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_resource_success(client: AsyncClient):
    """Update — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Res", "slug": "org-upd-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Upd Me"}
    )
    res_id = c_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/resources/{res_id}", json={"name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_resource_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — viewer — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_res_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Res VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd ResV", "slug": "org-upd-resv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd ResV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Target"}
    )
    res_id = c_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_res_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Res VU",
        },
    )
    await add_project_member(session, proj_id, "upd_res_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_res_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/resources/{res_id}", json={"name": "Fail"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_resource_not_found(client: AsyncClient):
    """Update — non-existent — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_res_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Res NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd NF", "slug": "org-upd-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/resources/{rand_id}", json={"name": "Fail"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_resource_success_owner(client: AsyncClient):
    """Delete — success — owner (204)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Res", "slug": "org-del-res"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Res",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Del Me"}
    )
    res_id = c_resp.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert resp.status_code == 204

    # Check deleted (hard delete -> 404)
    get_resp = await client.get(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_resource_success_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — success — manager (204)."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_mo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res MO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del ResM", "slug": "org-del-resm"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del ResM",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Del Mgr"}
    )
    res_id = c_resp.json()["id"]

    # Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_mu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res MU",
        },
    )
    await add_project_member(session, proj_id, "del_res_mu@x.com", "manager")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_res_mu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_resource_forbidden_member(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — member — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_fo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res FO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del ResF", "slug": "org-del-resf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del ResF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Target"}
    )
    res_id = c_resp.json()["id"]

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_fu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res FU",
        },
    )
    await add_project_member(session, proj_id, "del_res_fu@x.com", "member")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_res_fu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_resource_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — viewer — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del ResV", "slug": "org-del-resv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del ResV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Target"}
    )
    res_id = c_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res VU",
        },
    )
    await add_project_member(session, proj_id, "del_res_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_res_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/resources/{res_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_resource_not_found(client: AsyncClient):
    """Delete — non-existent — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_res_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Res NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del NF", "slug": "org-del-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/v1/projects/{proj_id}/resources/{rand_id}")
    assert resp.status_code == 404
