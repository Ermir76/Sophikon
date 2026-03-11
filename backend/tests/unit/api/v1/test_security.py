"""
Security-focused API contract tests.
"""

import uuid

import pytest
from httpx import AsyncClient
from limits import parse
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.wrappers import Limit
from starlette.requests import Request

from app.core.rate_limit import rate_limit_exceeded_handler


async def _register_and_login(client: AsyncClient, suffix: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"security_{suffix}@x.com",
            "password": "StrongPassword123!",
            "full_name": f"Security {suffix}",
        },
    )
    assert response.status_code == 201, response.text


async def _create_project(client: AsyncClient, suffix: str) -> str:
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": f"Security Org {suffix}",
            "slug": f"security-org-{suffix}-{uuid.uuid4().hex[:8]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Security Project {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


@pytest.mark.asyncio
async def test_sql_injection_in_task_name_sanitized(client: AsyncClient) -> None:
    """Task name with SQL-looking payload is stored as plain text."""
    await _register_and_login(client, "sql-injection")
    project_id = await _create_project(client, "sql-injection")
    sql_payload = "'; DROP TABLE task;--"

    create_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": sql_payload,
            "start_date": "2024-01-01",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert create_response.status_code == 201, create_response.text
    task_id = create_response.json()["id"]
    assert create_response.json()["name"] == sql_payload

    get_response = await client.get(f"/api/v1/projects/{project_id}/tasks/{task_id}")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["name"] == sql_payload


@pytest.mark.asyncio
async def test_sql_like_project_name_stored_as_literal_text(
    client: AsyncClient,
) -> None:
    """Project names with SQL-like content are persisted as plain text."""
    await _register_and_login(client, "sql-project-name")

    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Security Org SQL Name",
            "slug": f"security-org-name-{uuid.uuid4().hex[:8]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    sql_like_name = "Project'; DROP TABLE project;--"
    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": sql_like_name,
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]
    assert project_response.json()["name"] == sql_like_name

    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["name"] == sql_like_name


@pytest.mark.asyncio
async def test_sql_like_org_slug_payload_returns_422_not_500(
    client: AsyncClient,
) -> None:
    """
    SQL-like slug payload is rejected as invalid input (schema validation path).

    Security contract: malformed slug must not produce a 500.
    """
    await _register_and_login(client, "sql-org-slug")

    response = await client.post(
        "/api/v1/organizations",
        json={
            "name": "Security Org Bad Slug",
            "slug": "';drop-table-org;--",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_xss_payload_in_comment_stored_as_text(client: AsyncClient) -> None:
    """Comment content keeps script-like payload as literal text."""
    await _register_and_login(client, "xss-comment")
    project_id = await _create_project(client, "xss-comment")
    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Task For XSS Comment",
            "start_date": "2024-01-01",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    xss_payload = "<script>alert('xss')</script>"
    comment_response = await client.post(
        "/api/v1/comments",
        json={
            "entity_type": "task",
            "entity_id": task_id,
            "content": xss_payload,
            "parent_comment_id": None,
        },
    )
    assert comment_response.status_code == 201, comment_response.text
    assert comment_response.json()["content"] == xss_payload

    list_response = await client.get(f"/api/v1/comments/entity/task/{task_id}")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["data"][0]["content"] == xss_payload


@pytest.mark.asyncio
async def test_invalid_uuid_in_path_returns_422_not_500(client: AsyncClient) -> None:
    """Malformed UUID path params are validation errors, not server errors."""
    await _register_and_login(client, "invalid-uuid")

    response = await client.get("/api/v1/projects/not-a-uuid/tasks")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    """Allowed Origin receives explicit CORS allow-origin echo."""
    response = await client.get(
        "/",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )


@pytest.mark.asyncio
async def test_cors_blocks_unconfigured_origin(client: AsyncClient) -> None:
    """Unconfigured Origin does not receive allow-origin header."""
    response = await client.get(
        "/",
        headers={"Origin": "https://evil.example.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_auth_cookies_include_samesite_lax(client: AsyncClient) -> None:
    """Auth cookie contract includes SameSite=Lax for CSRF mitigation."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"security_cookie_{uuid.uuid4().hex[:8]}@x.com",
            "password": "StrongPassword123!",
            "full_name": "Security Cookie",
        },
    )
    assert response.status_code == 201, response.text

    set_cookie_values = response.headers.get_list("set-cookie")
    assert any(
        "SameSite=lax" in value or "SameSite=Lax" in value
        for value in set_cookie_values
    )


def test_rate_limit_exceeded_handler_returns_429_contract() -> None:
    """
    Pass-now rate-limit contract test.

    Global test fixtures disable the limiter to keep suites deterministic and to
    avoid hard Redis dependency. This test verifies the 429 error payload shape.
    """
    request = Request(
        scope={
            "type": "http",
            "asgi": {"version": "3.0"},
            "method": "GET",
            "path": "/api/v1/auth/login",
            "headers": [],
        }
    )
    limit = Limit(
        limit=parse("10/minute"),
        key_func=get_remote_address,
        scope=None,
        per_method=False,
        methods=None,
        error_message=None,
        exempt_when=None,
        cost=1,
        override_defaults=False,
    )
    response = rate_limit_exceeded_handler(request, RateLimitExceeded(limit))

    assert response.status_code == 429
    body = response.body.decode()
    assert "RATE_LIMIT_EXCEEDED" in body
    assert "Rate limit exceeded" in body


@pytest.mark.asyncio
async def test_oversized_request_body_rejected(client: AsyncClient) -> None:
    """Oversized JSON field payload is rejected by request schema validation."""
    await _register_and_login(client, "oversized-body")
    project_id = await _create_project(client, "oversized-body")

    # Intentionally >1MB to exercise oversized payload validation path.
    oversized_notes = "n" * 1_100_000
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Oversized Body Task",
            "start_date": "2024-01-01",
            "duration": 480,  # 1 working day (8h * 60min)
            "notes": oversized_notes,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401_not_500(
    client: AsyncClient,
) -> None:
    """Protected endpoints return 401 when no auth cookie is present."""
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")

    response = await client.get("/api/v1/organizations")
    assert response.status_code == 401
