import asyncio
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.schema.contracts import ChatRequest
from app.service.providers.openai_provider import stream_openai


def _request_payload() -> dict:
    return {
        "message": "status",
        "provider": "openai",
        "model": "gpt-5-mini",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "OpenAI Provider Project",
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


def test_stream_openai_emits_chunk_function_tool_call_and_done(monkeypatch):
    captured: dict = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            function_tool_call = SimpleNamespace(
                type="function",
                id="tool-call-1",
                function=SimpleNamespace(name="get_tasks", arguments='{"limit": 5}'),
            )
            custom_tool_call = SimpleNamespace(type="custom", id="custom-1")
            message = SimpleNamespace(
                content="hello from openai",
                tool_calls=[function_tool_call, custom_tool_call],
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=message)],
                usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
            )

    class FakeAsyncOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI))

    request = ChatRequest.model_validate(_request_payload())

    async def _collect():
        return [
            event
            async for event in stream_openai(
                request,
                model_id="gpt-5-mini",
                tool_definitions=[{"name": "get_tasks", "input_schema": {"type": "object"}}],
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert any(event["type"] == "chunk" and "openai" in event["content"] for event in events)
    assert any(event["type"] == "tool_call" and event["tool_name"] == "get_tasks" for event in events)
    assert events[-1]["type"] == "done"
    assert captured["tools"][0]["type"] == "function"
