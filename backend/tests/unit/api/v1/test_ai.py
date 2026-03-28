import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_member import ProjectMember
from app.models.role import Role
from app.models.user import User

TEST_PASSWORD = "StrongPassword123!"


async def _register_user(client: AsyncClient, email: str, full_name: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text


async def _login_user(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text


async def _create_project(client: AsyncClient, email: str, slug: str) -> str:
    await _register_user(client, email, "AI Owner")

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "AI Project",
            "organization_id": org_id,
            "start_date": "2026-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


async def _add_project_member(
    session: AsyncSession,
    *,
    project_id: str,
    user_email: str,
    role_name: str,
) -> None:
    user = (
        await session.execute(select(User).where(User.email == user_email))
    ).scalar_one()
    role = (
        await session.execute(select(Role).where(Role.name == role_name))
    ).scalar_one()

    session.add(
        ProjectMember(
            project_id=uuid.UUID(project_id),
            user_id=user.id,
            role_id=role.id,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient):
    response = await client.post(
        f"/api/v1/projects/{uuid.uuid4()}/ai/chat",
        json={"message": "What is the project status?"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_streams_for_viewer(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
    monkeypatch: pytest.MonkeyPatch,
):
    project_id = await _create_project(client, "ai-owner@example.com", "org-ai-chat")
    await _register_user(client, "ai-viewer@example.com", "AI Viewer")
    await _add_project_member(
        session,
        project_id=project_id,
        user_email="ai-viewer@example.com",
        role_name="viewer",
    )

    async def fake_prepare_chat_stream(db, project, user, role_name, body):
        assert str(project.id) == project_id
        assert user.email == "ai-viewer@example.com"
        assert role_name == "viewer"
        assert body.message == "Status?"

        async def _stream():
            yield 'data: {"type":"start","conversation_id":"conv-1"}\n\n'
            yield 'data: {"type":"chunk","content":"Project summary"}\n\n'
            yield 'data: {"type":"done"}\n\n'

        return _stream()

    monkeypatch.setattr(
        "app.api.v1.endpoints.ai.ai_service.prepare_chat_stream",
        fake_prepare_chat_stream,
    )

    response = await client.post(
        f"/api/v1/projects/{project_id}/ai/chat",
        json={"message": "Status?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"type":"start","conversation_id":"conv-1"}' in response.text
    assert 'data: {"type":"chunk","content":"Project summary"}' in response.text


@pytest.mark.asyncio
async def test_estimate_forbidden_for_viewer(
    client: AsyncClient,
    session: AsyncSession,
    setup_roles,
):
    project_id = await _create_project(
        client, "ai-owner-estimate@example.com", "org-ai-estimate"
    )
    await _register_user(client, "ai-viewer-estimate@example.com", "AI Viewer")
    await _add_project_member(
        session,
        project_id=project_id,
        user_email="ai-viewer-estimate@example.com",
        role_name="viewer",
    )

    response = await client.post(
        f"/api/v1/projects/{project_id}/ai/estimate",
        json={"task_name": "Review release plan"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_suggestions_forbidden_for_non_member(client: AsyncClient):
    project_id = await _create_project(
        client, "ai-owner-suggestions@example.com", "org-ai-suggestions"
    )

    await _register_user(client, "ai-intruder@example.com", "AI Intruder")

    response = await client.get(f"/api/v1/projects/{project_id}/ai/suggestions")

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path_suffix", "json_body", "service_path"),
    [
        (
            "post",
            "chat",
            {"message": "Status?"},
            "app.api.v1.endpoints.ai.ai_service.prepare_chat_stream",
        ),
        (
            "post",
            "estimate",
            {"task_name": "Review release plan"},
            "app.api.v1.endpoints.ai.ai_service.estimate_for_project",
        ),
        (
            "get",
            "suggestions",
            None,
            "app.api.v1.endpoints.ai.ai_service.suggestions_for_project",
        ),
    ],
)
async def test_ai_endpoints_forbid_access_to_other_project(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path_suffix: str,
    json_body: dict[str, str] | None,
    service_path: str,
):
    project_a_id = await _create_project(
        client, "ai-owner-a@example.com", "org-ai-isolation-a"
    )
    project_b_id = await _create_project(
        client, "ai-owner-b@example.com", "org-ai-isolation-b"
    )

    assert project_a_id != project_b_id

    await _login_user(client, "ai-owner-a@example.com")

    called = False

    async def _unexpected_call(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("AI service should not run for cross-project access")

    monkeypatch.setattr(service_path, _unexpected_call)

    request = getattr(client, method)
    if json_body is None:
        response = await request(f"/api/v1/projects/{project_b_id}/ai/{path_suffix}")
    else:
        response = await request(
            f"/api/v1/projects/{project_b_id}/ai/{path_suffix}",
            json=json_body,
        )

    assert response.status_code == 403
    assert called is False
