import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


async def _register_and_login(client: AsyncClient, email: str, full_name: str) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": full_name,
        },
    )
    assert register_response.status_code == 201, register_response.text

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )
    assert login_response.status_code == 200, login_response.text


async def _create_project_and_task(client: AsyncClient) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Task Service Org",
            "slug": f"task-service-{uuid.uuid4().hex[:8]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Task Service Project",
            "organization_id": org_id,
            "start_date": "2026-03-08",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Task with comments",
            "start_date": "2026-03-08",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    return project_id, task_id


async def _create_task(client: AsyncClient, project_id: str, name: str) -> str:
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": name,
            "start_date": "2026-03-08",
            "duration": 480,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.asyncio
async def test_task_endpoints_return_comment_counts(client: AsyncClient) -> None:
    await _register_and_login(
        client, "task-service-comments@example.com", "Task Service User"
    )
    project_id, task_id = await _create_project_and_task(client)

    initial_task_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert initial_task_response.status_code == 200, initial_task_response.text
    assert initial_task_response.json()["comments_count"] == 0

    parent_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": "Parent comment",
            "parent_comment_id": None,
        },
    )
    assert parent_response.status_code == 201, parent_response.text
    parent_comment_id = parent_response.json()["id"]

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

    detail_response = await client.get(f"/api/v1/projects/{project_id}/tasks/{task_id}")
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["comments_count"] == 2

    list_response = await client.get(f"/api/v1/projects/{project_id}/tasks")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["items"][0]["comments_count"] == 2

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"name": "Renamed task"},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["comments_count"] == 2

    delete_response = await client.delete(f"/api/v1/comments/{parent_comment_id}")
    assert delete_response.status_code == 204, delete_response.text

    after_delete_detail = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert after_delete_detail.status_code == 200, after_delete_detail.text
    assert after_delete_detail.json()["comments_count"] == 0


@pytest.mark.asyncio
async def test_delete_task_soft_deletes_task_comments(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await _register_and_login(
        client, "task-service-delete-comments@example.com", "Task Delete User"
    )
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
    assert parent_response.status_code == 201, parent_response.text

    delete_task_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert delete_task_response.status_code == 204, delete_task_response.text

    deleted_task_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert deleted_task_response.status_code == 404, deleted_task_response.text

    deleted_task_comments_response = await client.get(
        f"/api/v1/comments/entity/task/{task_id}"
    )
    assert deleted_task_comments_response.status_code == 404, (
        deleted_task_comments_response.text
    )

    comment_rows_result = await session.execute(
        select(Comment).where(
            Comment.entity_type == "task",
            Comment.entity_id == uuid.UUID(task_id),
        )
    )
    comment_rows = list(comment_rows_result.scalars().all())
    assert comment_rows
    assert all(comment.is_deleted for comment in comment_rows)


@pytest.mark.asyncio
async def test_task_hierarchy_endpoints_keep_comment_count(
    client: AsyncClient,
) -> None:
    await _register_and_login(
        client, "task-service-hierarchy-comments@example.com", "Task Hierarchy User"
    )
    project_id, task_one_id = await _create_project_and_task(client)
    task_two_id = await _create_task(client, project_id, "Task Two")
    task_three_id = await _create_task(client, project_id, "Task Three")

    comment_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_two_id,
            "content": "Hierarchy comment",
            "parent_comment_id": None,
        },
    )
    assert comment_response.status_code == 201, comment_response.text

    indent_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_two_id}/indent"
    )
    assert indent_response.status_code == 200, indent_response.text
    assert indent_response.json()["comments_count"] == 1

    outdent_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_two_id}/outdent"
    )
    assert outdent_response.status_code == 200, outdent_response.text
    assert outdent_response.json()["comments_count"] == 1

    reorder_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_two_id}/reorder",
        json={
            "after_task_id": task_three_id,
            "before_task_id": None,
            "new_parent_id": None,
        },
    )
    assert reorder_response.status_code == 200, reorder_response.text
    assert reorder_response.json()["comments_count"] == 1

    detail_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_two_id}"
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["comments_count"] == 1
