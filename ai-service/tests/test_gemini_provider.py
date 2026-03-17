import asyncio
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.core.config import settings
from app.service.providers import gemini_provider


def test_stream_gemini_emits_chunk_tool_call_and_done(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")

    class FakeChunk:
        def __init__(self, *, text=None, function_call=None):
            self.text = text
            self.usage_metadata = None
            self.candidates = []
            if function_call is not None:
                part = SimpleNamespace(function_call=function_call)
                content = SimpleNamespace(parts=[part])
                self.candidates = [SimpleNamespace(content=content)]

    class FakeUsageChunk:
        def __init__(self):
            self.text = None
            self.candidates = []
            self.usage_metadata = SimpleNamespace(
                prompt_token_count=10, candidates_token_count=7
            )

    async def fake_generate_content_stream(**kwargs):
        async def _gen():
            yield FakeChunk(text="hello from gemini")
            yield FakeChunk(
                function_call=SimpleNamespace(name="get_tasks", args={"limit": 5})
            )
            yield FakeUsageChunk()

        return _gen()

    fake_models = SimpleNamespace(generate_content_stream=fake_generate_content_stream)
    fake_aio = SimpleNamespace(models=fake_models)

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.aio = fake_aio

    fake_types = SimpleNamespace(
        FunctionDeclaration=lambda **kw: kw,
        Tool=lambda **kw: kw,
        GenerateContentConfig=lambda **kw: kw,
    )

    monkeypatch.setitem(
        sys.modules,
        "google.genai",
        SimpleNamespace(Client=FakeClient, types=fake_types),
    )
    monkeypatch.setitem(
        sys.modules,
        "google.genai.types",
        fake_types,
    )
    monkeypatch.setitem(
        sys.modules,
        "google",
        SimpleNamespace(genai=SimpleNamespace(Client=FakeClient)),
    )

    messages = [{"role": "user", "content": "status"}]
    tools = [{"name": "get_tasks", "input_schema": {"type": "object"}}]

    async def _collect():
        return [
            event
            async for event in gemini_provider.stream_gemini(
                messages,
                "You are a PM assistant.",
                tools,
                model_id="gemini-2.5-flash",
                conversation_id=uuid4(),
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert any(event["type"] == "chunk" and "gemini" in event["content"] for event in events)
    assert any(event["type"] == "tool_call" and event["tool_name"] == "get_tasks" for event in events)
    assert events[-1]["type"] == "done"
