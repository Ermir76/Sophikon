from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.service import project_service


def _unique_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local}+{uuid7()}@{domain}"


def _unique_slug(slug: str) -> str:
    return f"{slug}-{uuid7()}"


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
async def test_create_project_creates_owner_membership(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = _unique_email("project-service-owner@example.com")
    await _register_user(client, owner_email, "Project Service Owner")
    org_id = await _create_org(client, _unique_slug("project-service-owner-org"))
    owner = await _get_user(session, owner_email)

    project = await project_service.create_project(
        session,
        owner,
        {
            "organization_id": org_id,
            "name": "Owner Membership Project",
            "start_date": date(2026, 3, 1),
        },
    )

    membership_result = await session.execute(
        select(ProjectMember, Role.name)
        .join(Role, Role.id == ProjectMember.role_id)
        .where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == owner.id,
        )
    )
    member, role_name = membership_result.one()

    assert str(member.project_id) == str(project.id)
    assert role_name == "owner"


@pytest.mark.asyncio
async def test_list_projects_deduplicates_owned_projects_with_multiple_members(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = _unique_email("project-service-list-owner@example.com")
    teammate_one_email = _unique_email("project-service-list-member-1@example.com")
    teammate_two_email = _unique_email("project-service-list-member-2@example.com")

    await _register_user(client, owner_email, "Project List Owner")
    org_id = await _create_org(client, _unique_slug("project-service-list-org"))
    owner = await _get_user(session, owner_email)

    project = await project_service.create_project(
        session,
        owner,
        {
            "organization_id": org_id,
            "name": "Shared Project",
            "start_date": date(2026, 3, 2),
        },
    )

    await _register_user(client, teammate_one_email, "Project List Member One")
    await _register_user(client, teammate_two_email, "Project List Member Two")
    teammate_one = await _get_user(session, teammate_one_email)
    teammate_two = await _get_user(session, teammate_two_email)
    member_role = await _ensure_project_role(session, "member")

    session.add(
        ProjectMember(
            project_id=project.id,
            user_id=teammate_one.id,
            role_id=member_role.id,
        )
    )
    await session.flush()
    session.add(
        ProjectMember(
            project_id=project.id,
            user_id=teammate_two.id,
            role_id=member_role.id,
        )
    )
    await session.commit()

    projects, total = await project_service.list_projects(session, owner)

    assert total == 1
    assert [str(item.id) for item in projects] == [str(project.id)]
