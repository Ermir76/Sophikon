import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.project_members import add_project_member


@pytest.mark.asyncio
async def test_list_tasks_success(client: AsyncClient):
    """List — success — ordered by order_index (200)."""
    # Setup
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_t@x.com",
            "password": "StrongPassword123!",
            "full_name": "List T",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org List T", "slug": "org-list-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj List T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create Tasks (order handled by backend or default)
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 2", "start_date": "2024-01-01", "duration": 480},
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert items[0]["name"] == "Task 1"
    assert items[1]["name"] == "Task 2"


@pytest.mark.asyncio
async def test_create_task_inclusive_finish_date_when_auto_calculate_disabled(
    client: AsyncClient,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "create-inclusive-finish@x.com",
            "password": "StrongPassword123!",
            "full_name": "Create Inclusive Finish",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inclusive", "slug": "org-inclusive-finish"},
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Inclusive",
            "organization_id": org_id,
            "start_date": "2024-01-01",
            "settings": {"auto_calculate": False},
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "One Day Task", "start_date": "2024-01-01", "duration": 480},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["start_date"] == "2024-01-01"
    assert payload["finish_date"] == "2024-01-01"


@pytest.mark.asyncio
async def test_list_tasks_excludes_deleted(client: AsyncClient):
    """List — excludes soft-deleted by default."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_del_def@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Del Def",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Def", "slug": "org-del-def"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Def",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create & Delete
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task Del", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks")
    assert len(resp.json()["items"]) == 0


@pytest.mark.asyncio
async def test_list_tasks_include_deleted_owner(client: AsyncClient):
    """List — include_deleted=true — owner can see."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_inc_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Inc O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Inc O", "slug": "org-inc-o"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Inc O",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task Del", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?include_deleted=true")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_tasks_include_deleted_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """List — include_deleted=true — member returns 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_inc_fo@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Inc FO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Inc FO", "slug": "org-inc-fo"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Inc FO",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_inc_fu@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Inc FU",
        },
    )
    await add_project_member(session, proj_id, "list_inc_fu@x.com", "member")

    # Login Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": "list_inc_fu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?include_deleted=true")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_tasks_pagination(client: AsyncClient):
    """List — pagination."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_pag_t@x.com",
            "password": "StrongPassword123!",
            "full_name": "List Pag T",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Pag T", "slug": "org-pag-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Pag T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create 3 tasks
    for i in range(3):
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": f"Task {i}", "start_date": "2024-01-01", "duration": 480},
        )

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks?page=1&per_page=2")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 2

    resp2 = await client.get(f"/api/v1/projects/{proj_id}/tasks?page=2&per_page=2")
    assert len(resp2.json()["items"]) == 1


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient):
    """Create — success — auto WBS and order_index."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Ok",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr T", "slug": "org-cr-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "New Task", "start_date": "2024-01-01", "duration": 480},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["wbs_code"] == "1"
    assert data["order_index"] == 1


@pytest.mark.asyncio
async def test_create_task_with_parent(client: AsyncClient):
    """Create — with parent — sets outline level/WBS."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_par@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Par",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Par T", "slug": "org-par-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Par T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Parent
    p_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
    )
    parent_id = p_resp.json()["id"]

    # Child
    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Child",
            "start_date": "2024-01-01",
            "duration": 480,
            "parent_task_id": parent_id,
        },
    )
    assert c_resp.status_code == 201
    data = c_resp.json()
    assert data["wbs_code"] == "1.1"
    assert data["outline_level"] == 2


@pytest.mark.asyncio
async def test_create_task_invalid_parent(client: AsyncClient):
    """Create — invalid parent (not in project) — 400."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_inv_p@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Inv P",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Inv P", "slug": "org-inv-p"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Inv P",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Bad Parent",
            "start_date": "2024-01-01",
            "duration": 480,
            "parent_task_id": rand_id,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_create_task_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Create — viewer role — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cr TV", "slug": "org-cr-tv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cr TV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T VU",
        },
    )
    await add_project_member(session, proj_id, "cr_t_vu@x.com", "viewer")

    # Login Viewer
    await client.post(
        "/api/v1/auth/login",
        json={"email": "cr_t_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Viewer Task", "start_date": "2024-01-01", "duration": 480},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_task_missing_fields(client: AsyncClient):
    """Create — missing required fields — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_miss@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Miss",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org T Miss", "slug": "org-t-miss"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj T Miss",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Missing name
    resp1 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"start_date": "2024-01-01", "duration": 480},
    )
    assert resp1.status_code == 422

    # Missing start_date
    resp2 = await client.post(
        f"/api/v1/projects/{proj_id}/tasks", json={"name": "No Date", "duration": 480}
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_duration(client: AsyncClient):
    """Create — invalid duration (negative) — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_dur@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Dur",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org T Dur", "slug": "org-t-dur"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj T Dur",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Neg Dur", "start_date": "2024-01-01", "duration": -10},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_priority(client: AsyncClient):
    """Create — invalid priority (outside 0-1000) — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_prio@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Prio",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org T Prio", "slug": "org-t-prio"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj T Prio",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Bad Prio",
            "start_date": "2024-01-01",
            "duration": 480,
            "priority": 1001,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_task_rejects_overlong_notes_and_color(client: AsyncClient):
    """Create — overlong notes/color — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cr_t_len@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cr T Len",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org T Len", "slug": "org-t-len"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj T Len",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={
            "name": "Too Long Task",
            "start_date": "2024-01-01",
            "duration": 480,
            "notes": "n" * 5001,
            "color": "c" * 33,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_success(client: AsyncClient):
    """Get — success — returns task (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_t_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get T Ok",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Get T", "slug": "org-get-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Get T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_deleted(client: AsyncClient):
    """Get — deleted task — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_t_del@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get T Del",
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

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task Del", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]
    await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")

    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient):
    """Get — non-existent ID — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_t_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Get T NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Get NF", "slug": "org-get-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Get NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/projects/{proj_id}/tasks/{rand_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_task_success(client: AsyncClient):
    """Update — success — partial update (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T Ok",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd T", "slug": "org-upd-t"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd T",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_task_syncs_duration_progress_fields(client: AsyncClient):
    """Update — leaf task keeps actual/remaining duration in sync."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_dur@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T Dur",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Dur", "slug": "org-upd-dur"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Dur",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    task = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()
    task_id = task["id"]
    assert task["actual_duration"] == 0
    assert task["remaining_duration"] == 480

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"percent_complete": 25}
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["actual_duration"] == 120
    assert updated["remaining_duration"] == 360

    resp2 = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"duration": 600}
    )
    assert resp2.status_code == 200
    updated2 = resp2.json()
    assert updated2["actual_duration"] == 150
    assert updated2["remaining_duration"] == 450


@pytest.mark.asyncio
async def test_update_task_rejects_overlong_notes_and_color(client: AsyncClient):
    """Update — overlong notes/color — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_len@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T Len",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd TL", "slug": "org-upd-t-len"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd TL",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    task_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task Len", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = task_resp.json()["id"]

    notes_response = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}",
        json={"notes": "n" * 5001},
    )
    assert notes_response.status_code == 422

    color_response = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}",
        json={"color": "c" * 33},
    )
    assert color_response.status_code == 422


@pytest.mark.asyncio
async def test_update_task_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Update — viewer role — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd TV", "slug": "org-upd-tv"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd TV",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T VU",
        },
    )
    await add_project_member(session, proj_id, "upd_t_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "upd_t_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"name": "Fail"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_task_invalid_percent(client: AsyncClient):
    """Update — invalid percent_complete (>100) — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_pct@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T Pct",
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
    task_id = t_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{task_id}", json={"percent_complete": 101}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_task_rejects_computed_fields_on_summary_task(client: AsyncClient):
    """Update — summary rollup fields are read-only — 422."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_sum@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T Sum",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Upd Sum", "slug": "org-upd-sum"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Upd Sum",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    parent_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "Parent", "start_date": "2024-01-01", "duration": 480},
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

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/tasks/{parent_id}",
        json={"duration": 999},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "auto-calculate duration" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient):
    """Update — non-existent task — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_t_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Upd T NF",
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
        f"/api/v1/projects/{proj_id}/tasks/{rand_id}", json={"name": "Fail"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_success_owner(client: AsyncClient):
    """Delete — success — owner (204)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_own@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T Own",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del Own", "slug": "org-del-own"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del Own",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 204

    # Check deleted
    resp2 = await client.get(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_success_manager(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — success — manager (204)."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_mo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T MO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del MO", "slug": "org-del-mo"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del MO",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    # Manager
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_mu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T MU",
        },
    )
    await add_project_member(session, proj_id, "del_t_mu@x.com", "manager")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_t_mu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_task_member_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — member role — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_fo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T FO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del FO", "slug": "org-del-fo"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del FO",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    # Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_fu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T FU",
        },
    )
    await add_project_member(session, proj_id, "del_t_fu@x.com", "member")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_t_fu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_task_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Delete — viewer role — 403."""
    # Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_vo@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T VO",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Del VO", "slug": "org-del-vo"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Del VO",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]
    t_resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "Task 1", "start_date": "2024-01-01", "duration": 480},
    )
    task_id = t_resp.json()["id"]

    # Viewer
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_t_vu@x.com",
            "password": "StrongPassword123!",
            "full_name": "Del T VU",
        },
    )
    await add_project_member(session, proj_id, "del_t_vu@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "del_t_vu@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.delete(f"/api/v1/projects/{proj_id}/tasks/{task_id}")
    assert resp.status_code == 403


# --- Indent Tests ---


@pytest.mark.asyncio
async def test_indent_task_success(client: AsyncClient):
    """Indent — success — task becomes child of previous sibling."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ind_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "Ind Ok",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Ind", "slug": "org-ind"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Ind",
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

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/indent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["parent_task_id"] == t1_id
    assert data["wbs_code"] == "1.1"


@pytest.mark.asyncio
async def test_indent_first_task(client: AsyncClient):
    """Indent — first task — 400."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ind_first@x.com",
            "password": "StrongPassword123!",
            "full_name": "Ind First",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Ind F", "slug": "org-ind-f"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Ind F",
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

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t1_id}/indent")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_indent_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Indent — viewer role — 403."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ind_v_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Ind VO",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Ind V", "slug": "org-ind-v"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Ind V",
                "organization_id": org_id,
                "start_date": "2024-01-01",
            },
        )
    ).json()["id"]

    await client.post(
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T1", "start_date": "2024-01-01", "duration": 480},
    )
    t2_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ind_v_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Ind VU",
        },
    )
    await add_project_member(session, proj_id, "ind_v_u@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "ind_v_u@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/indent")
    assert resp.status_code == 403


# --- Outdent Tests ---


@pytest.mark.asyncio
async def test_outdent_task_success(client: AsyncClient):
    """Outdent — success."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "out_ok@x.com",
            "password": "StrongPassword123!",
            "full_name": "Out Ok",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Out", "slug": "org-out"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Out",
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
            json={
                "name": "T2",
                "start_date": "2024-01-01",
                "duration": 480,
                "parent_task_id": t1_id,
            },
        )
    ).json()["id"]

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/outdent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["parent_task_id"] is None
    assert data["wbs_code"] == "2"


@pytest.mark.asyncio
async def test_outdent_root_task(client: AsyncClient):
    """Outdent — root task — 400."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "out_root@x.com",
            "password": "StrongPassword123!",
            "full_name": "Out Root",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Out R", "slug": "org-out-r"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Out R",
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

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t1_id}/outdent")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_outdent_viewer_forbidden(
    client: AsyncClient, session: AsyncSession, setup_roles
):
    """Outdent — viewer role — 403."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "out_v_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Out VO",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Out V", "slug": "org-out-v"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Out V",
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
            json={
                "name": "T2",
                "start_date": "2024-01-01",
                "duration": 480,
                "parent_task_id": t1_id,
            },
        )
    ).json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "out_v_u@x.com",
            "password": "StrongPassword123!",
            "full_name": "Out VU",
        },
    )
    await add_project_member(session, proj_id, "out_v_u@x.com", "viewer")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "out_v_u@x.com", "password": "StrongPassword123!"},
    )

    resp = await client.post(f"/api/v1/projects/{proj_id}/tasks/{t2_id}/outdent")
    assert resp.status_code == 403


# --- Reorder Tests ---


@pytest.mark.asyncio
async def test_reorder_task_after(client: AsyncClient):
    """Reorder — with after_task_id."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reo_aft@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Aft",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Reo A", "slug": "org-reo-a"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo A",
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
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    t3_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T3", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t3_id}/reorder",
        json={"after_task_id": t1_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_index"] == 2
    assert data["wbs_code"] == "2"


@pytest.mark.asyncio
async def test_reorder_task_before(client: AsyncClient):
    """Reorder — with before_task_id."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reo_bef@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Bef",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Reo B", "slug": "org-reo-b"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo B",
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
        f"/api/v1/projects/{proj_id}/tasks",
        json={"name": "T2", "start_date": "2024-01-01", "duration": 480},
    )
    t3_id = (
        await client.post(
            f"/api/v1/projects/{proj_id}/tasks",
            json={"name": "T3", "start_date": "2024-01-01", "duration": 480},
        )
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t3_id}/reorder",
        json={"before_task_id": t1_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_index"] == 1
    assert data["wbs_code"] == "1"


@pytest.mark.asyncio
async def test_reorder_task_new_parent(client: AsyncClient):
    """Reorder — with new_parent_id."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reo_par@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Par",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Reo P", "slug": "org-reo-p"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo P",
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

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t2_id}/reorder",
        json={"new_parent_id": t1_id},
    )
    assert resp.status_code == 200
    assert resp.json()["parent_task_id"] == t1_id


@pytest.mark.asyncio
async def test_reorder_descendant(client: AsyncClient):
    """Reorder — to descendant (400)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reo_desc@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Desc",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org Reo D", "slug": "org-reo-d"}
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo D",
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
            json={
                "name": "T2",
                "start_date": "2024-01-01",
                "duration": 480,
                "parent_task_id": t1_id,
            },
        )
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t1_id}/reorder",
        json={"new_parent_id": t2_id},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_reorder_both_after_before(client: AsyncClient):
    """Reorder — with both after_task_id and before_task_id (422)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reo_both@x.com",
            "password": "StrongPassword123!",
            "full_name": "Reo Both",
        },
    )
    org_id = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Org Reo Both", "slug": "org-reo-both"},
        )
    ).json()["id"]
    proj_id = (
        await client.post(
            "/api/v1/projects",
            json={
                "name": "Proj Reo Both",
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

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/tasks/{t2_id}/reorder",
        json={"after_task_id": t1_id, "before_task_id": t1_id},
    )
    assert resp.status_code == 422
