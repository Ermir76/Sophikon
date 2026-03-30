import asyncio
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import CompleteRequest
from app.service import brain_service


def _complete_request(provider: str = "mock") -> CompleteRequest:
    return CompleteRequest(
        messages=[{"role": "user", "content": "status?"}],
        tools=[],
        system_prompt="You are a PM assistant.",
        provider=provider,
        model="mock" if provider == "mock" else "gpt-5-mini",
        conversation_id=uuid4(),
    )


async def _collect(request: CompleteRequest) -> list[dict]:
    return [event async for event in brain_service.complete_stream(request)]


def test_complete_stream_returns_error_event_when_provider_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model, *, has_user_key=False: (
            "gemini",
            "gemini-2.5-flash",
            "Provider 'gemini' is not configured on server",
        ),
    )

    request = _complete_request("gemini")
    events = asyncio.run(_collect(request))

    assert events == [
        {
            "type": "error",
            "error": "Provider 'gemini' is not configured on server",
            "model": "gemini-2.5-flash",
        }
    ]


def test_complete_stream_dispatches_to_openai_stream_in_live_mode(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model, *, has_user_key=False: ("openai", "gpt-5-mini", None),
    )

    async def fake_stream_openai(messages, system_prompt, tools, *, model_id, **kwargs):
        assert model_id == "gpt-5-mini"
        yield {"type": "start", "model": model_id}
        yield {"type": "done", "model": model_id}

    monkeypatch.setattr(brain_service, "_provider_stream_openai", fake_stream_openai)

    async def should_not_run(*args, **kwargs):
        raise AssertionError("wrong provider stream selected")
        yield {}

    monkeypatch.setattr(brain_service, "_provider_stream_claude", should_not_run)
    monkeypatch.setattr(brain_service, "_provider_stream_gemini", should_not_run)
    monkeypatch.setattr(brain_service, "_provider_stream_mock", should_not_run)

    request = _complete_request("openai")
    events = asyncio.run(_collect(request))

    assert events == [
        {"type": "start", "model": "gpt-5-mini"},
        {"type": "done", "model": "gpt-5-mini"},
    ]


def test_complete_stream_ignores_prompt_cache_and_still_dispatches(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model, *, has_user_key=False: ("openai", "gpt-5-mini", None),
    )

    async def fake_stream_openai(messages, system_prompt, tools, *, model_id, **kwargs):
        assert model_id == "gpt-5-mini"
        assert "prompt_cache" not in kwargs
        assert kwargs.get("conversation_id") is not None
        yield {"type": "start", "model": model_id}
        yield {"type": "done", "model": model_id}

    monkeypatch.setattr(brain_service, "_provider_stream_openai", fake_stream_openai)

    request = _complete_request("openai")
    request.prompt_cache = {
        "key": "agent:planner:v1",
        "ttl_seconds": 3600,
        "tags": ["agent", "planner", "v1"],
    }
    events = asyncio.run(_collect(request))

    assert events == [
        {"type": "start", "model": "gpt-5-mini"},
        {"type": "done", "model": "gpt-5-mini"},
    ]


def test_complete_stream_uses_mock_stream_when_not_live(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "mock")
    monkeypatch.setattr(
        brain_service,
        "validate_provider_and_model",
        lambda provider, model, *, has_user_key=False: ("openai", "gpt-5-mini", None),
    )

    async def fake_stream_mock(messages, system_prompt, *, model_id, **kwargs):
        assert model_id == "gpt-5-mini"
        yield {"type": "start", "model": model_id}
        yield {"type": "done", "model": model_id}

    monkeypatch.setattr(brain_service, "_provider_stream_mock", fake_stream_mock)

    async def should_not_run(*args, **kwargs):
        raise AssertionError("live provider stream should not run in mock mode")
        yield {}

    monkeypatch.setattr(brain_service, "_provider_stream_openai", should_not_run)
    monkeypatch.setattr(brain_service, "_provider_stream_claude", should_not_run)
    monkeypatch.setattr(brain_service, "_provider_stream_gemini", should_not_run)

    request = _complete_request("openai")
    events = asyncio.run(_collect(request))

    assert events == [
        {"type": "start", "model": "gpt-5-mini"},
        {"type": "done", "model": "gpt-5-mini"},
    ]
