import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.config import settings
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
        json={
            "name": f"Attachment Org {suffix}",
            "slug": _slug(f"attach-org-{suffix}"),
        },
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
            "name": "Attachment Task",
            "start_date": "2026-03-13",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert task_response.status_code == 201, task_response.text
    return project_id, task_response.json()["id"]


@pytest.mark.asyncio
async def test_attachment_upload_list_download_delete_roundtrip(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    await _register(client, "attach-owner@example.com", "Attachment Owner")
    await _login(client, "attach-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "roundtrip")

    upload_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("notes.txt", b"hello attachment", "text/plain")},
        data={"description": "Spec note"},
    )
    assert upload_response.status_code == 201, upload_response.text
    uploaded = upload_response.json()
    assert uploaded["file_name"] == "notes.txt"
    assert uploaded["file_size"] == 16
    assert uploaded["mime_type"] == "text/plain"
    assert uploaded["description"] == "Spec note"

    list_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["id"] == uploaded["id"]

    download_response = await client.get(uploaded["download_url"])
    assert download_response.status_code == 200, download_response.text
    assert download_response.content == b"hello attachment"
    assert download_response.headers["content-type"].startswith("text/plain")

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments/{uploaded['id']}"
    )
    assert delete_response.status_code == 204, delete_response.text

    list_after_delete_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert list_after_delete_response.status_code == 200, (
        list_after_delete_response.text
    )
    assert list_after_delete_response.json() == []


@pytest.mark.asyncio
async def test_attachment_upload_rejects_unsupported_content_type(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    await _register(client, "attach-type@example.com", "Attachment Type")
    await _login(client, "attach-type@example.com")
    project_id, task_id = await _create_project_and_task(client, "bad-type")

    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("script.sh", b"echo hi", "application/x-sh")},
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_attachment_upload_rejects_oversized_file(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")
    monkeypatch.setattr(settings, "MAX_ATTACHMENT_UPLOAD_BYTES", 8)

    await _register(client, "attach-size@example.com", "Attachment Size")
    await _login(client, "attach-size@example.com")
    project_id, task_id = await _create_project_and_task(client, "too-large")

    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("big.txt", b"123456789", "text/plain")},
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_attachment_access_controls_for_viewer_and_non_member(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "ATTACHMENT_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "ATTACHMENT_UPLOAD_SUBDIR", "attachments")

    await _register(client, "attach-ac-owner@example.com", "Attachment AC Owner")
    await _login(client, "attach-ac-owner@example.com")
    project_id, task_id = await _create_project_and_task(client, "access-control")

    upload_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("owner.txt", b"owner-file", "text/plain")},
    )
    assert upload_response.status_code == 201, upload_response.text
    download_url = upload_response.json()["download_url"]
    attachment_id = upload_response.json()["id"]

    await _register(client, "attach-ac-viewer@example.com", "Attachment Viewer")
    await add_project_member(
        session, project_id, "attach-ac-viewer@example.com", "viewer"
    )
    await _login(client, "attach-ac-viewer@example.com")

    viewer_upload_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments",
        files={"file": ("viewer.txt", b"viewer-file", "text/plain")},
    )
    assert viewer_upload_response.status_code == 403, viewer_upload_response.text

    viewer_list_response = await client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments"
    )
    assert viewer_list_response.status_code == 200, viewer_list_response.text
    assert len(viewer_list_response.json()) == 1

    viewer_download_response = await client.get(download_url)
    assert viewer_download_response.status_code == 200, viewer_download_response.text
    assert viewer_download_response.content == b"owner-file"

    viewer_delete_response = await client.delete(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert viewer_delete_response.status_code == 403, viewer_delete_response.text

    await _register(client, "attach-ac-outsider@example.com", "Attachment Outsider")
    await _login(client, "attach-ac-outsider@example.com")
    outsider_download_response = await client.get(download_url)
    assert outsider_download_response.status_code == 403, (
        outsider_download_response.text
    )
