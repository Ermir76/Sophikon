import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api.v1.conftest import add_project_member


@pytest.mark.asyncio
async def test_list_assignments_success(client: AsyncClient):
    """List — returns assignments for task (200)."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_asn_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Asn O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org List Asn", "slug": "org-list-asn"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj List Asn",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Task + Resource
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    tid = t_resp.json()["id"]
    r_resp = await client.post(
        f"/api/v1/projects/{proj_id}/resources", json={"name": "Res 1", "type": "WORK"}
    )
    rid = r_resp.json()["id"]

    # Assign
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_list_assignments_task_not_found(client: AsyncClient):
    """List — non-existent task — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_asn_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Asn NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org List Asn NF", "slug": "org-list-asn-nf"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj List Asn NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{rand_id}/assignments")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_assignment_success(client: AsyncClient):
    """Create — assigns resource to task (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr Asn", "slug": "org-cr-asn"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr Asn",
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

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 0.5,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["units"] == "0.50"


@pytest.mark.asyncio
async def test_create_assignment_resource_not_in_project(client: AsyncClient):
    """Create — resource not in project — returns 400."""
    # Org 1, Proj 1
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_bad@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn Bad",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Asn Bad", "slug": "org-asn-bad"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Asn Bad",
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

    # Proj 2 -> Res 2
    proj2_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Proj 2", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    pid2 = proj2_resp.json()["id"]
    r_resp = await client.post(
        f"/api/v1/projects/{pid2}/resources", json={"name": "Res 2", "type": "WORK"}
    )
    rid = r_resp.json()["id"]

    # Try assign Res 2 (from Proj 2) to Task 1 (in Proj 1)
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_assignment_duplicate(client: AsyncClient):
    """Create — duplicate assignment — returns 409."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_dup@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn Dup",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Asn Dup", "slug": "org-asn-dup"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Asn Dup",
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

    await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_assignment_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Create — viewer role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Asn VO", "slug": "org-asn-vo"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Asn VO",
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

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn VU",
        },
    )
    await add_project_member(session, proj_id, "cr_asn_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cr_asn_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": 1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_assignment_missing_fields(client: AsyncClient):
    """Create — missing required fields — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_miss@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn Miss",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Asn Miss", "slug": "org-asn-miss"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Asn Miss",
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

    # Missing resource_id
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments", json={"units": 1.0}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_assignment_invalid_units(client: AsyncClient):
    """Create — invalid units (negative) — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_asn_un@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Asn Un",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Asn Un", "slug": "org-asn-un"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Asn Un",
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

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments",
        json={
            "resource_id": rid,
            "units": -1.0,
            "start_date": "2024-01-01",
            "finish_date": "2024-01-02",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_assignment_success(client: AsyncClient):
    """Update — partial update — returns 200."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_asn_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Asn O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Asn", "slug": "org-upd-asn"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Asn",
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

    resp = await client.patch(f"/api/v1/assignments/{aid}", json={"units": 0.5})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_assignment_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — viewer role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_asn_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Asn VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd AsnV", "slug": "org-upd-asnv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd AsnV",
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

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_asn_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Asn VU",
        },
    )
    await add_project_member(session, proj_id, "upd_asn_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_asn_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.patch(f"/api/v1/assignments/{aid}", json={"units": 0.5})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_assignment_invalid_percent(client: AsyncClient):
    """Update — invalid percent work complete — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_asn_pct@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Asn Pct",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Pct", "slug": "org-upd-pct"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Pct",
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

    resp = await client.patch(
        f"/api/v1/assignments/{aid}", json={"percent_work_complete": 101}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_assignment_not_found(client: AsyncClient):
    """Update — non-existent assignment — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_asn_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Asn NF",
        },
    )

    rand_id = str(uuid.uuid4())
    resp = await client.patch(f"/api/v1/assignments/{rand_id}", json={"units": 0.5})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_assignment_success_owner(client: AsyncClient):
    """Delete — success — owner (204)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Asn", "slug": "org-del-asn"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Asn",
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

    resp = await client.delete(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 204

    # Check 404
    get_resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{tid}/assignments")
    items = get_resp.json()
    ids = [i["id"] for i in items]
    assert aid not in ids


@pytest.mark.asyncio
async def test_delete_assignment_success_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — success — manager (204)."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_mo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn MO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del AsnM", "slug": "org-del-asnm"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del AsnM",
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

    # Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_mu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn MU",
        },
    )
    await add_project_member(session, proj_id, "del_asn_mu@x.com", "manager")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_asn_mu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_assignment_forbidden_member(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — member role — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_fo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn FO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del AsnF", "slug": "org-del-asnf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del AsnF",
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

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_fu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn FU",
        },
    )
    await add_project_member(session, proj_id, "del_asn_fu@x.com", "member")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_asn_fu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/assignments/{aid}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_assignment_not_found(client: AsyncClient):
    """Delete — non-existent assignment — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_asn_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Asn NF",
        },
    )

    rand_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/v1/assignments/{rand_id}")
    assert resp.status_code == 404
