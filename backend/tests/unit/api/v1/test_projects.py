import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.service import auth_service
from tests.fixtures.project_members import add_project_member


async def _seed_project_dashboard_data(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> str:
    today = date.today()

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Dashboard User",
        },
    )
    assert register_response.status_code == 201, register_response.text

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Dashboard Project",
            "organization_id": org_id,
            "start_date": str(today - timedelta(days=14)),
            "budget": 15000,
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_payloads = [
        {
            "name": "Completed task",
            "start_date": str(today - timedelta(days=9)),
            "duration": 480,
        },
        {
            "name": "Overdue critical task",
            "start_date": str(today - timedelta(days=5)),
            "duration": 960,
        },
        {
            "name": "Upcoming milestone",
            "start_date": str(today + timedelta(days=4)),
            "duration": 0,
            "is_milestone": True,
        },
        {
            "name": "Not started task",
            "start_date": str(today + timedelta(days=1)),
            "duration": 480,
        },
    ]

    for payload in task_payloads:
        response = await client.post(
            f"/api/v1/projects/{project_id}/tasks", json=payload
        )
        assert response.status_code == 201, response.text

    tasks = list(
        (
            await session.execute(
                select(Task).where(Task.project_id == uuid.UUID(project_id))
            )
        ).scalars()
    )
    tasks_by_name = {task.name: task for task in tasks}

    tasks_by_name["Completed task"].percent_complete = 100
    tasks_by_name["Completed task"].finish_date = today - timedelta(days=7)
    tasks_by_name["Completed task"].total_cost = 2400
    tasks_by_name["Completed task"].actual_cost = 2400
    tasks_by_name["Completed task"].remaining_cost = 0

    tasks_by_name["Overdue critical task"].percent_complete = 25
    tasks_by_name["Overdue critical task"].finish_date = today - timedelta(days=2)
    tasks_by_name["Overdue critical task"].is_critical = True
    tasks_by_name["Overdue critical task"].total_cost = 3000
    tasks_by_name["Overdue critical task"].actual_cost = 1200
    tasks_by_name["Overdue critical task"].remaining_cost = 1800

    tasks_by_name["Upcoming milestone"].finish_date = today + timedelta(days=5)

    tasks_by_name["Not started task"].finish_date = today + timedelta(days=3)
    tasks_by_name["Not started task"].total_cost = 1200
    tasks_by_name["Not started task"].remaining_cost = 1200

    await session.commit()

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Lead Engineer", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    assignment_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{tasks_by_name['Overdue critical task'].id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.5,
            "start_date": str(today - timedelta(days=5)),
            "finish_date": str(today - timedelta(days=2)),
        },
    )
    assert assignment_response.status_code == 201, assignment_response.text

    return project_id


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
async def test_list_projects_rejects_unverified_user_after_grace_period(
    client: AsyncClient,
    session: AsyncSession,
):
    email = "list_proj_unverified_expired@x.com"

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Expired Project User",
        },
    )
    assert register_response.status_code == 201

    user = await auth_service.get_user_by_email(session, email)
    assert user is not None
    user.created_at = datetime.now(UTC) - timedelta(hours=25)
    await session.commit()

    response = await client.get("/api/v1/projects")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_VERIFICATION_REQUIRED"


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
async def test_create_project_rejects_unknown_settings_keys(client: AsyncClient):
    """Create rejects unknown project settings keys (422)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_set_inv@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj Set Inv",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Cr Proj Set Inv", "slug": "org-cr-proj-set-inv"},
    )
    org_id = org_resp.json()["id"]

    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "New Proj Invalid Settings",
            "organization_id": org_id,
            "start_date": "2024-05-01",
            "settings": {"evil_toggle": True},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_project_with_partial_settings_allows_task_create(
    client: AsyncClient,
):
    """
    Create - partial settings payload does not null-out required scheduling defaults.
    """
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_partial_set@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj Partial Set",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Partial Settings", "slug": "org-partial-settings"},
    )
    org_id = org_resp.json()["id"]

    project_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Partial Settings",
            "organization_id": org_id,
            "start_date": "2024-01-01",
            "settings": {"auto_calculate": False},
        },
    )
    assert project_resp.status_code == 201, project_resp.text
    project_id = project_resp.json()["id"]

    task_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"name": "Task from Partial Settings", "start_date": "2024-01-01"},
    )
    assert task_resp.status_code == 201, task_resp.text


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
async def test_update_project_rejects_unknown_settings_keys(client: AsyncClient):
    """Update rejects unknown project settings keys (422)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_set_inv@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Set Inv",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Set", "slug": "org-upd-set"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Set",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"settings": {"unexpected_key": "value"}},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project_accepts_kanban_wip_limits(client: AsyncClient):
    """Update accepts bounded kanban_wip_limits keys in settings payload."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_set_wip@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Set Wip",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Wip", "slug": "org-upd-wip"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Wip",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"settings": {"kanban_wip_limits": {"BACKLOG": 3, "TODO": 5}}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["settings"]["kanban_wip_limits"] == {"BACKLOG": 3, "TODO": 5}


@pytest.mark.asyncio
async def test_update_project_accepts_status_thresholds(client: AsyncClient):
    """Update accepts bounded status_thresholds keys in settings payload."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_set_status_threshold@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Set Threshold",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Threshold", "slug": "org-upd-threshold"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Threshold",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={
            "settings": {
                "status_thresholds": {
                    "IN_PROGRESS": 1,
                    "IN_REVIEW": 85,
                    "DONE": 100,
                }
            }
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["settings"]["status_thresholds"] == {
        "IN_PROGRESS": 1,
        "IN_REVIEW": 85,
        "DONE": 100,
    }


@pytest.mark.asyncio
async def test_update_project_merges_partial_settings_patch(client: AsyncClient):
    """Update settings with one key preserves existing settings keys."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_set_merge@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Set Merge",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Merge", "slug": "org-upd-merge"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Merge",
            "organization_id": org_id,
            "start_date": "2024-01-01",
            "settings": {
                "auto_calculate": False,
                "status_thresholds": {
                    "IN_PROGRESS": 1,
                    "IN_REVIEW": 85,
                    "DONE": 100,
                },
            },
        },
    )
    assert proj_resp.status_code == 201, proj_resp.text
    proj_id = proj_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"settings": {"auto_calculate": True}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["settings"]["auto_calculate"] is True
    assert response.json()["settings"]["status_thresholds"] == {
        "IN_PROGRESS": 1,
        "IN_REVIEW": 85,
        "DONE": 100,
    }


@pytest.mark.asyncio
async def test_update_project_rejects_in_review_threshold_of_100(client: AsyncClient):
    """Update rejects IN_REVIEW threshold >= 100 (422)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_set_status_threshold_invalid@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Set Threshold Invalid",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Threshold Invalid", "slug": "org-upd-threshold-invalid"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Threshold Invalid",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={
            "settings": {
                "status_thresholds": {
                    "IN_PROGRESS": 1,
                    "IN_REVIEW": 100,
                    "DONE": 100,
                }
            }
        },
    )
    assert response.status_code == 422


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
async def test_create_project_rejects_overlong_description_and_color(
    client: AsyncClient,
):
    """Create — overlong description/color — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_proj_len@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr Proj Len",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Len", "slug": "org-proj-len"}
    )
    org_id = org_resp.json()["id"]

    overlong_description = "x" * 4001
    overlong_color = "c" * 33

    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Too Long",
            "organization_id": org_id,
            "start_date": "2024-01-01",
            "description": overlong_description,
            "color": overlong_color,
        },
    )
    assert response.status_code == 422


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


@pytest.mark.asyncio
async def test_update_project_rejects_unknown_patch_field(client: AsyncClient):
    """Update â€” unknown patch field â€” returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_unknown@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Unknown",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Unknown", "slug": "org-upd-unknown"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Unknown",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"unknown_patch_field": "value"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_project_rejects_overlong_description_and_color(
    client: AsyncClient,
):
    """Update — overlong description/color — returns 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_proj_len@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Proj Len",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd Len", "slug": "org-upd-proj-len"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Len",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    overlong_description = "x" * 4001
    overlong_color = "c" * 33

    description_response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"description": overlong_description},
    )
    assert description_response.status_code == 422

    color_response = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"color": overlong_color},
    )
    assert color_response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_returns_full_shape(
    client: AsyncClient,
    session: AsyncSession,
):
    project_id = await _seed_project_dashboard_data(
        client,
        session,
        email="proj_dash_owner@x.com",
        slug="org-proj-dash",
    )

    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert sorted(data) == [
        "cost",
        "critical_path",
        "overdue_tasks",
        "recent_activity",
        "resources",
        "schedule",
        "summary",
        "upcoming_milestones",
    ]
    assert data["summary"]["total_tasks"] == 4
    assert data["summary"]["completed_tasks"] == 1
    assert data["summary"]["in_progress_tasks"] == 1
    assert data["summary"]["not_started_tasks"] == 2
    assert data["summary"]["overdue_tasks"] == 1
    assert data["summary"]["milestones"] == 1
    assert data["resources"]["overallocated_count"] == 1
    assert data["critical_path"]["task_count"] == 1
    assert "path_length_days" in data["critical_path"]
    assert data["cost"]["budget"] == 15000.0
    assert len(data["upcoming_milestones"]) == 1
    assert len(data["overdue_tasks"]) == 1


@pytest.mark.asyncio
async def test_dashboard_requires_auth(
    client: AsyncClient,
    session: AsyncSession,
):
    project_id = await _seed_project_dashboard_data(
        client,
        session,
        email="proj_dash_auth@x.com",
        slug="org-proj-dash-auth",
    )

    client.cookies.clear()
    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_forbidden_for_non_member(
    client: AsyncClient,
    session: AsyncSession,
):
    project_id = await _seed_project_dashboard_data(
        client,
        session,
        email="proj_dash_owner2@x.com",
        slug="org-proj-dash-owner2",
    )

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "proj_dash_intruder@x.com",
            "password": "StrongPassword123!",
            "full_name": "Intruder",
        },
    )
    assert register_response.status_code == 201, register_response.text

    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")
    assert response.status_code == 403

    random_project = str(uuid.uuid4())
    random_response = await client.get(f"/api/v1/projects/{random_project}/dashboard")
    assert random_response.status_code in (403, 404)


@pytest.mark.asyncio
async def test_dashboard_custom_window_validation(
    client: AsyncClient,
    session: AsyncSession,
):
    project_id = await _seed_project_dashboard_data(
        client,
        session,
        email="proj_dash_window@x.com",
        slug="org-proj-dash-window",
    )

    missing_dates = await client.get(
        f"/api/v1/projects/{project_id}/dashboard",
        params={"window_preset": "custom"},
    )
    assert missing_dates.status_code == 422

    invalid_range = await client.get(
        f"/api/v1/projects/{project_id}/dashboard",
        params={
            "window_preset": "custom",
            "start_date": "2026-04-02",
            "end_date": "2026-04-01",
        },
    )
    assert invalid_range.status_code == 422
