"""Thin router — delegates single-turn completions to the appropriate LLM provider."""

from app.core.config import settings
from app.schema.contracts import ChatEvent, CompleteRequest
from app.service.model_catalog import validate_provider_and_model
from app.service.providers.anthropic_provider import stream_claude as _provider_stream_claude
from app.service.providers.gemini_provider import stream_gemini as _provider_stream_gemini
from app.service.providers.mock_provider import stream_mock as _provider_stream_mock
from app.service.providers.openai_provider import stream_openai as _provider_stream_openai


def _resolve_provider_and_model(
    request: CompleteRequest,
) -> tuple[str | None, str, str | None]:
    has_user_key = bool(request.api_key)
    provider, model, error = validate_provider_and_model(
        request.provider, request.model, has_user_key=has_user_key
    )
    if settings.AI_MODE != "live":
        return None, model, None
    return provider, model, error


async def complete_stream(request: CompleteRequest):
    provider, model_id, error = _resolve_provider_and_model(request)
    if error:
        yield ChatEvent(type="error", error=error, model=model_id).model_dump(
            mode="json", exclude_none=True
        )
        return

    raw_cache = request.prompt_cache
    prompt_cache = raw_cache.model_dump() if hasattr(raw_cache, "model_dump") else raw_cache

    if provider == "anthropic":
        async for event in _provider_stream_claude(
            request.messages,
            request.system_prompt,
            request.tools,
            model_id=model_id,
            api_key=request.api_key,
            conversation_id=request.conversation_id,
            prompt_cache=prompt_cache,
        ):
            yield event
    elif provider == "openai":
        async for event in _provider_stream_openai(
            request.messages,
            request.system_prompt,
            request.tools,
            model_id=model_id,
            api_key=request.api_key,
            conversation_id=request.conversation_id,
            prompt_cache=prompt_cache,
        ):
            yield event
    elif provider == "gemini":
        async for event in _provider_stream_gemini(
            request.messages,
            request.system_prompt,
            request.tools,
            model_id=model_id,
            api_key=request.api_key,
            conversation_id=request.conversation_id,
            prompt_cache=prompt_cache,
        ):
            yield event
    else:
        async for event in _provider_stream_mock(
            request.messages,
            request.system_prompt,
            model_id=model_id,
            conversation_id=request.conversation_id,
        ):
            yield event
