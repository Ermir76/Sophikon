import asyncio
from uuid import uuid4

from app.service.providers.mock_provider import stream_mock


def test_stream_mock_emits_start_chunks_done():
    messages = [{"role": "user", "content": "What is status?"}]
    conversation_id = uuid4()

    async def _collect():
        return [
            event
            async for event in stream_mock(
                messages,
                "You are a PM assistant.",
                model_id="sophikon-mock-v1",
                conversation_id=conversation_id,
            )
        ]

    events = asyncio.run(_collect())

    assert events[0]["type"] == "start"
    assert events[-1]["type"] == "done"
    assert any(event.get("type") == "chunk" for event in events)
    assert events[-1]["usage"]["model"] == "sophikon-mock-v1"
