import asyncio
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.service.providers.anthropic_provider import stream_claude


def test_stream_claude_emits_tool_call_chunk_and_done(monkeypatch):
    class FakeStreamContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def __aiter__(self):
            async def _events():
                yield SimpleNamespace(
                    type="content_block_start",
                    content_block=SimpleNamespace(type="tool_use", id="tool-1", name="get_tasks"),
                )
                yield SimpleNamespace(
                    type="content_block_delta",
                    delta=SimpleNamespace(type="input_json_delta", partial_json='{"limit": 5}'),
                )
                yield SimpleNamespace(type="content_block_stop")
                yield SimpleNamespace(
                    type="content_block_delta",
                    delta=SimpleNamespace(type="text_delta", text="hello from claude"),
                )

            return _events()

        async def get_final_message(self):
            return SimpleNamespace(usage=SimpleNamespace(input_tokens=14, output_tokens=9))

    class FakeMessagesApi:
        def stream(self, **kwargs):
            return FakeStreamContext()

    class FakeAsyncAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = FakeMessagesApi()

    monkeypatch.setitem(
        sys.modules, "anthropic", SimpleNamespace(AsyncAnthropic=FakeAsyncAnthropic)
    )

    messages = [{"role": "user", "content": "status"}]
    tools = [{"name": "get_tasks", "input_schema": {"type": "object"}}]

    async def _collect():
        return [
            event
            async for event in stream_claude(
                messages,
                "You are a PM assistant.",
                tools,
                model_id="claude-3-7-sonnet-latest",
                conversation_id=uuid4(),
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert any(event["type"] == "tool_call" and event["tool_name"] == "get_tasks" for event in events)
    assert any(event["type"] == "chunk" and "claude" in event["content"] for event in events)
    assert events[-1]["type"] == "done"
