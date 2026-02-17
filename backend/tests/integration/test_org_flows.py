import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_org_invite_visibility(client: AsyncClient):
    """
    Integration: User A creates Org -> Invites User B -> User B sees the Org.
    """
    # 1. Register User A
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "org_flow_a@example.com",
            "password": "StrongPassword123!",
            "full_name": "Org Flow A",
        },
    )
    # 2. Create Org
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Flow Shared", "slug": "org-flow-shared"},
    )
    org_id = org_resp.json()["id"]

    # 3. Register User B
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "org_flow_b@example.com",
            "password": "StrongPassword123!",
            "full_name": "Org Flow B",
        },
    )

    # 4. Login User A (to invite)
    await client.post(
        "/api/v1/auth/login",
        json={"email": "org_flow_a@example.com", "password": "StrongPassword123!"},
    )

    # 5. Invite User B
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "org_flow_b@example.com", "role": "member"},
    )

    # 6. Login User B
    await client.post(
        "/api/v1/auth/login",
        json={"email": "org_flow_b@example.com", "password": "StrongPassword123!"},
    )

    # 7. List Orgs for User B
    list_resp = await client.get("/api/v1/organizations")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]

    # Verify User B sees the org
    org_ids = [o["id"] for o in items]
    assert org_id in org_ids


@pytest.mark.asyncio
async def test_remove_member_visibility(client: AsyncClient):
    """
    Integration: Remove Member -> Member no longer sees the Org.
    """
    # 1. Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_vis_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Vis Owner",
        },
    )
    org_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Vis", "slug": "org-rem-vis"},
    )
    org_id = org_resp.json()["id"]

    # 2. Register Victim
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_vis_victim@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Vis Victim",
        },
    )

    # 3. Login Owner -> Invite Victim
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_vis_owner@example.com", "password": "StrongPassword123!"},
    )
    inv_resp = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "rem_vis_victim@example.com", "role": "member"},
    )
    member_id = inv_resp.json()["id"]

    # 4. Remove Victim
    await client.delete(f"/api/v1/organizations/{org_id}/members/{member_id}")

    # 5. Login Victim
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_vis_victim@example.com", "password": "StrongPassword123!"},
    )

    # 6. List Orgs
    list_resp = await client.get("/api/v1/organizations")
    items = list_resp.json()["items"]

    # Verify Org is GONE
    org_ids = [o["id"] for o in items]
    assert org_id not in org_ids
