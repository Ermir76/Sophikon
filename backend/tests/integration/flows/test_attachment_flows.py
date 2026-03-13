"""
Integration flow tests for task attachment collaboration behavior.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.config import settings
from app.models.role import Role
from tests.fixtures.project_members import add_project_member


def _slug(prefix: str) -> str:
    return f"{prefix}-{str(uuid7()).split('-')[0]}"


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


async def _create_project_and_task(client: AsyncClient, suffix: str) -> tuple[str, str]:
    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Attachment Org {suffix}", "slug": _slug(f"att-org-{suffix}")},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Attachment Project {suffix}",
            "organization_id": org_id,
            "start_date": "2026-03-13",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Attachment Flow Task",
            "start_date": "2026-03-13",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project_id, task_response.json()["id"]


async def _ensure_project_roles(session: AsyncSession) -> None:
    for role_name in ["owner", "manager", "member", "viewer"]:
        existing = await session.execute(select(Role).where(Role.name == role_name))
        if existing.scalar_one_or_none() is None:
            session.add(Role(name=role_name, scope="project"))
    await session.commit()


@pytest.mark.asyncio
async def test_attachment_flow_member_collaboration_and_non_member_denied(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    await _ensure_project_roles(session)
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    await _register(client, "attach-flow-owner@example.com", "Attachment Flow Owner")
    await _login(client, "attach-flow-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "flow")

    upload_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("design.pdf", b"%PDF-1.4 flow", "application/pdf")},
    )
    assert upload_response.status_code == 201, upload_response.text
    attachment = upload_response.json()

    await _register(client, "attach-flow-member@example.com", "Attachment Flow Member")
    await add_project_member(
        session, project_id, "attach-flow-member@example.com", "member"
    )
    await _login(client, "attach-flow-member@example.com")

    member_list_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert member_list_response.status_code == 200, member_list_response.text
    assert len(member_list_response.json()) == 1

    member_download_response = await client.get(attachment["download_url"])
    assert member_download_response.status_code == 200, member_download_response.text
    assert member_download_response.content == b"%PDF-1.4 flow"

    member_delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments/{attachment['id']}"
    )
    assert member_delete_response.status_code == 204, member_delete_response.text

    list_after_delete_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert list_after_delete_response.status_code == 200, (
        list_after_delete_response.text
    )
    assert list_after_delete_response.json() == []

    await _register(
        client, "attach-flow-outsider@example.com", "Attachment Flow Outsider"
    )
    await _login(client, "attach-flow-outsider@example.com")
    outsider_list_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert outsider_list_response.status_code == 403, outsider_list_response.text
