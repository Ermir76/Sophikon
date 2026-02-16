import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_organizations_success(client: AsyncClient):
    """
    List — success — returns only orgs user belongs to (200).
    Scenario:
    1. Register User A.
    2. User A creates 'Org A'.
    3. User A lists orgs. Should see 'Org A' (plus personal org).
    4. Register User B.
    5. User B lists orgs. Should NOT see 'Org A'.
    """
    # 1. Register User A
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userA_list@example.com",
            "password": "StrongPassword123!",
            "full_name": "User A List",
        },
    )

    # 2. Create Org A
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org A", "slug": "org-a-list"},
    )
    assert create_resp.status_code == 201

    # 3. List orgs for User A
    list_resp = await client.get("/api/v1/organizations")
    assert list_resp.status_code == 200
    data = list_resp.json()
    items = data["items"]
    # Check "Org A" is present
    found = any(o["slug"] == "org-a-list" for o in items)
    assert found
    # Check personal org is present
    found_personal = any(o["is_personal"] is True for o in items)
    assert found_personal

    # 4. Register User B (Login User B)
    # Logout first or just overwrite cookie? Register overwrites cookie.
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userB_list@example.com",
            "password": "StrongPassword123!",
            "full_name": "User B List",
        },
    )

    # 5. List orgs for User B
    list_resp_b = await client.get("/api/v1/organizations")
    assert list_resp_b.status_code == 200
    items_b = list_resp_b.json()["items"]

    # Should NOT see "Org A" (slug="org-a-list")
    found_b = any(o["slug"] == "org-a-list" for o in items_b)
    assert not found_b
    # Should see their own personal org
    assert any(o["is_personal"] is True for o in items_b)


@pytest.mark.asyncio
async def test_list_organizations_pagination(client: AsyncClient):
    """List — pagination — page and per_page work correctly."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "pag_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Pag User",
        },
    )

    # Create 5 orgs
    for i in range(5):
        await client.post(
            "/api/v1/organizations",
            json={"name": f"Org {i}", "slug": f"org-pag-{i}"},
        )

    # List page 1, per_page 2
    resp1 = await client.get("/api/v1/organizations?page=1&per_page=2")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["items"]) == 2
    assert data1["total"] >= 6  # 5 created + 1 personal

    # List page 2, per_page 2
    resp2 = await client.get("/api/v1/organizations?page=2&per_page=2")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["items"]) == 2

    # Verify items are different (assuming ordering by created_at desc)
    ids1 = {item["id"] for item in data1["items"]}
    ids2 = {item["id"] for item in data2["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_list_organizations_unauthenticated(client: AsyncClient):
    """List — unauthenticated — returns 401."""
    # Ensure no auth cookie
    client.cookies.delete("access_token")

    response = await client.get("/api/v1/organizations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_organization_success(client: AsyncClient):
    """Create — success — creates org, makes user owner (201)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "create_success@example.com",
            "password": "StrongPassword123!",
            "full_name": "Create Success",
        },
    )

    response = await client.post(
        "/api/v1/organizations",
        json={"name": "New Org", "slug": "new-org-success"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Org"
    assert data["slug"] == "new-org-success"
    assert data["id"] is not None

    # Verify owner role via GET detail? Or assume create implies owner on strict REST?
    # Test plan says "makes user owner".
    # We can verify by trying to UPDATE it (only owner can).

    org_id = data["id"]
    update_resp = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Updated Org"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Org"


@pytest.mark.asyncio
async def test_create_organization_duplicate_slug(client: AsyncClient):
    """Create — duplicate slug — returns 409."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup_slug@example.com",
            "password": "StrongPassword123!",
            "full_name": "Dup Slug",
        },
    )

    # Create first
    await client.post(
        "/api/v1/organizations",
        json={"name": "Org 1", "slug": "dup-slug"},
    )

    # Create second with same slug
    response = await client.post(
        "/api/v1/organizations",
        json={"name": "Org 2", "slug": "dup-slug"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_organization_missing_fields(client: AsyncClient):
    """Create — missing required fields — returns 422."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "missing_fields@example.com",
            "password": "StrongPassword123!",
            "full_name": "Missing Fields",
        },
    )

    # Missing name
    resp1 = await client.post(
        "/api/v1/organizations",
        json={"slug": "no-name"},
    )
    assert resp1.status_code == 422

    # Missing slug
    resp2 = await client.post(
        "/api/v1/organizations",
        json={"name": "No Slug"},
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_create_organization_invalid_slug(client: AsyncClient):
    """Create — invalid slug format — returns 422."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid_slug@example.com",
            "password": "StrongPassword123!",
            "full_name": "Invalid Slug",
        },
    )

    # Space in slug
    resp1 = await client.post(
        "/api/v1/organizations",
        json={"name": "Bad Slug 1", "slug": "space slug"},
    )
    assert resp1.status_code == 422

    # Uppercase in slug
    resp2 = await client.post(
        "/api/v1/organizations",
        json={"name": "Bad Slug 2", "slug": "Upper-Slug"},
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_create_organization_unauthenticated(client: AsyncClient):
    """Create — unauthenticated — returns 401."""
    client.cookies.delete("access_token")
    response = await client.post(
        "/api/v1/organizations",
        json={"name": "Unauth Org", "slug": "unauth-org"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_organization_success(client: AsyncClient):
    """Get — success — returns org details for member (200)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "get_success@example.com",
            "password": "StrongPassword123!",
            "full_name": "Get Success",
        },
    )

    # Create org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Get Org", "slug": "get-org"},
    )
    org_id = create_resp.json()["id"]

    # Get org
    response = await client.get(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == org_id
    assert data["name"] == "Get Org"
    assert "settings" in data


@pytest.mark.asyncio
async def test_get_organization_non_member(client: AsyncClient):
    """Get — non-member — returns 403."""
    # 1. Register User A (Owner)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner_get@example.com",
            "password": "StrongPassword123!",
            "full_name": "Owner Get",
        },
    )
    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Private Org", "slug": "private-org"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register/Login as User B (Non-member)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder_get@example.com",
            "password": "StrongPassword123!",
            "full_name": "Intruder Get",
        },
    )

    # Try to access Org
    response = await client.get(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 403
    assert "do not have access" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_organization_deleted(client: AsyncClient):
    """Get — deleted org — returns 404."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_get@example.com",
            "password": "StrongPassword123!",
            "full_name": "Delete Get",
        },
    )

    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "To Delete", "slug": "to-delete-get"},
    )
    org_id = create_resp.json()["id"]

    # Delete Org
    # (Checking DELETE endpoint implicitly here, assuming it works or verifying later)
    del_resp = await client.delete(f"/api/v1/organizations/{org_id}")
    assert del_resp.status_code == 204

    # Try get
    response = await client.get(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 404
    assert "Organization not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_organization_not_found(client: AsyncClient):
    """Get — non-existent org ID — returns 404."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not_found@example.com",
            "password": "StrongPassword123!",
            "full_name": "Not Found",
        },
    )

    random_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/organizations/{random_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_organization_success(client: AsyncClient):
    """Update — success — owner can update name/slug (200)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "update_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "Update Owner",
        },
    )

    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Old Name", "slug": "old-slug"},
    )
    org_id = create_resp.json()["id"]

    # Update
    response = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "New Name", "slug": "new-slug"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["slug"] == "new-slug"


@pytest.mark.asyncio
async def test_update_organization_non_owner(client: AsyncClient):
    """Update — non-owner — returns 403. Tests as non-member (returns 403 from membership check)."""
    # Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner_upd@example.com",
            "password": "StrongPassword123!",
            "full_name": "Owner Upd",
        },
    )
    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Upd", "slug": "org-upd"},
    )
    org_id = create_resp.json()["id"]

    # Register Intruder
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "intruder_upd@example.com",
            "password": "StrongPassword123!",
            "full_name": "Intruder Upd",
        },
    )

    # Try Update
    response = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Hacked Name"},
    )
    # This will likely return 403 "You do not have access" (get_org_membership_or_404)
    # Not "Owner role required". But still 403.
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_organization_duplicate_slug(client: AsyncClient):
    """Update — duplicate slug — returns 409."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup_upd@example.com",
            "password": "StrongPassword123!",
            "full_name": "Dup Upd",
        },
    )

    # Create Org 1
    await client.post(
        "/api/v1/organizations",
        json={"name": "Org 1", "slug": "slug-one"},
    )

    # Create Org 2
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org 2", "slug": "slug-two"},
    )
    org_id_2 = create_resp.json()["id"]

    # Update Org 2 to slug-one
    response = await client.patch(
        f"/api/v1/organizations/{org_id_2}",
        json={"slug": "slug-one"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_organization_invalid_slug(client: AsyncClient):
    """Update — invalid slug format — returns 422."""
    # Register/Create
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upd_slug_inv@example.com",
            "password": "StrongPassword123!",
            "full_name": "Upd Slug Inv",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv", "slug": "slug-valid"},
    )
    org_id = create_resp.json()["id"]

    # Update with Space
    resp1 = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"slug": "space slug"},
    )
    assert resp1.status_code == 422

    # Update with Uppercase
    resp2 = await client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"slug": "Upper-Slug"},
    )
    assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_delete_organization_success(client: AsyncClient):
    """Delete — success — owner can soft delete org (204)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_success@example.com",
            "password": "StrongPassword123!",
            "full_name": "Del Success",
        },
    )
    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "To Delete", "slug": "to-delete-success"},
    )
    org_id = create_resp.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 204

    # Verify deleted (404 on get)
    get_resp = await client.get(f"/api/v1/organizations/{org_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_organization_non_owner(client: AsyncClient):
    """Delete — non-owner — returns 403."""
    # Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "Del Owner",
        },
    )
    # Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Secure Org", "slug": "secure-org"},
    )
    org_id = create_resp.json()["id"]

    # Register Intruder
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_intruder@example.com",
            "password": "StrongPassword123!",
            "full_name": "Del Intruder",
        },
    )

    # Try Delete
    response = await client.delete(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_personal_organization(client: AsyncClient):
    """Delete — personal org — returns 400 (cannot delete personal org)."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "del_personal@example.com",
            "password": "StrongPassword123!",
            "full_name": "Del Personal",
        },
    )

    # Find personal org
    # Assuming list returns it
    list_resp = await client.get("/api/v1/organizations")
    items = list_resp.json()["items"]
    # Usually the first one is personal, or check is_personal
    personal_org = next((o for o in items if o.get("is_personal")), None)

    assert personal_org is not None, "Personal org should be created on registration"

    org_id = personal_org["id"]
    response = await client.delete(f"/api/v1/organizations/{org_id}")
    assert response.status_code == 400
    assert "Cannot delete personal organization" in response.json()["detail"]
