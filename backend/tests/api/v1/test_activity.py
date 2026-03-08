import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.enums import AuditAction
from app.models.user import User
from tests.api.v1.conftest import add_project_member


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
    org_slug: str,
    project_name: str,
) -> str:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {org_slug}", "slug": org_slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": project_name,
            "organization_id": org_id,
            "start_date": "2026-03-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


@pytest.mark.asyncio
async def test_task_create_update_delete_produce_activity_records(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = "activity-owner@example.com"
    await _register_user(client, owner_email, "Activity Owner")
    project_id = await _create_project(
        client,
        org_slug="activity-org",
        project_name="Activity Test",
    )

    create_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Design homepage",
            "start_date": "2026-03-02",
            "duration": 480,
        },
    )
    assert create_response.status_code == 201, create_response.text
    task_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"percent_complete": 25},
    )
    assert update_response.status_code == 200, update_response.text

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}"
    )
    assert delete_response.status_code == 204, delete_response.text

    activity_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"entity_type": "task"},
    )
    assert activity_response.status_code == 200, activity_response.text
    payload = activity_response.json()
    assert payload["total"] == 3
    assert [item["action"] for item in payload["items"]] == [
        "deleted",
        "updated",
        "created",
    ]
    assert payload["items"][1]["changes"]["fields"] == [
        {"field": "percent_complete", "old": 0, "new": 25}
    ]

    user_result = await session.execute(select(User).where(User.email == owner_email))
    owner = user_result.scalar_one()
    filtered_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"user_id": str(owner.id), "action": "deleted"},
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered_payload = filtered_response.json()
    assert filtered_payload["total"] == 1
    assert filtered_payload["items"][0]["action"] == "deleted"


@pytest.mark.asyncio
async def test_member_activity_endpoints_are_logged_and_project_members_can_read(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    setup_roles,
):
    owner_email = "activity-owner-members@example.com"
    member_email = "activity-member@example.com"
    viewer_email = "activity-viewer@example.com"
    outsider_email = "activity-outsider@example.com"

    await _register_user(client, owner_email, "Owner")
    project_id = await _create_project(
        client,
        org_slug="activity-members-org",
        project_name="Activity Members Test",
    )
    await _register_user(client, member_email, "Team Member")
    await _register_user(client, viewer_email, "Viewer")
    await _register_user(client, outsider_email, "Outsider")
    await add_project_member(session, project_id, member_email, "member")
    await add_project_member(session, project_id, viewer_email, "viewer")
    await _login_user(client, owner_email)

    async def _fake_send(**kwargs):
        _ = kwargs

    monkeypatch.setattr(
        "app.api.v1.endpoints.project_members.project_member_service."
        "send_project_invitation_email_with_retry",
        _fake_send,
    )

    invite_response = await client.post(
        f"/api/v1/projects/{project_id}/members/invite",
        json={"email": "new-invitee@example.com", "role": "viewer"},
    )
    assert invite_response.status_code == 201, invite_response.text

    members_response = await client.get(f"/api/v1/projects/{project_id}/members")
    member_id = next(
        item["id"]
        for item in members_response.json()["items"]
        if item["user_email"] == member_email
    )

    role_response = await client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        json={"role": "viewer"},
    )
    assert role_response.status_code == 200, role_response.text

    remove_response = await client.delete(
        f"/api/v1/projects/{project_id}/members/{member_id}"
    )
    assert remove_response.status_code == 204, remove_response.text

    activity_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"entity_type": "project_member"},
    )
    assert activity_response.status_code == 200, activity_response.text
    payload = activity_response.json()
    assert payload["total"] == 3
    assert [item["action"] for item in payload["items"]] == [
        "deleted",
        "updated",
        "created",
    ]
    assert payload["items"][0]["entity_name"] == "Team Member"
    assert payload["items"][1]["changes"]["fields"] == [
        {"field": "role", "old": "member", "new": "viewer"}
    ]

    await _login_user(client, viewer_email)
    member_read_response = await client.get(f"/api/v1/projects/{project_id}/activity")
    assert member_read_response.status_code == 200, member_read_response.text

    await _login_user(client, outsider_email)
    outsider_response = await client.get(f"/api/v1/projects/{project_id}/activity")
    assert outsider_response.status_code == 403


@pytest.mark.asyncio
async def test_project_create_delete_produce_activity_records(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = "activity-project-owner@example.com"
    await _register_user(client, owner_email, "Project Activity Owner")

    project_name = "Project Activity Lifecycle"
    project_id = await _create_project(
        client,
        org_slug="activity-project-org",
        project_name=project_name,
    )

    delete_response = await client.delete(f"/api/v1/projects/{project_id}")
    assert delete_response.status_code == 204, delete_response.text

    result = await session.execute(
        select(ActivityLog)
        .where(
            ActivityLog.project_id == uuid.UUID(project_id),
            ActivityLog.entity_type == "project",
        )
        .order_by(ActivityLog.created_at.asc(), ActivityLog.id.asc())
    )
    entries = list(result.scalars().all())

    assert [entry.action for entry in entries] == [
        AuditAction.CREATED,
        AuditAction.DELETED,
    ]
    assert [entry.entity_name for entry in entries] == [project_name, project_name]


@pytest.mark.asyncio
async def test_resource_create_delete_produce_activity_records(
    client: AsyncClient,
):
    await _register_user(
        client, "activity-resource-owner@example.com", "Resource Owner"
    )
    project_id = await _create_project(
        client,
        org_slug="activity-resource-org",
        project_name="Resource Activity Test",
    )

    create_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Lead Engineer", "max_units": 1.0},
    )
    assert create_response.status_code == 201, create_response.text
    resource_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/resources/{resource_id}"
    )
    assert delete_response.status_code == 204, delete_response.text

    activity_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"entity_type": "resource"},
    )
    assert activity_response.status_code == 200, activity_response.text
    payload = activity_response.json()

    assert payload["total"] == 2
    assert [item["action"] for item in payload["items"]] == ["deleted", "created"]
    assert [item["entity_name"] for item in payload["items"]] == [
        "Lead Engineer",
        "Lead Engineer",
    ]


@pytest.mark.asyncio
async def test_assignment_create_delete_produce_activity_records(
    client: AsyncClient,
):
    await _register_user(
        client,
        "activity-assignment-owner@example.com",
        "Assignment Owner",
    )
    project_id = await _create_project(
        client,
        org_slug="activity-assignment-org",
        project_name="Assignment Activity Test",
    )

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Design homepage",
            "start_date": "2026-03-02",
            "duration": 480,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    resource_response = await client.post(
        f"/api/v1/projects/{project_id}/resources",
        json={"name": "Lead Engineer", "max_units": 1.0},
    )
    assert resource_response.status_code == 201, resource_response.text
    resource_id = resource_response.json()["id"]

    create_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assignments",
        json={
            "resource_id": resource_id,
            "units": 1.0,
            "start_date": "2026-03-02",
            "finish_date": "2026-03-02",
        },
    )
    assert create_response.status_code == 201, create_response.text
    assignment_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/assignments/{assignment_id}")
    assert delete_response.status_code == 204, delete_response.text

    activity_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"entity_type": "assignment"},
    )
    assert activity_response.status_code == 200, activity_response.text
    payload = activity_response.json()

    assert payload["total"] == 2
    assert [item["action"] for item in payload["items"]] == ["deleted", "created"]
    assert [item["entity_name"] for item in payload["items"]] == [
        "Lead Engineer -> Design homepage",
        "Lead Engineer -> Design homepage",
    ]


@pytest.mark.asyncio
async def test_dependency_create_delete_produce_activity_records(
    client: AsyncClient,
):
    await _register_user(
        client,
        "activity-dependency-owner@example.com",
        "Dependency Owner",
    )
    project_id = await _create_project(
        client,
        org_slug="activity-dependency-org",
        project_name="Dependency Activity Test",
    )

    predecessor_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Predecessor",
            "start_date": "2026-03-02",
            "duration": 480,
        },
    )
    assert predecessor_response.status_code == 201, predecessor_response.text
    predecessor_id = predecessor_response.json()["id"]

    successor_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Successor",
            "start_date": "2026-03-03",
            "duration": 480,
        },
    )
    assert successor_response.status_code == 201, successor_response.text
    successor_id = successor_response.json()["id"]

    create_response = await client.post(
        f"/api/v1/projects/{project_id}/dependencies",
        json={
            "predecessor_id": predecessor_id,
            "successor_id": successor_id,
            "type": "FS",
        },
    )
    assert create_response.status_code == 201, create_response.text
    dependency_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/dependencies/{dependency_id}"
    )
    assert delete_response.status_code == 204, delete_response.text

    activity_response = await client.get(
        f"/api/v1/projects/{project_id}/activity",
        params={"entity_type": "dependency"},
    )
    assert activity_response.status_code == 200, activity_response.text
    payload = activity_response.json()

    assert payload["total"] == 2
    assert [item["action"] for item in payload["items"]] == ["deleted", "created"]
    assert [item["entity_name"] for item in payload["items"]] == [
        "Predecessor -> Successor",
        "Predecessor -> Successor",
    ]
