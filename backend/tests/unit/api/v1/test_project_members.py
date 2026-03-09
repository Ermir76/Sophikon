from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization_member import OrganizationMember
from app.models.project_invitation import ProjectInvitation
from app.models.user import User
from tests.fixtures.project_members import add_project_member


async def _register_user(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _login_user(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200, response.text


async def _create_project(
    client: AsyncClient,
    *,
    owner_email: str,
    org_slug: str,
) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {org_slug}", "slug": org_slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Project Members Test",
            "organization_id": org_id,
            "start_date": "2026-03-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    await _login_user(client, owner_email)
    return org_id, project_id


@pytest.mark.asyncio
async def test_list_members_includes_owner_row(client: AsyncClient):
    owner_email = "pm_owner_list@example.com"
    await _register_user(client, owner_email, "Owner List")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-list",
    )

    response = await client.get(f"/api/v1/projects/{project_id}/members")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["role"] == "owner"
    assert data["items"][0]["user_email"] == owner_email


@pytest.mark.asyncio
async def test_invite_creates_pending_invitation_and_enqueues_email(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    owner_email = "pm_owner_invite@example.com"
    invitee_email = "pm_invitee_invite@example.com"
    await _register_user(client, owner_email, "Owner Invite")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-invite",
    )
    await _register_user(client, invitee_email, "Invitee")
    await _login_user(client, owner_email)

    sent: list[str] = []

    async def _fake_send(**kwargs):
        sent.append(kwargs["recipient_email"])

    monkeypatch.setattr(
        "app.api.v1.endpoints.project_members.project_member_service."
        "send_project_invitation_email_with_retry",
        _fake_send,
    )

    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "member"},
    )
    assert invite_response.status_code == 201, invite_response.text
    payload = invite_response.json()["invitation"]
    assert payload["email"] == invitee_email
    assert payload["role"] == "member"
    assert sent == [invitee_email]

    list_response = await client.get(
        f"/api/v1/projects/{project_id}/members/invitations"
    )
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] == 1


@pytest.mark.asyncio
async def test_manager_invite_restrictions(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    owner_email = "pm_owner_mgr_inv@example.com"
    manager_email = "pm_manager_inv@example.com"
    invitee_email = "pm_invitee_mgr_inv@example.com"

    await _register_user(client, owner_email, "Owner Manager Invite")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-mgr-invite",
    )
    await _register_user(client, manager_email, "Manager")
    await _register_user(client, invitee_email, "Invitee")
    await add_project_member(session, project_id, manager_email, "manager")

    await _login_user(client, manager_email)
    forbidden = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "manager"},
    )
    assert forbidden.status_code == 403

    allowed = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "viewer"},
    )
    assert allowed.status_code == 201, allowed.text


@pytest.mark.asyncio
async def test_invite_rejects_invalid_email_format(client: AsyncClient):
    owner_email = "pm_owner_invalid_email@example.com"
    await _register_user(client, owner_email, "Owner Invalid Email")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-invalid-email",
    )

    response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": "not-an-email", "role": "member"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_owner_role_change_and_last_owner_protection(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    owner_email = "pm_owner_role@example.com"
    member_email = "pm_member_role@example.com"

    await _register_user(client, owner_email, "Owner Role")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-role",
    )
    await _register_user(client, member_email, "Member Role")
    await add_project_member(session, project_id, member_email, "member")
    await _login_user(client, owner_email)

    members_response = await client.get(f"/api/v1/projects/{project_id}/members")
    members = members_response.json()["items"]
    owner_member_id = next(m["id"] for m in members if m["role"] == "owner")
    target_member_id = next(m["id"] for m in members if m["user_email"] == member_email)

    demote_last_owner = await client.patch(
        f"/api/v1/projects/{project_id}/members/{owner_member_id}",
        json={"role": "manager"},
    )
    assert demote_last_owner.status_code == 400

    promote_member = await client.patch(
        f"/api/v1/projects/{project_id}/members/{target_member_id}",
        json={"role": "viewer"},
    )
    assert promote_member.status_code == 200, promote_member.text
    assert promote_member.json()["role"] == "viewer"


@pytest.mark.asyncio
async def test_manager_cannot_change_roles(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    owner_email = "pm_owner_mgr_patch@example.com"
    manager_email = "pm_manager_patch@example.com"
    member_email = "pm_member_patch@example.com"

    await _register_user(client, owner_email, "Owner")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-mgr-patch",
    )
    await _register_user(client, manager_email, "Manager")
    await _register_user(client, member_email, "Member")
    await add_project_member(session, project_id, manager_email, "manager")
    await add_project_member(session, project_id, member_email, "member")

    await _login_user(client, owner_email)
    members_response = await client.get(f"/api/v1/projects/{project_id}/members")
    member_id = next(
        m["id"]
        for m in members_response.json()["items"]
        if m["user_email"] == member_email
    )

    await _login_user(client, manager_email)
    response = await client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        json={"role": "viewer"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_manager_remove_restrictions(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    owner_email = "pm_owner_mgr_remove@example.com"
    manager_email = "pm_manager_remove@example.com"
    member_email = "pm_member_remove@example.com"
    other_manager_email = "pm_other_manager_remove@example.com"

    await _register_user(client, owner_email, "Owner")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-mgr-remove",
    )
    await _register_user(client, manager_email, "Manager")
    await _register_user(client, member_email, "Member")
    await _register_user(client, other_manager_email, "Other Manager")
    await add_project_member(session, project_id, manager_email, "manager")
    await add_project_member(session, project_id, member_email, "member")
    await add_project_member(session, project_id, other_manager_email, "manager")

    await _login_user(client, manager_email)
    members_response = await client.get(f"/api/v1/projects/{project_id}/members")
    members = members_response.json()["items"]
    member_id = next(m["id"] for m in members if m["user_email"] == member_email)
    other_manager_id = next(
        m["id"] for m in members if m["user_email"] == other_manager_email
    )

    remove_member_response = await client.delete(
        f"/api/v1/projects/{project_id}/members/{member_id}"
    )
    assert remove_member_response.status_code == 204, remove_member_response.text

    remove_manager_response = await client.delete(
        f"/api/v1/projects/{project_id}/members/{other_manager_id}"
    )
    assert remove_manager_response.status_code == 403


@pytest.mark.asyncio
async def test_resend_and_revoke_invitation(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    owner_email = "pm_owner_resend@example.com"
    invitee_email = "pm_invitee_resend@example.com"

    await _register_user(client, owner_email, "Owner Resend")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-resend",
    )
    await _register_user(client, invitee_email, "Invitee Resend")
    await _login_user(client, owner_email)

    call_count = {"count": 0}

    async def _fake_send(**kwargs):
        _ = kwargs
        call_count["count"] += 1

    monkeypatch.setattr(
        "app.api.v1.endpoints.project_members.project_member_service."
        "send_project_invitation_email_with_retry",
        _fake_send,
    )

    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "viewer"},
    )
    invitation_id = invite_response.json()["invitation"]["id"]

    resend_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invitations/{invitation_id}/resend"
    )
    assert resend_response.status_code == 200, resend_response.text
    assert call_count["count"] == 2

    revoke_response = await client.delete(
        f"/api/v1/projects/{project_id}/members/invitations/{invitation_id}"
    )
    assert revoke_response.status_code == 204, revoke_response.text

    list_response = await client.get(
        f"/api/v1/projects/{project_id}/members/invitations"
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_accept_invitation_success_adds_org_membership(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    owner_email = "pm_owner_accept_ok@example.com"
    invitee_email = "pm_invitee_accept_ok@example.com"
    token = "pm-invite-token-accept-ok"

    await _register_user(client, owner_email, "Owner Accept")
    org_id, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-accept-ok",
    )
    await _register_user(client, invitee_email, "Invitee Accept")
    await _login_user(client, owner_email)

    monkeypatch.setattr(
        "app.service.project_member_service.secrets.token_urlsafe",
        lambda _: token,
    )

    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "member"},
    )
    assert invite_response.status_code == 201, invite_response.text

    await _login_user(client, invitee_email)
    accept_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert accept_response.status_code == 200, accept_response.text
    assert accept_response.json()["project_id"] == project_id

    project_access_response = await client.get(f"/api/v1/projects/{project_id}")
    assert project_access_response.status_code == 200, project_access_response.text

    user_result = await session.execute(select(User).where(User.email == invitee_email))
    invitee_user = user_result.scalar_one()
    org_member_result = await session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == invitee_user.id,
        )
    )
    org_member = org_member_result.scalar_one_or_none()
    assert org_member is not None
    assert org_member.role == "member"


@pytest.mark.asyncio
async def test_accept_invitation_rejects_email_mismatch_and_invalid_token(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    owner_email = "pm_owner_accept_bad@example.com"
    invitee_email = "pm_invitee_accept_bad@example.com"
    other_email = "pm_other_accept_bad@example.com"
    token = "pm-invite-token-accept-bad"

    await _register_user(client, owner_email, "Owner Accept Bad")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-accept-bad",
    )
    await _register_user(client, invitee_email, "Invitee Accept Bad")
    await _register_user(client, other_email, "Other Accept Bad")
    await _login_user(client, owner_email)

    monkeypatch.setattr(
        "app.service.project_member_service.secrets.token_urlsafe",
        lambda _: token,
    )
    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "member"},
    )
    assert invite_response.status_code == 201, invite_response.text

    await _login_user(client, other_email)
    mismatch_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert mismatch_response.status_code == 403

    invalid_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": "not-a-valid-token"},
    )
    assert invalid_response.status_code == 400


@pytest.mark.asyncio
async def test_accept_invitation_rejects_revoked_expired_and_already_accepted(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    owner_email = "pm_owner_accept_state@example.com"
    invitee_email = "pm_invitee_accept_state@example.com"
    token = "pm-invite-token-accept-state"

    await _register_user(client, owner_email, "Owner Accept State")
    _, project_id = await _create_project(
        client,
        owner_email=owner_email,
        org_slug="org-pm-accept-state",
    )
    await _register_user(client, invitee_email, "Invitee Accept State")
    await _login_user(client, owner_email)

    monkeypatch.setattr(
        "app.service.project_member_service.secrets.token_urlsafe",
        lambda _: token,
    )
    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": invitee_email, "role": "member"},
    )
    assert invite_response.status_code == 201

    invitation_result = await session.execute(
        select(ProjectInvitation).where(ProjectInvitation.email == invitee_email)
    )
    invitation = invitation_result.scalar_one()

    await _login_user(client, invitee_email)

    invitation.is_revoked = True
    await session.commit()
    revoked_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert revoked_response.status_code == 400

    invitation.is_revoked = False
    invitation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await session.commit()
    expired_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert expired_response.status_code == 400

    invitation.expires_at = datetime.now(UTC) + timedelta(days=1)
    invitation.accepted_at = None
    await session.commit()
    accepted_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert accepted_response.status_code == 200

    accepted_again_response = await client.post(
        "/api/v1/projects/members/invitations/accept",
        json={"token": token},
    )
    assert accepted_again_response.status_code == 400
