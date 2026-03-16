import asyncio
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import ChatRequest
from app.service.providers import gemini_provider


def _request_payload() -> dict:
    return {
        "message": "status",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "Gemini Provider Project",
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


def test_stream_gemini_emits_chunk_tool_call_and_done(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")

    class FakeResponse:
        status_code = 200
        text = "ok"

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "hello from gemini"},
                                {"functionCall": {"name": "get_tasks", "args": {"limit": 5}}},
                            ]
                        }
                    }
                ],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 7},
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, endpoint, params, json):
            return FakeResponse()

    monkeypatch.setattr(gemini_provider.httpx, "AsyncClient", FakeAsyncClient)

    request = ChatRequest.model_validate(_request_payload())

    async def _collect():
        return [
            event
            async for event in gemini_provider.stream_gemini(
                request,
                model_id="gemini-2.5-flash",
                tool_definitions=[{"name": "get_tasks", "input_schema": {"type": "object"}}],
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert any(event["type"] == "chunk" and "gemini" in event["content"] for event in events)
    assert any(event["type"] == "tool_call" and event["tool_name"] == "get_tasks" for event in events)
    assert events[-1]["type"] == "done"
