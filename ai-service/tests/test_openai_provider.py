import asyncio
import sys
from types import SimpleNamespace
from uuid import uuid4

from app.service.providers.openai_provider import stream_openai


def test_stream_openai_emits_chunk_function_tool_call_and_done(monkeypatch):
    captured: dict = {}

    class FakeStream:
        def __aiter__(self):
            async def _iter():
                # Text chunk
                yield SimpleNamespace(
                    usage=None,
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(
                                content=[
                                    SimpleNamespace(text="hello "),
                                    SimpleNamespace(text="from openai"),
                                ],
                                tool_calls=None,
                            )
                        )
                    ],
                )
                # Tool call chunk with function payload
                yield SimpleNamespace(
                    usage=None,
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(
                                content=None,
                                tool_calls=[
                                    SimpleNamespace(
                                        type="function",
                                        index=0,
                                        id="tool-call-1",
                                        function=SimpleNamespace(
                                            name="get_tasks", arguments='{"limit": 5}'
                                        ),
                                    )
                                ],
                            )
                        )
                    ],
                )
                # Usage chunk
                yield SimpleNamespace(
                    usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
                    choices=[],
                )

            return _iter()

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return FakeStream()

    class FakeAsyncOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI))

    messages = [{"role": "user", "content": "status"}]
    tools = [{"name": "get_tasks", "input_schema": {"type": "object"}}]

    async def _collect():
        return [
            event
            async for event in stream_openai(
                messages,
                "You are a PM assistant.",
                tools,
                model_id="gpt-5-mini",
                conversation_id=uuid4(),
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert any(event["type"] == "chunk" and "openai" in event["content"] for event in events)
    assert any(event["type"] == "tool_call" and event["tool_name"] == "get_tasks" for event in events)
    assert events[-1]["type"] == "done"
    assert captured["tools"][0]["type"] == "function"
    assert captured["stream"] is True
    assert captured["stream_options"]["include_usage"] is True
