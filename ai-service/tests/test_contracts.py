import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schema import contracts


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def service_headers():
    return {"X-AI-Service-Secret": settings.AI_SERVICE_SHARED_SECRET}


def test_complete_request_accepts_prompt_cache_metadata():
    request = contracts.CompleteRequest(
        messages=[{"role": "user", "content": "status"}],
        tools=[],
        system_prompt="You are a PM assistant.",
        provider="mock",
        model="mock",
        prompt_cache={
            "key": "agent:planner:v1",
            "ttl_seconds": 3600,
            "tags": ["agent", "planner", "v1"],
        },
    )
    payload = request.model_dump(mode="json")
    assert payload["prompt_cache"]["key"] == "agent:planner:v1"


def test_complete_stream_events_match_chat_event_contract(
    client: TestClient,
    service_headers: dict[str, str],
):
    request = contracts.CompleteRequest(
        messages=[{"role": "user", "content": "What is the project status?"}],
        tools=[],
        system_prompt="You are a PM assistant.",
        provider="mock",
        model="mock",
        conversation_id=uuid4(),
        prompt_cache={"key": "agent:chat:v1", "ttl_seconds": 60, "tags": ["agent"]},
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

    service_events = [contracts.ChatEvent.model_validate(payload) for payload in event_payloads]
    service_types = [event.type for event in service_events]
    assert service_types[0] == "start"
    assert service_types[-1] == "done"
