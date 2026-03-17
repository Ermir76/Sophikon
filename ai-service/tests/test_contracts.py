import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schema import contracts


def _load_backend_schema_module():
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "backend" / "app" / "schema" / "ai.py"
    spec = importlib.util.spec_from_file_location("backend_ai_schema", schema_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load backend schema from {schema_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backend_ai = _load_backend_schema_module()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def service_headers():
    return {"X-AI-Service-Secret": settings.AI_SERVICE_SHARED_SECRET}


@pytest.fixture
def project_context_payload():
    return {
        "project_id": str(uuid4()),
        "name": "Apollo Rollout",
        "description": "Launch readiness and release coordination",
        "status": "ACTIVE",
        "start_date": "2026-03-01",
        "finish_date": "2026-03-31",
        "updated_at": "2026-03-07T10:15:00Z",
        "tasks": [
            {
                "id": str(uuid4()),
                "name": "QA regression pass",
                "notes": "Validate release candidate",
                "start_date": "2026-03-03",
                "finish_date": "2026-03-05",
                "duration": 960,
                "percent_complete": 50.0,
                "priority": 700,
                "is_summary": False,
                "updated_at": "2026-03-06T08:00:00Z",
            },
            {
                "id": str(uuid4()),
                "name": "Production release",
                "notes": "Deploy after QA sign-off",
                "start_date": "2026-03-06",
                "finish_date": "2026-03-06",
                "duration": 480,
                "percent_complete": 0.0,
                "priority": 850,
                "is_summary": False,
                "updated_at": "2026-03-06T09:00:00Z",
            },
        ],
    }


def test_complete_request_is_valid():
    request = contracts.CompleteRequest(
        messages=[
            {"role": "user", "content": "What is the project status?"},
        ],
        tools=[],
        system_prompt="You are a PM assistant.",
        provider="mock",
        model="mock",
    )
    payload = request.model_dump(mode="json")
    assert payload["provider"] == "mock"
    assert len(payload["messages"]) == 1


def test_estimate_request_payload_from_backend_schema_matches_ai_service_contract(
    project_context_payload,
):
    backend_request = backend_ai.AIServiceEstimateRequest(
        project_context=project_context_payload,
        task_inputs=[
            {
                "task_id": uuid4(),
                "task_name": "API integration testing",
                "task_description": "Validate backend and frontend integration",
                "duration": 720,
            }
        ],
        include_reasoning=True,
    )

    payload = backend_request.model_dump(mode="json")
    service_request = contracts.EstimateRequest.model_validate(payload)

    assert service_request.model_dump(mode="json") == payload


def test_suggestions_request_payload_from_backend_schema_matches_ai_service_contract(
    project_context_payload,
):
    backend_request = backend_ai.AIServiceSuggestionsRequest(
        project_context=project_context_payload,
        limit=5,
        ui_context={
            "current_view": "gantt",
            "selected_task_ids": [uuid4()],
        },
    )

    payload = backend_request.model_dump(mode="json")
    service_request = contracts.SuggestionsRequest.model_validate(payload)

    assert service_request.model_dump(mode="json") == payload


def test_complete_stream_response_matches_event_contract(
    client,
    service_headers,
):
    request = contracts.CompleteRequest(
        messages=[{"role": "user", "content": "What is the project status?"}],
        tools=[],
        system_prompt="You are a PM assistant.",
        provider="mock",
        model="mock",
        conversation_id=uuid4(),
    )

    response = client.post(
        "/v1/complete",
        headers=service_headers,
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    event_payloads = [
        json.loads(line.removeprefix("data:").strip())
        for line in response.text.splitlines()
        if line.startswith("data:")
    ]

    assert len(event_payloads) >= 3

    backend_events = [
        backend_ai.AIChatEvent.model_validate(payload) for payload in event_payloads
    ]
    service_events = [
        contracts.ChatEvent.model_validate(payload) for payload in event_payloads
    ]
    event_types = [event.type for event in backend_events]

    assert event_types[0] == "start"
    assert event_types[-1] == "done"
    assert all(event_type == "chunk" for event_type in event_types[1:-1])
    assert backend_events[0].conversation_id is not None
    assert backend_events[-1].message_id is not None
    assert [event.model_dump(mode="json") for event in backend_events] == [
        event.model_dump(mode="json") for event in service_events
    ]


def test_estimate_response_matches_backend_contract(
    client,
    service_headers,
    project_context_payload,
):
    backend_request = backend_ai.AIServiceEstimateRequest(
        project_context=project_context_payload,
        task_inputs=[
            {
                "task_id": uuid4(),
                "task_name": "API integration testing",
                "task_description": "Validate backend and frontend integration",
                "duration": 720,
            }
        ],
        include_reasoning=True,
    )

    response = client.post(
        "/v1/brain/estimate",
        headers=service_headers,
        json=backend_request.model_dump(mode="json"),
    )

    assert response.status_code == 200

    payload = response.json()
    backend_response = backend_ai.AIEstimateResponse.model_validate(payload)
    service_response = contracts.EstimateResponse.model_validate(payload)

    assert backend_response.model_dump(mode="json") == service_response.model_dump(
        mode="json"
    )
    assert len(backend_response.estimates) == 1
    assert backend_response.estimates[0].reasoning is not None


def test_suggestions_response_matches_backend_contract(
    client,
    service_headers,
    project_context_payload,
):
    backend_request = backend_ai.AIServiceSuggestionsRequest(
        project_context=project_context_payload,
        limit=5,
        ui_context={"current_view": "overview"},
    )

    response = client.post(
        "/v1/brain/suggestions",
        headers=service_headers,
        json=backend_request.model_dump(mode="json"),
    )

    assert response.status_code == 200

    payload = response.json()
    backend_response = backend_ai.AISuggestionsResponse.model_validate(payload)
    service_response = contracts.SuggestionsResponse.model_validate(payload)

    assert backend_response.model_dump(mode="json") == service_response.model_dump(
        mode="json"
    )
    assert len(backend_response.suggestions) >= 1
