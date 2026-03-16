import asyncio
from uuid import uuid4

from app.core.config import settings
from app.service import brain_service


def _chat_request_payload() -> dict:
    return {
        "message": "status?",
        "provider": "openai",
        "model": "gpt-5-mini",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "Dispatch Test Project",
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


async def _collect_stream_events(payload: dict) -> list[dict]:
    request = brain_service.ChatRequest.model_validate(payload)
    return [event async for event in brain_service.stream_chat_events(request)]


def test_stream_chat_events_returns_error_event_when_provider_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model: (
            "gemini",
            "gemini-2.5-flash",
            "Provider 'gemini' is not configured on server",
        ),
    )

    events = asyncio.run(_collect_stream_events(_chat_request_payload()))

    assert events == [
        {
            "type": "error",
            "error": "Provider 'gemini' is not configured on server",
            "model": "gemini-2.5-flash",
        }
    ]


def test_stream_chat_events_dispatches_to_openai_stream_in_live_mode(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model: ("openai", "gpt-5-mini", None),
    )

    async def fake_stream_openai(request, *, model_id):
        assert model_id == "gpt-5-mini"
        yield {"type": "start", "model": model_id}
        yield {"type": "done", "model": model_id}

    monkeypatch.setattr(brain_service, "_stream_openai", fake_stream_openai)

    async def should_not_run(*args, **kwargs):
        raise AssertionError("wrong provider stream selected")
        yield {}

    monkeypatch.setattr(brain_service, "_stream_claude", should_not_run)
    monkeypatch.setattr(brain_service, "_stream_gemini", should_not_run)
    monkeypatch.setattr(brain_service, "_stream_mock", should_not_run)

    events = asyncio.run(_collect_stream_events(_chat_request_payload()))

    assert events == [
        {"type": "start", "model": "gpt-5-mini"},
        {"type": "done", "model": "gpt-5-mini"},
    ]


def test_stream_chat_events_uses_mock_stream_when_not_live(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "mock")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model: ("openai", "gpt-5-mini", None),
    )

    async def fake_stream_mock(request, *, model_id):
        assert model_id == "gpt-5-mini"
        yield {"type": "start", "model": model_id}
        yield {"type": "done", "model": model_id}

    monkeypatch.setattr(brain_service, "_stream_mock", fake_stream_mock)

    async def should_not_run(*args, **kwargs):
        raise AssertionError("live provider stream should not run in mock mode")
        yield {}

    monkeypatch.setattr(brain_service, "_stream_openai", should_not_run)
    monkeypatch.setattr(brain_service, "_stream_claude", should_not_run)
    monkeypatch.setattr(brain_service, "_stream_gemini", should_not_run)

    events = asyncio.run(_collect_stream_events(_chat_request_payload()))

    assert events == [
        {"type": "start", "model": "gpt-5-mini"},
        {"type": "done", "model": "gpt-5-mini"},
    ]
