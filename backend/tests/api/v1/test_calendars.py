import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_calendars_success(client: AsyncClient):
    """List — success — returns project calendars (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_list_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal List O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal List", "slug": "org-cal-list"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal List",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    # Create calendar
    await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Night Shift"},
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/calendars")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Night Shift" in names


@pytest.mark.asyncio
async def test_create_calendar_success(client: AsyncClient):
    """Create — success (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_cr_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal Cr O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal Cr", "slug": "org-cal-cr"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal Cr",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Custom Calendar", "is_base": False},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Calendar"
    assert data["project_id"] == proj_id
    # Default work week should be set
    assert data["work_week"] is not None
    assert len(data["work_week"]) == 7


@pytest.mark.asyncio
async def test_create_calendar_custom_work_week(client: AsyncClient):
    """Create — with custom work week (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_cww@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal CWW",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal CWW", "slug": "org-cal-cww"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal CWW",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    custom_week = [
        None,  # Sunday
        {"start": "08:00", "end": "16:00", "breaks": []},
        {"start": "08:00", "end": "16:00", "breaks": []},
        {"start": "08:00", "end": "16:00", "breaks": []},
        {"start": "08:00", "end": "16:00", "breaks": []},
        {"start": "08:00", "end": "16:00", "breaks": []},
        None,  # Saturday
    ]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Early Shift", "work_week": custom_week},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["work_week"][1]["start"] == "08:00"


@pytest.mark.asyncio
async def test_get_calendar_success(client: AsyncClient):
    """Get — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_get_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal Get O",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal Get", "slug": "org-cal-get"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal Get",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Get Me"},
    )
    cal_id = c_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{proj_id}/calendars/{cal_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cal_id


@pytest.mark.asyncio
async def test_get_calendar_not_found(client: AsyncClient):
    """Get — non-existent — 404."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal NF",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal NF", "slug": "org-cal-nf"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal NF",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    rand_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/projects/{proj_id}/calendars/{rand_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_calendar_success(client: AsyncClient):
    """Update — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_upd@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal Upd",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal Upd", "slug": "org-cal-upd"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal Upd",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Old Name"},
    )
    cal_id = c_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}",
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_calendar_success(client: AsyncClient):
    """Delete — success (204)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cal_del@x.com",
            "password": "StrongPassword123!",
            "full_name": "Cal Del",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Cal Del", "slug": "org-cal-del"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Cal Del",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    c_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Delete Me"},
    )
    cal_id = c_resp.json()["id"]

    resp = await client.delete(f"/api/v1/projects/{proj_id}/calendars/{cal_id}")
    assert resp.status_code == 204

    # Confirm gone
    get_resp = await client.get(f"/api/v1/projects/{proj_id}/calendars/{cal_id}")
    assert get_resp.status_code == 404


# ── Calendar Exception Tests ──


@pytest.mark.asyncio
async def test_create_exception_success(client: AsyncClient):
    """Create exception — success (201)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "exc_cr@x.com",
            "password": "StrongPassword123!",
            "full_name": "Exc Cr",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Exc Cr", "slug": "org-exc-cr"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Exc Cr",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    cal_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Cal With Exc"},
    )
    cal_id = cal_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions",
        json={
            "name": "Christmas",
            "start_date": "2024-12-25",
            "end_date": "2024-12-25",
            "is_working": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Christmas"
    assert data["is_working"] is False


@pytest.mark.asyncio
async def test_list_exceptions_success(client: AsyncClient):
    """List exceptions — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "exc_list@x.com",
            "password": "StrongPassword123!",
            "full_name": "Exc List",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Exc List", "slug": "org-exc-list"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Exc List",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    cal_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Cal Exc List"},
    )
    cal_id = cal_resp.json()["id"]

    # Create 2 exceptions
    await client.post(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions",
        json={
            "name": "New Year",
            "start_date": "2024-01-01",
            "end_date": "2024-01-01",
        },
    )
    await client.post(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions",
        json={
            "name": "Easter",
            "start_date": "2024-03-31",
            "end_date": "2024-04-01",
        },
    )

    resp = await client.get(f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions")
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()]
    assert "New Year" in names
    assert "Easter" in names


@pytest.mark.asyncio
async def test_update_exception_success(client: AsyncClient):
    """Update exception — success (200)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "exc_upd@x.com",
            "password": "StrongPassword123!",
            "full_name": "Exc Upd",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Exc Upd", "slug": "org-exc-upd"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Exc Upd",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    cal_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Cal Exc Upd"},
    )
    cal_id = cal_resp.json()["id"]

    exc_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions",
        json={
            "name": "Old Holiday",
            "start_date": "2024-06-01",
            "end_date": "2024-06-01",
        },
    )
    exc_id = exc_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions/{exc_id}",
        json={"name": "Updated Holiday"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Holiday"


@pytest.mark.asyncio
async def test_delete_exception_success(client: AsyncClient):
    """Delete exception — success (204)."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "exc_del@x.com",
            "password": "StrongPassword123!",
            "full_name": "Exc Del",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org Exc Del", "slug": "org-exc-del"}
    )
    org_id = org_resp.json()["id"]
    proj_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "Proj Exc Del",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    proj_id = proj_resp.json()["id"]

    cal_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars",
        json={"name": "Cal Exc Del"},
    )
    cal_id = cal_resp.json()["id"]

    exc_resp = await client.post(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions",
        json={
            "name": "Delete Me",
            "start_date": "2024-07-04",
            "end_date": "2024-07-04",
        },
    )
    exc_id = exc_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/projects/{proj_id}/calendars/{cal_id}/exceptions/{exc_id}"
    )
    assert resp.status_code == 204
