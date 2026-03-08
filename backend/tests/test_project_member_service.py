from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.security import hash_token
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.schema.project import ProjectCreate
from app.schema.project_member import ProjectInvitationAccept, ProjectMemberInvite
from app.service import project_member_service, project_service


def _unique_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local}+{uuid7()}@{domain}"


def _unique_slug(slug: str) -> str:
    return f"{slug}-{uuid7()}"


def _unique_token(prefix: str) -> str:
    return f"{prefix}-{uuid7()}"


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


async def _create_org(client: AsyncClient, slug: str) -> str:
    response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one()


async def _ensure_project_role(session: AsyncSession, name: str) -> Role:
    result = await session.execute(
        select(Role).where(Role.name == name, Role.scope == "project")
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=name, scope="project")
        session.add(role)
        await session.flush()
    return role


@pytest.mark.asyncio
async def test_ensure_owner_membership_upgrades_owner_row_to_owner_role(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = _unique_email("project-member-owner@example.com")
    await _register_user(client, owner_email, "Project Member Owner")
    org_id = await _create_org(client, _unique_slug("project-member-owner-org"))
    owner = await _get_user(session, owner_email)
    member_role = await _ensure_project_role(session, "member")

    project = Project(
        owner_id=owner.id,
        organization_id=org_id,
        name="Owner Membership Repair",
        start_date=date(2026, 3, 1),
    )
    session.add(project)
    await session.flush()

    session.add(
        ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role_id=member_role.id,
        )
    )
    await session.commit()

    await project_member_service.ensure_owner_membership(session, project)

    membership_result = await session.execute(
        select(ProjectMember, Role.name)
        .join(Role, Role.id == ProjectMember.role_id)
        .where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner.id,
        )
    )
    member, role_name = membership_result.one()

    assert str(member.user_id) == str(owner.id)
    assert role_name == "owner"


@pytest.mark.asyncio
async def test_invite_member_normalizes_email_and_persists_token(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    inviter_email = _unique_email("project-member-inviter@example.com")
    await _register_user(client, inviter_email, "Project Member Inviter")
    org_id = await _create_org(client, _unique_slug("project-member-invite-org"))
    inviter = await _get_user(session, inviter_email)
    expected_token = _unique_token("project-member-service-token")

    project = await project_service.create_project(
        session,
        inviter,
        ProjectCreate(
            organization_id=org_id,
            name="Invite Member Project",
            start_date=date(2026, 3, 2),
        ),
    )

    monkeypatch.setattr(
        "app.service.project_member_service.secrets.token_urlsafe",
        lambda _: expected_token,
    )

    invitation_payload, raw_token = await project_member_service.invite_member(
        session,
        project,
        inviter,
        "owner",
        ProjectMemberInvite(
            email="Invitee@Example.com",
            role="viewer",
            message="Please join",
        ),
    )

    stored_invitation = (
        await session.execute(
            select(ProjectInvitation).where(ProjectInvitation.project_id == project.id)
        )
    ).scalar_one()

    assert raw_token == expected_token
    assert invitation_payload["email"] == "invitee@example.com"
    assert invitation_payload["role"] == "viewer"
    assert stored_invitation.email == "invitee@example.com"
    assert stored_invitation.token_hash == hash_token(raw_token)


@pytest.mark.asyncio
async def test_accept_invitation_creates_memberships_and_marks_invitation_used(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = _unique_email("project-member-accept-owner@example.com")
    invitee_email = _unique_email("project-member-accept-invitee@example.com")
    accept_token = _unique_token("accept-token")

    await _register_user(client, owner_email, "Project Member Accept Owner")
    org_id = await _create_org(client, _unique_slug("project-member-accept-org"))
    await _register_user(client, invitee_email, "Project Member Accept Invitee")

    owner = await _get_user(session, owner_email)
    invitee = await _get_user(session, invitee_email)
    project = await project_service.create_project(
        session,
        owner,
        ProjectCreate(
            organization_id=org_id,
            name="Accept Member Project",
            start_date=date(2026, 3, 3),
        ),
    )
    member_role = await _ensure_project_role(session, "member")

    invitation = ProjectInvitation(
        project_id=project.id,
        invited_by_id=owner.id,
        role_id=member_role.id,
        email=invitee.email,
        token_hash=hash_token(accept_token),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        is_revoked=False,
    )
    session.add(invitation)
    await session.commit()

    project_id, member_id = await project_member_service.accept_invitation(
        session,
        invitee,
        ProjectInvitationAccept(token=accept_token),
    )

    org_member = (
        await session.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == invitee.id,
            )
        )
    ).scalar_one()
    project_member = (
        await session.execute(
            select(ProjectMember).where(ProjectMember.id == member_id)
        )
    ).scalar_one()
    await session.refresh(invitation)

    assert str(project_id) == str(project.id)
    assert str(project_member.project_id) == str(project.id)
    assert str(project_member.user_id) == str(invitee.id)
    assert org_member.role == "member"
    assert invitation.accepted_at is not None
