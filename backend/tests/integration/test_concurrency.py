"""
Concurrency regression tests for critical backend race windows.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import database
from app.main import app


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


async def _setup_project(client: AsyncClient, suffix: str) -> tuple[str, str]:
    slug = f"{suffix.lower().replace('_', '-')}-{uuid.uuid4().hex[:8]}"
    owner_email = f"concurrency_{slug}@x.com"
    await _register(
        client,
        email=owner_email,
        full_name=f"Concurrency {suffix}",
    )
    org_response = await client.post(
        "/api/v1/organizations",
        json={
            "name": f"Concurrency Org {suffix}",
            "slug": f"concurrency-org-{slug}-{uuid.uuid4().hex[:6]}",
        },
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Concurrency Project {suffix}",
            "organization_id": org_id,
            "start_date": "2024-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"], owner_email


async def _create_task(client: AsyncClient, project_id: str, name: str) -> dict:
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": name,
            "start_date": "2024-01-01",
            "duration": 480,  # 1 working day (8h * 60min)
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture(autouse=True)
async def _reset_global_asyncpg_pool_per_test() -> AsyncGenerator[None]:
    """
    Keep asyncpg connections bound to the active asyncio event loop.

    These tests use the app's global SQLAlchemy async engine (not the savepoint
    test fixture engine). On Windows/Proactor loops, reusing pooled asyncpg
    connections across test-loop boundaries can raise `AttributeError:
    'NoneType' object has no attribute 'send'`. Disposing the pool around each
    test ensures new loop-local connections.
    """
    await database.engine.dispose()
    yield
    await database.engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_task_creation_same_project_keeps_order_indices_unique() -> (
    None
):
    """Concurrent creates on one project should not produce duplicate order_index values."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as owner_client:
        project_id, _ = await _setup_project(owner_client, "task-create-lock")

        async def _create(index: int):
            return await owner_client.post(
                f"/api/v1/projects/{project_id}/tasks",
                json={
                    "name": f"Concurrent Task {index}",
                    "start_date": "2024-01-01",
                    "duration": 480,  # 1 working day (8h * 60min)
                },
            )

        responses = await asyncio.gather(*[_create(i) for i in range(1, 11)])
        assert all(resp.status_code == 201 for resp in responses)

        list_response = await owner_client.get(f"/api/v1/projects/{project_id}/tasks")
        assert list_response.status_code == 200, list_response.text
        items = [
            item
            for item in list_response.json()["items"]
            if item["name"].startswith("Concurrent Task ")
        ]
        assert len(items) == 10
        order_indexes = [item["order_index"] for item in items]
        assert len(order_indexes) == len(set(order_indexes))


@pytest.mark.asyncio
async def test_concurrent_schedule_recalculation_stays_consistent() -> None:
    """Parallel schedule calculations must not corrupt final schedule state."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as owner_client:
        project_id, _ = await _setup_project(owner_client, "schedule-recalc")

        task_a = await _create_task(owner_client, project_id, "A")
        task_b = await _create_task(owner_client, project_id, "B")
        task_c = await _create_task(owner_client, project_id, "C")

        for pred, succ in [(task_a["id"], task_b["id"]), (task_b["id"], task_c["id"])]:
            dep_response = await owner_client.post(
                f"/api/v1/projects/{project_id}/dependencies",
                json={
                    "predecessor_id": pred,
                    "successor_id": succ,
                    "type": "FS",
                },
            )
            assert dep_response.status_code == 201, dep_response.text

        responses = await asyncio.gather(
            *[
                owner_client.post(f"/api/v1/projects/{project_id}/schedule/calculate")
                for _ in range(5)
            ]
        )
        assert all(resp.status_code == 200 for resp in responses)

        task_a_after = await owner_client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_a['id']}"
        )
        task_b_after = await owner_client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_b['id']}"
        )
        task_c_after = await owner_client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_c['id']}"
        )
        assert task_a_after.status_code == 200, task_a_after.text
        assert task_b_after.status_code == 200, task_b_after.text
        assert task_c_after.status_code == 200, task_c_after.text
        assert task_a_after.json()["start_date"] == "2024-01-01"
        assert task_b_after.json()["start_date"] == "2024-01-02"
        assert task_c_after.json()["start_date"] == "2024-01-03"


@pytest.mark.asyncio
async def test_concurrent_invitation_acceptance_allows_only_one_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent acceptance of the same invitation token is one-success only."""
    token = f"concurrency-invite-token-{uuid.uuid4().hex}"
    invitee_email = f"concurrency_invitee_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as owner_client:
        project_id, owner_email = await _setup_project(owner_client, "invite-race")
        await _register(owner_client, invitee_email, "Concurrency Invitee")
        monkeypatch.setattr(
            "app.service.project_member_service.secrets.token_urlsafe",
            lambda _: token,
        )
        await _login(owner_client, owner_email)

        invite_response = await owner_client.post(
            f"/api/v1/projects/{project_id}/members/invite",
            json={"email": invitee_email, "role": "member"},
        )
        assert invite_response.status_code == 201, invite_response.text

    async with (
        AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client_a,
        AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client_b,
    ):
        await _login(client_a, invitee_email)
        await _login(client_b, invitee_email)

        accept_a, accept_b = await asyncio.gather(
            client_a.post(
                "/api/v1/projects/members/invitations/accept",
                json={"token": token},
            ),
            client_b.post(
                "/api/v1/projects/members/invitations/accept",
                json={"token": token},
            ),
        )

    statuses = sorted([accept_a.status_code, accept_b.status_code])
    assert statuses == [200, 400]


@pytest.mark.asyncio
async def test_concurrent_wbs_regeneration_keeps_codes_unique() -> None:
    """Concurrent reorder operations should not leave duplicate WBS codes."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as owner_client:
        project_id, _ = await _setup_project(owner_client, "wbs-regen")
        task_a = await _create_task(owner_client, project_id, "WBS A")
        task_b = await _create_task(owner_client, project_id, "WBS B")
        task_c = await _create_task(owner_client, project_id, "WBS C")

        reorder_b = owner_client.post(
            f"/api/v1/projects/{project_id}/tasks/{task_b['id']}/reorder",
            json={
                "after_task_id": task_c["id"],
                "before_task_id": None,
                "new_parent_id": None,
            },
        )
        reorder_c = owner_client.post(
            f"/api/v1/projects/{project_id}/tasks/{task_c['id']}/reorder",
            json={
                "after_task_id": None,
                "before_task_id": task_a["id"],
                "new_parent_id": None,
            },
        )
        responses = await asyncio.gather(reorder_b, reorder_c)
        assert all(resp.status_code in {200, 400} for resp in responses)
        assert any(resp.status_code == 200 for resp in responses)

        list_response = await owner_client.get(f"/api/v1/projects/{project_id}/tasks")
        assert list_response.status_code == 200, list_response.text
        items = [
            item
            for item in list_response.json()["items"]
            if item["name"].startswith("WBS ")
        ]
        wbs_codes = [item["wbs_code"] for item in items]
        assert len(wbs_codes) == len(set(wbs_codes))
