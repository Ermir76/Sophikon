import asyncio
import sys
from types import SimpleNamespace
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
    captured: dict = {"configured_key": None}

    class FakeChunk:
        def __init__(self, *, text: str | None = None, function_call: object | None = None):
            self.text = text
            self.candidates = []
            if function_call is not None:
                part = SimpleNamespace(function_call=function_call)
                content = SimpleNamespace(parts=[part])
                self.candidates = [SimpleNamespace(content=content)]
            self.usage_metadata = None

    class FakeUsageChunk:
        def __init__(self):
            self.text = None
            self.candidates = []
            self.usage_metadata = SimpleNamespace(prompt_token_count=10, candidates_token_count=7)

    class FakeGenerativeModel:
        def __init__(self, *, model_name, system_instruction, tools):
            captured["model_name"] = model_name
            captured["system_instruction"] = system_instruction
            captured["tools"] = tools

        def generate_content(self, contents, stream):
            captured["contents"] = contents
            captured["stream"] = stream
            return iter(
                [
                    FakeChunk(text="hello from gemini"),
                    FakeChunk(
                        function_call=SimpleNamespace(name="get_tasks", args={"limit": 5})
                    ),
                    FakeUsageChunk(),
                ]
            )

    def _configure(*, api_key):
        captured["configured_key"] = api_key

    monkeypatch.setitem(
        sys.modules,
        "google.generativeai",
        SimpleNamespace(configure=_configure, GenerativeModel=FakeGenerativeModel),
    )

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
    assert captured["configured_key"] == "test-key"
    assert captured["model_name"] == "gemini-2.5-flash"
    assert captured["stream"] is True
