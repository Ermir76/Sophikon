import json
import uuid
from uuid import UUID

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.core.exceptions import InvalidOperationError, NotFoundError
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.ai_usage import AIUsage
from app.models.enums import AIMessageRole, ProjectStatus
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.service import ai_service
from app.service.contracts.ai import (
    AIChatEvent,
    AIChatInput,
    AIEstimateInput,
    AIProviderChatRequest,
    AIProviderEstimateRequest,
    AIProviderSuggestionsRequest,
    AIUsageMeta,
)


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


async def _seed_project_with_task(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str,
    slug: str,
) -> tuple[User, Project, Task]:
    await _register_user(client, email, "AI Service User")

    org_response = await client.post(
        "/api/v1/organizations",
        json={"name": f"Org {slug}", "slug": slug},
    )
    assert org_response.status_code == 201, org_response.text
    org_id = org_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "AI Service Project",
            "organization_id": org_id,
            "start_date": "2026-01-01",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = uuid.UUID(project_response.json()["id"])

    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "name": "Prepare launch notes",
            "notes": "Coordinate release details",
            "start_date": "2026-01-02",
            "duration": 960,
        },
    )
    assert task_response.status_code == 201, task_response.text
    task_id = uuid.UUID(task_response.json()["id"])

    user = (await session.execute(select(User).where(User.email == email))).scalar_one()
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one()
    task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one()
    return user, project, task


def _service_project_context_payload() -> dict:
    return {
        "project_id": str(uuid.uuid4()),
        "name": "AI Reliability Project",
        "status": "ACTIVE",
        "start_date": "2026-01-01",
        "finish_date": None,
        "updated_at": "2026-01-02T00:00:00Z",
        "tasks": [],
    }


@pytest.mark.asyncio
async def test_build_project_context_includes_project_status_and_tasks(
    client: AsyncClient,
    session: AsyncSession,
):
    _, project, task = await _seed_project_with_task(
        client,
        session,
        email="ai-context@example.com",
        slug="org-ai-context",
    )

    project.status = ProjectStatus.ACTIVE
    await session.commit()
    await session.refresh(project)

    context = await ai_service.build_project_context(session, project)

    assert context.project_id == project.id
    assert context.status == "ACTIVE"
    assert context.tasks[0].id == task.id
    assert context.tasks[0].name == "Prepare launch notes"
    assert context.tasks[0].notes == "Coordinate release details"


@pytest.mark.asyncio
async def test_prepare_chat_stream_creates_conversation_and_user_message(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, project, _ = await _seed_project_with_task(
        client,
        session,
        email="ai-chat-stream@example.com",
        slug="org-ai-chat-stream",
    )

    async def fake_stream_chat(body):
        assert body.project_context.project_id == project.id
        yield AIChatEvent(type="start")
        yield AIChatEvent(type="chunk", content="All clear.")
        yield AIChatEvent(
            type="done",
            usage=AIUsageMeta(tokens_in=4, tokens_out=6, model="mock-brain"),
            model="mock-brain",
        )

    async def fake_finalize_chat(**kwargs):
        return None

    monkeypatch.setattr(ai_service, "stream_chat", fake_stream_chat)
    monkeypatch.setattr(ai_service, "_finalize_chat", fake_finalize_chat)

    stream = await ai_service.prepare_chat_stream(
        session,
        project=project,
        user_id=user.id,
        body=AIChatInput(message="How are we doing?"),
    )
    payloads = [chunk async for chunk in stream]

    conversations = list(
        (
            await session.execute(
                select(AIConversation).where(
                    AIConversation.project_id == project.id,
                    AIConversation.user_id == user.id,
                )
            )
        ).scalars()
    )
    assert len(conversations) == 1  # exactly 1 conversation created
    conversation = conversations[-1]

    messages = list(
        (
            await session.execute(
                select(AIMessage)
                .where(AIMessage.conversation_id == conversation.id)
                .order_by(AIMessage.created_at.asc())
            )
        ).scalars()
    )

    assert len(payloads) == 3
    assert str(conversation.id) in payloads[0]
    assert json.loads(payloads[1].removeprefix("data: ").strip()) == {
        "type": "chunk",
        "content": "All clear.",
    }
    assert len(messages) == 1
    assert messages[0].role == AIMessageRole.USER
    assert messages[0].content == "How are we doing?"


def test_ai_schema_accepts_uuid_utils_uuid_values():
    conversation_id = uuid7()
    message_id = uuid7()
    user_id = uuid7()
    project_id = uuid7()

    request = AIProviderChatRequest(
        message="Hello",
        project_context={
            "project_id": project_id,
            "name": "AI Project",
            "status": "ACTIVE",
            "start_date": "2026-01-01",
            "finish_date": None,
            "updated_at": "2026-01-02T00:00:00Z",
            "tasks": [],
        },
        conversation_id=conversation_id,
        user_id=user_id,
    )
    event = AIChatEvent(
        type="start",
        conversation_id=conversation_id,
        message_id=message_id,
    )

    assert request.conversation_id == UUID(str(conversation_id))
    assert request.user_id == UUID(str(user_id))
    assert event.model_dump(mode="json", exclude_none=True) == {
        "type": "start",
        "conversation_id": str(conversation_id),
        "message_id": str(message_id),
    }


@pytest.mark.asyncio
async def test_estimate_for_project_builds_task_inputs_and_tracks_usage(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    user, project, task = await _seed_project_with_task(
        client,
        session,
        email="ai-estimate@example.com",
        slug="org-ai-estimate-service",
    )
    captured = {}

    async def fake_request_estimate(body):
        captured["body"] = body
        return {
            "estimates": [
                {
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "optimistic_minutes": 480,
                    "likely_minutes": 960,
                    "pessimistic_minutes": 1440,
                    "recommended_minutes": 960,
                    "confidence": 0.72,
                    "reasoning": "Based on similar release prep tasks.",
                }
            ],
            "usage": {
                "tokens_in": 7,
                "tokens_out": 13,
                "model": "mock-estimator",
            },
        }

    monkeypatch.setattr(ai_service, "request_estimate", fake_request_estimate)

    response = await ai_service.estimate_for_project(
        session,
        project=project,
        user_id=user.id,
        body=AIEstimateInput(task_ids=[task.id], include_reasoning=True),
    )

    usage_rows = list(
        (
            await session.execute(select(AIUsage).where(AIUsage.user_id == user.id))
        ).scalars()
    )

    assert captured["body"].task_inputs[0].task_id == task.id
    assert captured["body"].task_inputs[0].task_name == task.name
    assert captured["body"].project_context.project_id == project.id
    assert response.estimates[0].task_id == task.id
    assert len(usage_rows) == 1
    assert usage_rows[0].feature == "estimation"
    assert usage_rows[0].tokens_in == 7
    assert usage_rows[0].tokens_out == 13


@pytest.mark.asyncio
async def test_estimate_for_project_rejects_missing_task_ids(
    client: AsyncClient,
    session: AsyncSession,
):
    user, project, _ = await _seed_project_with_task(
        client,
        session,
        email="ai-missing-task@example.com",
        slug="org-ai-missing-task",
    )

    with pytest.raises(NotFoundError, match="One or more tasks were not found"):
        await ai_service.estimate_for_project(
            session,
            project=project,
            user_id=user.id,
            body=AIEstimateInput(task_ids=[uuid.uuid4()]),
        )


@pytest.mark.asyncio
async def test_stream_chat_emits_error_event_for_malformed_sse_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeStreamResponse:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def aiter_lines(self):
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': str(uuid.uuid4())})}"
            yield "data: {bad-json"

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def stream(self, *args, **kwargs):
            return FakeStreamResponse()

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", FakeAsyncClient)

    events = [
        event
        async for event in ai_service.stream_chat(
            AIProviderChatRequest(
                message="Status?",
                project_context=_service_project_context_payload(),
                conversation_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
        )
    ]

    assert events[0].type == "start"
    assert events[1] == AIChatEvent(
        type="error",
        error="Malformed AI stream event",
    )


@pytest.mark.asyncio
async def test_stream_chat_raises_invalid_operation_when_ai_service_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
):
    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def stream(self, *args, **kwargs):
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", FailingAsyncClient)

    with pytest.raises(InvalidOperationError, match="AI service is unavailable"):
        events = ai_service.stream_chat(
            AIProviderChatRequest(
                message="Status?",
                project_context=_service_project_context_payload(),
                conversation_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )
        )
        async for _ in events:
            pass


@pytest.mark.asyncio
async def test_request_estimate_rejects_malformed_ai_response(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeResponse:
        status_code = 200

        def json(self):
            raise json.JSONDecodeError("Expecting value", "", 0)

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(InvalidOperationError, match="Malformed AI estimation response"):
        await ai_service.request_estimate(
            AIProviderEstimateRequest(
                project_context=_service_project_context_payload(),
                task_inputs=[
                    {
                        "task_id": uuid.uuid4(),
                        "task_name": "Estimate release prep",
                        "task_description": "Prepare release",
                        "duration": 480,
                    }
                ],
                include_reasoning=True,
            )
        )


@pytest.mark.asyncio
async def test_request_suggestions_rejects_malformed_ai_response(
    monkeypatch: pytest.MonkeyPatch,
):
    class FakeResponse:
        status_code = 200

        def json(self):
            raise json.JSONDecodeError("Expecting value", "", 0)

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(ai_service.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(
        InvalidOperationError,
        match="Malformed AI suggestions response",
    ):
        await ai_service.request_suggestions(
            AIProviderSuggestionsRequest(
                project_context=_service_project_context_payload(),
                limit=5,
            )
        )
