import asyncio
from uuid import uuid4

from app.schema.contracts import ChatRequest
from app.service.providers.mock_provider import stream_mock


def _request_payload() -> dict:
    return {
        "message": "What is status?",
        "provider": "openai",
        "model": "gpt-5-mini",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "Mock Provider Project",
            "description": None,
            "status": "ACTIVE",
            "start_date": "2026-03-01",
            "finish_date": None,
            "updated_at": "2026-03-01T00:00:00Z",
            "tasks": [],
        },
        "conversation_id": str(uuid4()),
        "user_id": str(uuid4()),
    }


def test_stream_mock_emits_start_chunks_done():
    request = ChatRequest.model_validate(_request_payload())

    async def _collect():
        return [event async for event in stream_mock(request, model_id="sophikon-mock-v1")]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert events[-1]["type"] == "done"
    assert any(event.get("type") == "chunk" for event in events)
    assert events[-1]["usage"]["model"] == "sophikon-mock-v1"
