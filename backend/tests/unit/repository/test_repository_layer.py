from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.comment import Comment
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User
from app.repository import notification_repo, project_repo, task_repo


async def _register(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _login(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200, response.text


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    assert user is not None
    return user


async def _ensure_project_member_role(session: AsyncSession) -> Role:
    result = await session.execute(
        select(Role).where(Role.scope == "project", Role.name == "member")
    )
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name="member", scope="project")
        session.add(role)
        await session.flush()
    return role


async def _create_project(client: AsyncClient, *, org_slug: str) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {org_slug}", "slug": org_slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Repo Layer Project",
            "organization_id": org_id,
            "start_date": "2026-03-10",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return org_id, project_response.json()["id"]


@pytest.mark.asyncio
async def test_notification_repo_filters_and_joins_actor(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "repo-notif-user@example.com", "Repo Notif User")
    await _register(client, "repo-notif-actor@example.com", "Repo Notif Actor")
    user = await _get_user(session, "repo-notif-user@example.com")
    actor = await _get_user(session, "repo-notif-actor@example.com")

    session.add_all(
        [
            Notification(
                user_id=user.id,
                actor_id=actor.id,
                type=NotificationType.MENTIONED,
                title="Unread mention",
                entity_type="comment",
                entity_id=uuid.uuid4(),
            ),
            Notification(
                user_id=user.id,
                actor_id=actor.id,
                type=NotificationType.TASK_ASSIGNED,
                title="Read assignment",
                entity_type="task",
                entity_id=uuid.uuid4(),
                is_read=True,
            ),
        ]
    )
    await session.commit()

    rows, total = await notification_repo.list_with_actor(
        session,
        user_id=user.id,
        page=1,
        per_page=20,
        unread_only=True,
    )

    assert total == 1
    assert len(rows) == 1
    assert rows[0].notification.title == "Unread mention"
    assert rows[0].actor_full_name == "Repo Notif Actor"


@pytest.mark.asyncio
async def test_project_repo_deduplicates_when_project_has_multiple_members(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "repo-project-owner@example.com", "Repo Project Owner")
    await _register(client, "repo-project-member1@example.com", "Repo Member One")
    await _register(client, "repo-project-member2@example.com", "Repo Member Two")
    await _login(client, "repo-project-owner@example.com")

    _, project_id = await _create_project(
        client, org_slug=f"repo-org-{uuid.uuid4().hex[:8]}"
    )
    owner = await _get_user(session, "repo-project-owner@example.com")
    member_one = await _get_user(session, "repo-project-member1@example.com")
    member_two = await _get_user(session, "repo-project-member2@example.com")
    member_role = await _ensure_project_member_role(session)
    project = await project_repo.get_project_by_id(
        session,
        project_id=uuid.UUID(project_id),
    )
    assert project is not None

    session.add_all(
        [
            ProjectMember(
                id=uuid.UUID(bytes=uuid7().bytes),
                project_id=project.id,
                user_id=member_one.id,
                role_id=member_role.id,
            ),
            ProjectMember(
                id=uuid.UUID(bytes=uuid7().bytes),
                project_id=project.id,
                user_id=member_two.id,
                role_id=member_role.id,
            ),
        ]
    )
    await session.commit()

    projects, total = await project_repo.list_projects_for_user(
        session,
        user_id=owner.id,
        page=1,
        per_page=20,
        status=None,
        search=None,
        organization_id=None,
    )

    assert total == 1
    assert len(projects) == 1
    assert str(projects[0].id) == project_id


@pytest.mark.asyncio
async def test_task_repo_get_task_with_comment_count_excludes_deleted_comments(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "repo-task-user@example.com", "Repo Task User")
    await _login(client, "repo-task-user@example.com")
    _, project_id = await _create_project(
        client, org_slug=f"repo-task-org-{uuid.uuid4().hex[:8]}"
    )

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Repo task",
            "start_date": "2026-03-10",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = uuid.UUID(task_response.json()["id"])

    user = await _get_user(session, "repo-task-user@example.com")
    session.add_all(
        [
            Comment(
                entity_type="task",
                entity_id=task_id,
                author_id=user.id,
                content="Visible",
            ),
            Comment(
                entity_type="task",
                entity_id=task_id,
                author_id=user.id,
                content="Deleted",
                is_deleted=True,
            ),
        ]
    )
    await session.commit()

    row = await task_repo.get_task_with_comment_count(
        session,
        task_id=task_id,
        project_id=uuid.UUID(project_id),
    )

    assert row is not None
    task, comments_count = row
    assert task.id == task_id
    assert comments_count == 1
