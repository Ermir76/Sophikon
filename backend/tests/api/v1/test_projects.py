import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User


@pytest.fixture
async def setup_roles(session: AsyncSession):
    """Seed default roles."""
    # Check if exist
    for r_name in ["manager", "member", "viewer"]:
        res = await session.execute(select(Role).where(Role.name == r_name))
        if not res.scalar_one_or_none():
            role = Role(name=r_name, scope="project")
            session.add(role)
    await session.commit()


async def add_project_member(session: AsyncSession, project_id, user_email, role_name):
    """Helper: Add user to project with role."""
    # Get user
    res_u = await session.execute(select(User).where(User.email == user_email))
    user = res_u.scalar_one_or_none()
    assert user

    # Get role
    res_r = await session.execute(select(Role).where(Role.name == role_name))
    role = res_r.scalar_one_or_none()
    assert role

    member = ProjectMember(project_id=project_id, user_id=user.id, role_id=role.id)
    session.add(member)
    await session.commit()


@pytest.mark.asyncio
async def test_list_projects_success(client: AsyncClient):
    """List — success — returns projects user has access to."""
    # 1. Register User
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_proj_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Proj U",
        },
    )
    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org List Proj", "slug": "org-list-proj"},
    )
    org_id = create_resp.json()["id"]

    # 2. Create Project (Owner)
    await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Owner",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )

    # 3. List
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Proj Owner"


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient):
    """Create — success — creates project (201)."""
    # Register/Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj U",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Proj", "slug": "org-cr-proj"},
    )
    org_id = org_resp.json()["id"]

    # Create Project
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "New Proj",
            "organization_id": org_id,
            "start_date": "2024-05-01",
            "description": "Desc",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Proj"
    assert data["organization_id"] == org_id


@pytest.mark.asyncio
async def test_create_project_non_org_member(client: AsyncClient):
    """Create — non-org-member — returns 403."""
    # Register User A (Intruder)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_intro@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj Intr",
        },
    )

    # Register User B (Owner) -> Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_own@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj Own",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Proj Sec", "slug": "org-cr-proj-sec"},
    )
    org_id = org_resp.json()["id"]

    # Login Intruder
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cr_proj_intro@x.com", "password": "StrongPassword123!"},
    )

    # Try Create Project in Org
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Intr Proj",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_project_non_member(client: AsyncClient):
    """Get — non-member — returns 403."""
    # Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_nm_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get NM O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org NM", "slug": "org-nm"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={"name": "Proj NM", "organization_id": org_id, "start_date": "2024-01-01"},
    )
    proj_id = proj_resp.json()["id"]

    # Register Intruder
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_nm_i@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get NM I",
        },
    )

    # Try Get
    response = await client.get(f"/api/v1/projects/{proj_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_project_success_owner(client: AsyncClient):
    """Update — success — owner can update (200)."""
    # Register/Create
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd", "slug": "org-upd"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Update
    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Proj Upd New"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Proj Upd New"


@pytest.mark.asyncio
async def test_update_project_success_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — success — manager can update (200)."""
    # 1. Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_mgr_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Mgr O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Mgr", "slug": "org-mgr"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Mgr",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # 2. Register Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_mgr_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Mgr U",
        },
    )

    # 3. Add Manager Role directly to DB
    await add_project_member(session, proj_id, "upd_mgr_u@x.com", "manager")

    # 4. Login Manager & Update
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_mgr_u@x.com", "password": "StrongPassword123!"},
    )
    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Proj Mgr Upd"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Proj Mgr Upd"


@pytest.mark.asyncio
async def test_update_project_forbidden_member(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — member — returns 403."""
    # Owner Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_mem_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Mem O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Mem Forbidden", "slug": "org-mem-forbid"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Mem Forbid",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Member Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_mem_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Mem U",
        },
    )
    await add_project_member(session, proj_id, "upd_mem_u@x.com", "member")

    # Login Member & Try Update
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_mem_u@x.com", "password": "StrongPassword123!"},
    )
    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Should Fail"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_project_success_owner(client: AsyncClient):
    """Delete — success — owner can soft-delete (204)."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_proj_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Proj O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del", "slug": "org-del"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/projects/{proj_id}")
    assert response.status_code == 204

    # Verify 404
    get_resp = await client.get(f"/api/v1/projects/{proj_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_forbidden_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — manager — returns 403."""
    # Setup Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_mgr_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Mgr O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Mgr", "slug": "org-del-mgr"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Mgr",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Setup Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_mgr_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Mgr U",
        },
    )
    await add_project_member(session, proj_id, "del_mgr_u@x.com", "manager")

    # Login Manager & Try Delete
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_mgr_u@x.com", "password": "StrongPassword123!"},
    )
    response = await client.delete(f"/api/v1/projects/{proj_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient):
    """List — pagination — returns paginated results."""
    # Setup Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_pag_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Pag O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Pag", "slug": "org-pag"}
    )
    org_id = org_resp.json()["id"]

    # Create 3 projects
    for i in range(3):
        await client.post(
            "/api/v1/projects",
            json={
                "name": f"Proj {i}",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )

    # Page 1 (limit 2)
    resp1 = await client.get("/api/v1/projects?page=1&per_page=2")
    assert resp1.status_code == 200
    assert len(resp1.json()["items"]) == 2

    # Page 2 (limit 2)
    resp2 = await client.get("/api/v1/projects?page=2&per_page=2")
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_create_project_missing_fields(client: AsyncClient):
    """Create — missing fields — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_miss@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Miss",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Miss", "slug": "org-miss"}
    )
    org_id = org_resp.json()["id"]

    # Missing name
    resp1 = await client.post(
        "/api/v1/projects", json={"organization_id": org_id, "start_date": "2024-01-01"}
    )
    assert resp1.status_code == 422

    # Missing organization_id
    resp2 = await client.post(
        "/api/v1/projects", json={"name": "No Org", "start_date": "2024-01-01"}
    )
    assert resp2.status_code == 422

    # Missing start_date
    resp3 = await client.post(
        "/api/v1/projects", json={"name": "No Date", "organization_id": org_id}
    )
    assert resp3.status_code == 422


@pytest.mark.asyncio
async def test_get_project_success(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Get — success — member can access (200)."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_mem_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Mem O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Get Mem", "slug": "org-get-mem"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Get Mem",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Owner Get
    resp = await client.get(f"/api/v1/projects/{proj_id}")
    assert resp.status_code == 200

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_mem_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Mem U",
        },
    )
    await add_project_member(session, proj_id, "get_mem_u@x.com", "member")

    # Login Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": "get_mem_u@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Get — not found — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_nf_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Nf O",
        },
    )
    await client.post(
        "/api/v1/organizations", json={"name": "Org Nf", "slug": "org-nf"}
    )

    rand_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/projects/{rand_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project_forbidden_viewer(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — viewer — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_view_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd View O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org View Forbid", "slug": "org-view-forbid"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj View Forbid",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_view_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd View U",
        },
    )
    await add_project_member(session, proj_id, "upd_view_u@x.com", "viewer")

    # Login Viewer
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_view_u@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.patch(f"/api/v1/projects/{proj_id}", json={"name": "Fail"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_project_forbidden_member(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — member — returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_mem_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Mem O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Mem", "slug": "org-del-mem"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Mem",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_mem_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del Mem U",
        },
    )
    await add_project_member(session, proj_id, "del_mem_u@x.com", "member")

    # Login Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_mem_u@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_projects_filter_org(client: AsyncClient):
    """List — filter by org — returns only projects in org."""
    # Setup Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_filt_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Filt O",
        },
    )

    # Org 1
    org1_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Filt 1", "slug": "org-filt-1"}
    )
    org1_id = org1_resp.json()["id"]
    await client.post(
        "/api/v1/projects",
        json={"name": "Proj 1", "organization_id": org1_id, "start_date": "2024-01-01"},
    )

    # Org 2
    org2_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Filt 2", "slug": "org-filt-2"}
    )
    org2_id = org2_resp.json()["id"]
    await client.post(
        "/api/v1/projects",
        json={"name": "Proj 2", "organization_id": org2_id, "start_date": "2024-01-01"},
    )

    # Filter Org 1
    resp = await client.get(f"/api/v1/projects?organization_id={org1_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Proj 1"


@pytest.mark.asyncio
async def test_list_projects_filter_status(client: AsyncClient):
    """List — filter by status — returns only matching projects."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "filt_stat@x.com",
            "password": "StrongPassword123!",
            "full_name": "Filt Stat",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Filt Stat", "slug": "org-filt-stat"}
    )
    org_id = org_resp.json()["id"]

    # Create project (default status is "planning")
    await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Plan",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )

    # Filter by PLANNING — should find it
    resp = await client.get("/api/v1/projects?status=PLANNING")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    # Filter by ACTIVE — should find nothing
    resp2 = await client.get("/api/v1/projects?status=ACTIVE")
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 0


@pytest.mark.asyncio
async def test_list_projects_filter_search(client: AsyncClient):
    """List — filter by search — returns only matching projects."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "filt_search@x.com",
            "password": "StrongPassword123!",
            "full_name": "Filt Search",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Filt Search", "slug": "org-filt-search"},
    )
    org_id = org_resp.json()["id"]

    await client.post(
        "/api/v1/projects",
        json={
            "name": "Alpha Project",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    await client.post(
        "/api/v1/projects",
        json={
            "name": "Beta Project",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )

    # Search "Alpha" — should find 1
    resp = await client.get("/api/v1/projects?search=Alpha")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Alpha Project"

    # Search "Project" — should find 2
    resp2 = await client.get("/api/v1/projects?search=Project")
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 2


@pytest.mark.asyncio
async def test_list_projects_unauthenticated(client: AsyncClient):
    """List — unauthenticated — returns 401."""
    # Logout (clear cookies)
    client.cookies.clear()
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_project_non_existent_org(client: AsyncClient):
    """Create — non-existent org — returns 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_ne_org@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Ne Org",
        },
    )

    rand_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Ne Org",
            "organization_id": rand_id,
            "start_date": "2024-01-01",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_project_deleted(client: AsyncClient):
    """Get — deleted — returns 404."""
    # Setup Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_del_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get Del O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Get Del", "slug": "org-get-del"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Get Del",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Delete
    await client.delete(f"/api/v1/projects/{proj_id}")

    # Try Get
    resp = await client.get(f"/api/v1/projects/{proj_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_project_invalid_fields(client: AsyncClient):
    """Update — invalid date format — returns 422."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_inv_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Inv O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Inv", "slug": "org-upd-inv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Inv",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Invalid date format
    resp = await client.patch(
        f"/api/v1/projects/{proj_id}", json={"start_date": "invalid-date"}
    )
    assert resp.status_code == 422
