import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.models.activity_log import ActivityLog
from app.models.enums import AuditAction, ResourceType
from app.models.user import User
from app.service import activity_log_service


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

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": project_name,
            "organization_id": org_response.json()["id"],
            "start_date": "2026-03-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    return project_response.json()["id"]


async def _get_user(session: AsyncSession, email: str) -> User:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one()


def test_build_change_set_serializes_supported_value_types():
    task_id = uuid.uuid4()
    timestamp = datetime(2026, 3, 8, 14, 30, tzinfo=UTC)

    changes = activity_log_service.build_change_set(
        before={
            "amount": Decimal("1.50"),
            "due_date": date(2026, 3, 10),
            "items": [Decimal("1.5"), task_id],
            "meta": {"state": AuditAction.CREATED},
            "state": ResourceType.WORK,
            "task_id": task_id,
            "timestamp": timestamp,
            "unchanged": "same",
        },
        after={
            "amount": Decimal("2.00"),
            "due_date": date(2026, 3, 12),
            "items": [Decimal("2.5"), task_id],
            "meta": {"state": AuditAction.UPDATED},
            "state": ResourceType.MATERIAL,
            "task_id": task_id,
            "timestamp": timestamp,
            "unchanged": "same",
        },
    )

    assert changes == {
        "fields": [
            {"field": "amount", "old": 1.5, "new": 2.0},
            {"field": "due_date", "old": "2026-03-10", "new": "2026-03-12"},
            {
                "field": "items",
                "old": [1.5, str(task_id)],
                "new": [2.5, str(task_id)],
            },
            {
                "field": "meta",
                "old": {"state": "created"},
                "new": {"state": "updated"},
            },
            {"field": "state", "old": "WORK", "new": "MATERIAL"},
        ]
    }


@pytest.mark.asyncio
async def test_list_activity_filters_and_paginates_results(
    client: AsyncClient,
    session: AsyncSession,
):
    owner_email = _unique_email("activity-service-owner@example.com")
    reviewer_email = _unique_email("activity-service-reviewer@example.com")

    await _register_user(client, owner_email, "Activity Service Owner")
    project_id = await _create_project(
        client,
        org_slug=_unique_slug("activity-service-org"),
        project_name="Activity Service Project",
    )
    await _register_user(client, reviewer_email, "Activity Reviewer")

    owner = await _get_user(session, owner_email)
    reviewer = await _get_user(session, reviewer_email)
    project_uuid = uuid.UUID(project_id)

    await session.execute(
        delete(ActivityLog).where(ActivityLog.project_id == project_uuid)
    )

    created_entry = await activity_log_service.log_activity(
        session,
        project_id=project_uuid,
        action=AuditAction.CREATED,
        entity_type="task",
        entity_name="Kickoff",
        context=activity_log_service.ActivityContext(user_id=owner.id),
    )
    updated_entry = await activity_log_service.log_activity(
        session,
        project_id=project_uuid,
        action=AuditAction.UPDATED,
        entity_type="task",
        entity_name="Kickoff",
        changes=activity_log_service.build_change_set(
            {"percent_complete": 10},
            {"percent_complete": 25},
        ),
        context=activity_log_service.ActivityContext(user_id=owner.id),
    )
    deleted_entry = await activity_log_service.log_activity(
        session,
        project_id=project_uuid,
        action=AuditAction.DELETED,
        entity_type="resource",
        entity_name="Lead Engineer",
        context=activity_log_service.ActivityContext(user_id=reviewer.id),
    )

    created_entry.created_at = datetime(2026, 3, 8, 10, 0, tzinfo=UTC)
    updated_entry.created_at = datetime(2026, 3, 8, 11, 0, tzinfo=UTC)
    deleted_entry.created_at = datetime(2026, 3, 8, 12, 0, tzinfo=UTC)
    await session.commit()

    page_one_items, total = await activity_log_service.list_activity(
        session,
        project_id=project_uuid,
        page=1,
        per_page=2,
    )

    assert total == 3
    assert [item["action"] for item in page_one_items] == [
        AuditAction.DELETED,
        AuditAction.UPDATED,
    ]
    assert [item["entity_name"] for item in page_one_items] == [
        "Lead Engineer",
        "Kickoff",
    ]
    assert page_one_items[0]["user"] is not None
    assert page_one_items[0]["user"]["full_name"] == "Activity Reviewer"
    assert page_one_items[1]["changes"] is not None
    assert page_one_items[1]["changes"]["fields"] == [
        {"field": "percent_complete", "old": 10, "new": 25}
    ]

    page_two_items, page_two_total = await activity_log_service.list_activity(
        session,
        project_id=project_uuid,
        page=2,
        per_page=2,
    )

    assert page_two_total == 3
    assert [item["action"] for item in page_two_items] == [AuditAction.CREATED]
    assert page_two_items[0]["user"] is not None
    assert page_two_items[0]["user"]["id"] == owner.id

    filtered_items, filtered_total = await activity_log_service.list_activity(
        session,
        project_id=project_uuid,
        page=1,
        per_page=50,
        user_id=owner.id,
        entity_type="task",
        action=AuditAction.UPDATED,
    )

    assert filtered_total == 1
    assert len(filtered_items) == 1
    assert filtered_items[0]["action"] == AuditAction.UPDATED
    assert filtered_items[0]["entity_type"] == "task"
    assert filtered_items[0]["user"] is not None
    assert filtered_items[0]["user"]["id"] == owner.id
