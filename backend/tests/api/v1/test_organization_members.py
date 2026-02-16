import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_my_membership_success(client: AsyncClient):
    """Get my membership — success — returns role (200)."""
    # 1. Register User
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "my_mem_success@example.com",
            "password": "StrongPassword123!",
            "full_name": "My Mem Success",
        },
    )
    # 2. Create Org (User becomes owner)
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org My Mem", "slug": "org-my-mem-success"},
    )
    org_id = create_resp.json()["id"]

    # 3. Get Membership
    response = await client.get(f"/api/v1/organizations/{org_id}/members/me")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "owner"
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_get_my_membership_non_member(client: AsyncClient):
    """Get my membership — non-member — returns 403."""
    # 1. Register User A (Intruder)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "my_mem_intruder@example.com",
            "password": "StrongPassword123!",
            "full_name": "My Mem Intruder",
        },
    )
    # 2. Register User B (Owner)
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "my_mem_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "My Mem Owner",
        },
    )
    # 3. User B Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org My Mem Non", "slug": "org-my-mem-non"},
    )
    org_id = create_resp.json()["id"]

    # 4. Login as User A (Intruder)
    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "my_mem_intruder@example.com",
            "password": "StrongPassword123!",
        },
    )

    # 5. Try Get Membership
    # Note: get_org_membership_or_404 returns 403 for non-members
    response = await client.get(f"/api/v1/organizations/{org_id}/members/me")
    assert response.status_code == 403
    assert "access" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_members_success(client: AsyncClient):
    """List — success — returns members (200)."""
    # 1. Register Owner
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_mem_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "List Mem Owner",
        },
    )
    # 2. Create Org
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org List Mem", "slug": "org-list-mem"},
    )
    org_id = create_resp.json()["id"]

    # 3. Register Member
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_mem_user@example.com",
            "password": "StrongPassword123!",
            "full_name": "List Mem User",
        },
    )

    # 4. Login as Owner to Invite
    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "list_mem_owner@example.com",
            "password": "StrongPassword123!",
        },
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "list_mem_user@example.com", "role": "member"},
    )

    # 5. List Members
    response = await client.get(f"/api/v1/organizations/{org_id}/members")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) == 2  # Owner + Member

    # Check details
    roles = {m["role"] for m in items}
    assert "owner" in roles
    assert "member" in roles


@pytest.mark.asyncio
async def test_list_members_non_member(client: AsyncClient):
    """List — non-member — returns 403."""
    # 1. Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_non_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "List Non Owner",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org List Non", "slug": "org-list-non"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register Intruder
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "list_non_intr@example.com",
            "password": "StrongPassword123!",
            "full_name": "List Non Intr",
        },
    )

    # 3. Try List
    response = await client.get(f"/api/v1/organizations/{org_id}/members")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invite_member_success_owner(client: AsyncClient):
    """Invite — success — owner can invite (201)."""
    # 1. Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv Owner",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Owner", "slug": "org-inv-owner"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register Target User (must exist for invite)
    # Note: If invitation flow supported email-only (without existing user), test would be different.
    # But current implementation checks `select(User).where(email=...)`.
    target_email = "target_inv@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": target_email,
            "password": "StrongPassword123!",
            "full_name": "Target Inv",
        },
    )

    # 3. Login as Owner
    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "inv_owner@example.com",
            "password": "StrongPassword123!",
        },
    )

    # 4. Invite
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "member"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "member"
    assert data["user_email"] == target_email


@pytest.mark.asyncio
async def test_invite_member_success_admin(client: AsyncClient):
    """Invite — success — admin can invite (201)."""
    # 1. Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_o_admin@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv O Admin",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Admin", "slug": "org-inv-admin"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register Admin User
    admin_email = "inv_admin@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_email,
            "password": "StrongPassword123!",
            "full_name": "Inv Admin",
        },
    )

    # Login Owner -> Invite Admin User as 'admin'
    await client.post(
        "/api/v1/auth/login",
        json={"email": "inv_o_admin@example.com", "password": "StrongPassword123!"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": admin_email, "role": "admin"},
    )

    # 3. Register Target User
    target_email = "target_admin_inv@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": target_email,
            "password": "StrongPassword123!",
            "full_name": "Target Admin Inv",
        },
    )

    # 4. Login as Admin
    await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "StrongPassword123!"},
    )

    # 5. Invite Target
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "member"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_invite_member_non_admin(client: AsyncClient):
    """Invite — non-admin (member) — returns 403."""
    # 1. Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_o_mem@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv O Mem",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Mem", "slug": "org-inv-mem"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register Member User
    mem_email = "inv_mem@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": mem_email,
            "password": "StrongPassword123!",
            "full_name": "Inv Mem",
        },
    )

    # Login Owner -> Invite Member User as 'member'
    await client.post(
        "/api/v1/auth/login",
        json={"email": "inv_o_mem@example.com", "password": "StrongPassword123!"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": mem_email, "role": "member"},
    )

    # 3. Login as Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": mem_email, "password": "StrongPassword123!"},
    )

    # 4. Try Invite
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "someone@example.com", "role": "member"},
    )
    assert response.status_code == 403
    assert "Owner or admin role required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invite_member_unknown_email(client: AsyncClient):
    """Invite — unknown email — returns 404."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_unk@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv Unk",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Unk", "slug": "org-inv-unk"},
    )
    org_id = create_resp.json()["id"]

    # Invite unknown
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "doesnotexist@example.com", "role": "member"},
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invite_member_already_member(client: AsyncClient):
    """Invite — already member — returns 409."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_dup@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv Dup",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Dup", "slug": "org-inv-dup"},
    )
    org_id = create_resp.json()["id"]

    # Register Target
    target_email = "target_dup@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": target_email,
            "password": "StrongPassword123!",
            "full_name": "Target Dup",
        },
    )

    # Login Owner
    await client.post(
        "/api/v1/auth/login",
        json={"email": "inv_dup@example.com", "password": "StrongPassword123!"},
    )

    # Invite First Time
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "member"},
    )

    # Invite Second Time
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "admin"},
    )
    assert response.status_code == 409
    assert "already a member" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invite_member_missing_email(client: AsyncClient):
    """Invite — missing email — returns 422."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "inv_miss@example.com",
            "password": "StrongPassword123!",
            "full_name": "Inv Miss",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Inv Miss", "slug": "org-inv-miss"},
    )
    org_id = create_resp.json()["id"]

    # Invite missing email
    response = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"role": "member"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_role_success(client: AsyncClient):
    """Change Role — success — owner can change role (200)."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "role_suc@example.com",
            "password": "StrongPassword123!",
            "full_name": "Role Suc",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Role Suc", "slug": "org-role-suc"},
    )
    org_id = create_resp.json()["id"]

    # Register Target & Invite
    target_email = "target_role@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": target_email,
            "password": "StrongPassword123!",
            "full_name": "Target Role",
        },
    )
    # Login Owner
    await client.post(
        "/api/v1/auth/login",
        json={"email": "role_suc@example.com", "password": "StrongPassword123!"},
    )
    inv_resp = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "member"},
    )
    member_id = inv_resp.json()["id"]

    # Change Role to Admin
    response = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{member_id}",
        json={"role": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_change_role_non_owner(client: AsyncClient):
    """Change Role — non-owner (admin) — returns 403."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "role_non_o@example.com",
            "password": "StrongPassword123!",
            "full_name": "Role Non O",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Role Non", "slug": "org-role-non"},
    )
    org_id = create_resp.json()["id"]

    # Register Admin & Invite
    admin_email = "admin_try_role@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_email,
            "password": "StrongPassword123!",
            "full_name": "Admin Try Role",
        },
    )
    # Login Owner
    await client.post(
        "/api/v1/auth/login",
        json={"email": "role_non_o@example.com", "password": "StrongPassword123!"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": admin_email, "role": "admin"},
    )
    # Register Another Member
    mem_email = "target_mem@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": mem_email,
            "password": "StrongPassword123!",
            "full_name": "Target Mem",
        },
    )
    # Login Owner again
    await client.post(
        "/api/v1/auth/login",
        json={"email": "role_non_o@example.com", "password": "StrongPassword123!"},
    )
    inv_resp_2 = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": mem_email, "role": "member"},
    )
    member_id_2 = inv_resp_2.json()["id"]

    # Login as Admin
    await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "StrongPassword123!"},
    )

    # Try Change Role
    response = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{member_id_2}",
        json={"role": "admin"},
    )
    assert response.status_code == 403
    assert "Owner role required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_role_last_owner_demotion(client: AsyncClient):
    """Change Role — last owner demotion — returns 400."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "last_owner@example.com",
            "password": "StrongPassword123!",
            "full_name": "Last Owner",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Last Owner", "slug": "org-last-owner"},
    )
    org_id = create_resp.json()["id"]

    # Get Own Membership ID
    mem_resp = await client.get(f"/api/v1/organizations/{org_id}/members/me")
    member_id = mem_resp.json()["id"]

    # Try Demote Self
    response = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{member_id}",
        json={"role": "member"},
    )
    assert response.status_code == 400
    assert "Cannot demote the last owner" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member_success(client: AsyncClient):
    """Remove — success — owner can remove (204)."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_suc@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Suc",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Suc", "slug": "org-rem-suc"},
    )
    org_id = create_resp.json()["id"]

    # Register Target & Invite
    target_email = "rem_target@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": target_email,
            "password": "StrongPassword123!",
            "full_name": "Rem Target",
        },
    )
    # Login Owner
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_suc@example.com", "password": "StrongPassword123!"},
    )
    inv_resp = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": target_email, "role": "member"},
    )
    member_id = inv_resp.json()["id"]

    # Remove
    response = await client.delete(
        f"/api/v1/organizations/{org_id}/members/{member_id}"
    )
    assert response.status_code == 204

    # Verify removed
    list_resp = await client.get(f"/api/v1/organizations/{org_id}/members")
    items = list_resp.json()["items"]
    assert not any(m["id"] == member_id for m in items)


@pytest.mark.asyncio
async def test_remove_member_non_admin(client: AsyncClient):
    """Remove — non-admin (member) — returns 403."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_non@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Non",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Non", "slug": "org-rem-non"},
    )
    org_id = create_resp.json()["id"]

    # Register Member
    mem_email = "rem_killer@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": mem_email,
            "password": "StrongPassword123!",
            "full_name": "Rem Killer",
        },
    )
    # Login Owner -> Invite Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_non@example.com", "password": "StrongPassword123!"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": mem_email, "role": "member"},
    )

    # Login as Member
    await client.post(
        "/api/v1/auth/login",
        json={"email": mem_email, "password": "StrongPassword123!"},
    )

    # Try Remove Owner (or self, but endpoint requires admin/owner)
    # Get ID of owner? List members
    list_resp = await client.get(f"/api/v1/organizations/{org_id}/members")
    items = list_resp.json()["items"]
    owner_id = next(m["id"] for m in items if m["role"] == "owner")

    response = await client.delete(f"/api/v1/organizations/{org_id}/members/{owner_id}")
    assert response.status_code == 403
    assert "Owner or admin role required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_last_owner(client: AsyncClient):
    """Remove — last owner — returns 400."""
    # Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_last@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Last",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Last", "slug": "org-rem-last"},
    )
    org_id = create_resp.json()["id"]

    # Get Own Membership ID
    mem_resp = await client.get(f"/api/v1/organizations/{org_id}/members/me")
    member_id = mem_resp.json()["id"]

    # Try Remove Self
    response = await client.delete(
        f"/api/v1/organizations/{org_id}/members/{member_id}"
    )
    assert response.status_code == 400
    assert "Cannot remove the last owner" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member_success_admin(client: AsyncClient):
    """Remove — success — admin can remove (204)."""
    # 1. Register Owner & Create Org
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_adm_o@x.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Adm O",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Adm", "slug": "org-rem-adm"},
    )
    org_id = create_resp.json()["id"]

    # 2. Register Admin
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_adm@x.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Adm",
        },
    )
    # Login Owner -> Invite Admin
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_adm_o@x.com", "password": "StrongPassword123!"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "rem_adm@x.com", "role": "admin"},
    )

    # 3. Register Victim
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_vic@x.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Vic",
        },
    )

    # 4. Login Owner -> Invite Victim
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_adm_o@x.com", "password": "StrongPassword123!"},
    )
    inv_resp = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"email": "rem_vic@x.com", "role": "member"},
    )
    victim_id = inv_resp.json()["id"]

    # 5. Login Admin
    await client.post(
        "/api/v1/auth/login",
        json={"email": "rem_adm@x.com", "password": "StrongPassword123!"},
    )

    # 6. Remove Victim
    response = await client.delete(
        f"/api/v1/organizations/{org_id}/members/{victim_id}"
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_change_role_not_found(client: AsyncClient):
    """Change Role — member not found — returns 404."""
    # Register/Create
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "chg_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Chg Nf",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Chg Nf", "slug": "org-chg-nf"},
    )
    org_id = create_resp.json()["id"]

    # Try change random UUID
    rand_id = str(uuid.uuid4())

    response = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{rand_id}",
        json={"role": "admin"},
    )
    assert response.status_code == 404
    assert "Member not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_member_not_found(client: AsyncClient):
    """Remove — member not found — returns 404."""
    # Register/Create
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rem_nf@x.com",
            "password": "StrongPassword123!",
            "full_name": "Rem Nf",
        },
    )
    create_resp = await client.post(
        "/api/v1/organizations",
        json={"name": "Org Rem Nf", "slug": "org-rem-nf"},
    )
    org_id = create_resp.json()["id"]

    # Try remove random UUID
    rand_id = str(uuid.uuid4())

    response = await client.delete(f"/api/v1/organizations/{org_id}/members/{rand_id}")
    assert response.status_code == 404
    assert "Member not found" in response.json()["detail"]
