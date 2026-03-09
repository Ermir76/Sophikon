import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User
from tests.fixtures.project_members import add_project_member


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
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 200, response.text


async def _create_project_and_task(client: AsyncClient) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": "Comments Org", "slug": f"comments-org-{uuid.uuid4().hex[:8]}"},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Comments Project",
            "organization_id": org_id,
            "start_date": "2026-03-08",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Commented Task",
            "start_date": "2026-03-08",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project_id, task_response.json()["id"]


async def _get_user_id(session: AsyncSession, email: str) -> str:
    result = await session.execute(select(User.id).where(User.email == email))
    user_id = result.scalar_one_or_none()
    assert user_id is not None
    return str(user_id)


@pytest.mark.asyncio
async def test_task_comment_create_list_reply_and_mention_notification(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    await _register(client, "owner-comments@example.com", "Owner Comments")
    await _login(client, "owner-comments@example.com")
    project_id, task_id = await _create_project_and_task(client)

    await _register(client, "member-comments@example.com", "Member Comments")
    await add_project_member(
        session, project_id, "member-comments@example.com", "member"
    )
    mentioned_user_id = await _get_user_id(session, "member-comments@example.com")
    await _login(client, "owner-comments@example.com")

    create_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": f"Please review @[Member Comments](user:{mentioned_user_id})",
            "parent_comment_id": None,
        },
    )
    assert create_response.status_code == 201, create_response.text
    parent_comment_id = create_response.json()["id"]
    assert create_response.json()["mentions"] == [mentioned_user_id]

    reply_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Reply comment",
            "parent_comment_id": parent_comment_id,
        },
    )
    assert reply_response.status_code == 201, reply_response.text

    list_response = await client.get(f"/api/v1/comments/entity/task/{task_id}")
    assert list_response.status_code == 200, list_response.text
    payload = list_response.json()["data"]
    assert len(payload) == 1
    assert len(payload[0]["replies"]) == 1

    notif_result = await session.execute(
        select(Notification).where(
            Notification.user_id == uuid.UUID(mentioned_user_id),
            Notification.type == NotificationType.MENTIONED,
            Notification.entity_type == "comment",
        )
    )
    notifications = list(notif_result.scalars().all())
    assert len(notifications) == 1


@pytest.mark.asyncio
async def test_create_comment_rejects_invalid_mentioned_user(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "owner-mention-invalid@example.com", "Owner Mention")
    await _login(client, "owner-mention-invalid@example.com")
    _, task_id = await _create_project_and_task(client)

    await _register(client, "outsider-mention-invalid@example.com", "Outsider Mention")
    outsider_id = await _get_user_id(session, "outsider-mention-invalid@example.com")
    await _login(client, "owner-mention-invalid@example.com")

    response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": f"Invalid mention @[Outsider](user:{outsider_id})",
            "parent_comment_id": None,
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_OPERATION"


@pytest.mark.asyncio
async def test_viewer_cannot_create_comment(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    await _register(client, "owner-viewer-comments@example.com", "Owner Viewer")
    await _login(client, "owner-viewer-comments@example.com")
    project_id, task_id = await _create_project_and_task(client)

    await _register(client, "viewer-comments@example.com", "Viewer Comments")
    await add_project_member(
        session, project_id, "viewer-comments@example.com", "viewer"
    )
    await _login(client, "viewer-comments@example.com")

    response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Viewer cannot comment",
            "parent_comment_id": None,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_moderation_rules_for_update_comment(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    await _register(client, "owner-moderation@example.com", "Owner Moderation")
    await _login(client, "owner-moderation@example.com")
    project_id, task_id = await _create_project_and_task(client)

    await _register(client, "member-moderation@example.com", "Member Moderation")
    await _register(client, "manager-moderation@example.com", "Manager Moderation")
    await add_project_member(
        session, project_id, "member-moderation@example.com", "member"
    )
    await add_project_member(
        session, project_id, "manager-moderation@example.com", "manager"
    )

    create_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Original owner comment",
            "parent_comment_id": None,
        },
    )
    assert create_response.status_code == 201
    comment_id = create_response.json()["id"]

    await _login(client, "member-moderation@example.com")
    member_update = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"content": "Member tries update"},
    )
    assert member_update.status_code == 403

    await _login(client, "manager-moderation@example.com")
    manager_update = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"content": "Manager updated"},
    )
    assert manager_update.status_code == 200
    assert manager_update.json()["content"] == "Manager updated"
    assert manager_update.json()["is_edited"] is True


@pytest.mark.asyncio
async def test_noop_update_comment_keeps_edited_flag_false(
    client: AsyncClient,
):
    await _register(client, "owner-noop-update@example.com", "Owner Noop")
    await _login(client, "owner-noop-update@example.com")
    _, task_id = await _create_project_and_task(client)

    create_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "No-op update",
            "parent_comment_id": None,
        },
    )
    assert create_response.status_code == 201
    comment_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"content": "No-op update"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_edited"] is False


@pytest.mark.asyncio
async def test_delete_comment_soft_deletes_subtree_and_updates_task_count(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "owner-delete-comments@example.com", "Owner Delete")
    await _login(client, "owner-delete-comments@example.com")
    project_id, task_id = await _create_project_and_task(client)

    parent_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Parent comment",
            "parent_comment_id": None,
        },
    )
    parent_id = parent_response.json()["id"]
    await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Child comment",
            "parent_comment_id": parent_id,
        },
    )
    task_before_delete = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert task_before_delete.status_code == 200
    assert task_before_delete.json()["comments_count"] == 2

    delete_response = await client.delete(f"/api/v1/comments/{parent_id}")
    assert delete_response.status_code == 204

    list_response = await client.get(f"/api/v1/comments/entity/task/{task_id}")
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    task_after_delete = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert task_after_delete.status_code == 200
    assert task_after_delete.json()["comments_count"] == 0

    comment_result = await session.execute(
        select(Comment).where(
            Comment.entity_type == "task",
            Comment.entity_id == uuid.UUID(task_id),
        )
    )
    comments = list(comment_result.scalars().all())
    assert len(comments) == 2
    assert all(comment.is_deleted for comment in comments)


@pytest.mark.asyncio
async def test_list_comments_hides_orphaned_children_when_parent_deleted(
    client: AsyncClient,
    session: AsyncSession,
):
    await _register(client, "owner-orphan-comments@example.com", "Owner Orphan")
    await _login(client, "owner-orphan-comments@example.com")
    _, task_id = await _create_project_and_task(client)

    parent_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Parent comment",
            "parent_comment_id": None,
        },
    )
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["id"]

    child_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Child comment",
            "parent_comment_id": parent_id,
        },
    )
    assert child_response.status_code == 201

    parent_uuid = uuid.UUID(parent_id)
    parent_result = await session.execute(
        select(Comment).where(Comment.id == parent_uuid)
    )
    parent_comment = parent_result.scalar_one_or_none()
    assert parent_comment is not None
    parent_comment.is_deleted = True
    parent_comment.deleted_at = datetime.now(UTC)
    await session.commit()

    list_response = await client.get(f"/api/v1/comments/entity/task/{task_id}")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["data"] == []


@pytest.mark.asyncio
async def test_create_comment_on_project_entity(
    client: AsyncClient,
):
    await _register(client, "owner-project-comments@example.com", "Owner Project")
    await _login(client, "owner-project-comments@example.com")
    project_id, _ = await _create_project_and_task(client)

    response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "project",
            "entity_id": project_id,
            "content": "Project level note",
            "parent_comment_id": None,
        },
    )
    assert response.status_code == 201
    assert response.json()["entity_type"] == "project"
