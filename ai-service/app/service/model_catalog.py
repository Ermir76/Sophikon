"""
Single source of truth for AI provider/model options.
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class ModelOption:
    model_id: str
    label: str
    recommended: bool = False


@dataclass(frozen=True, slots=True)
class ProviderOption:
    provider_id: str
    display_name: str
    requires_env_key: str
    models: tuple[ModelOption, ...]
    test_only: bool = False


MODEL_CATALOG: dict[str, ProviderOption] = {
    "anthropic": ProviderOption(
        provider_id="anthropic",
        display_name="Anthropic",
        requires_env_key="ANTHROPIC_API_KEY",
        models=(
            ModelOption("claude-haiku-4-5-20251001", "Claude Haiku 4.5", recommended=True),
            ModelOption("claude-sonnet-4-6", "Claude Sonnet 4.6"),
            ModelOption("claude-opus-4-6", "Claude Opus 4.6"),
        ),
    ),
    "openai": ProviderOption(
        provider_id="openai",
        display_name="OpenAI",
        requires_env_key="OPENAI_API_KEY",
        models=(
            ModelOption("gpt-5-mini", "GPT-5 mini", recommended=True),
            ModelOption("gpt-5", "GPT-5"),
            ModelOption("gpt-5-nano", "GPT-5 nano"),
        ),
    ),
    "gemini": ProviderOption(
        provider_id="gemini",
        display_name="Google Gemini",
        requires_env_key="GEMINI_API_KEY",
        models=(
            ModelOption("gemini-2.5-pro", "Gemini 2.5 Pro", recommended=True),
            ModelOption("gemini-2.5-flash", "Gemini 2.5 Flash"),
            ModelOption("gemini-3-flash-preview", "Gemini 3 Flash Preview"),
        ),
    ),
    "mock": ProviderOption(
        provider_id="mock",
        display_name="Mock (Testing)",
        requires_env_key="",
        models=(
            ModelOption("mock", "Mock Model", recommended=True),
        ),
        test_only=True,
    ),
}

DEFAULT_PROVIDER = "gemini"
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-5-mini",
    "gemini": "gemini-2.5-pro",
    "mock": "mock",
}


def _provider_key_present(provider_id: str) -> bool:
    if provider_id == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if provider_id == "openai":
        return bool(settings.OPENAI_API_KEY)
    if provider_id == "gemini":
        return bool(settings.GEMINI_API_KEY)
    if provider_id == "mock":
        return True
    return False


def get_catalog_payload() -> dict:
    is_live = settings.AI_MODE == "live"
    providers = []
    for provider in MODEL_CATALOG.values():
        if is_live and provider.test_only:
            continue
        providers.append(
            {
                "provider_id": provider.provider_id,
                "display_name": provider.display_name,
                "requires_env_key": provider.requires_env_key,
                "available": _provider_key_present(provider.provider_id),
                "models": [
                    {
                        "model_id": model.model_id,
                        "label": model.label,
                        "recommended": model.recommended,
                    }
                    for model in provider.models
                ],
            }
        )

    configured_provider = (settings.AI_PROVIDER or DEFAULT_PROVIDER).lower().strip()
    if configured_provider not in MODEL_CATALOG:
        configured_provider = DEFAULT_PROVIDER

    configured_model = settings.AI_MODEL_NAME or DEFAULT_MODELS[configured_provider]
    allowed_models = {m.model_id for m in MODEL_CATALOG[configured_provider].models}
    if configured_model not in allowed_models:
        configured_model = DEFAULT_MODELS[configured_provider]
    return {
        "providers": providers,
        "defaults": {
            "provider": configured_provider,
            "model": configured_model,
            "mode": settings.AI_MODE,
        },
    }


def validate_provider_and_model(
    provider: str | None,
    model: str | None,
    *,
    has_user_key: bool = False,
) -> tuple[str, str, str | None]:
    """
    Returns: (provider_id, model_id, error_message)

    Pass has_user_key=True when the caller supplies their own API key so that
    the missing-server-key check is skipped.
    """
    provider_id = (provider or settings.AI_PROVIDER or DEFAULT_PROVIDER).lower().strip()
    provider_option = MODEL_CATALOG.get(provider_id)
    if provider_option is None:
        return provider_id, model or "", f"Unsupported AI provider: {provider_id}"
    if settings.AI_MODE == "live" and provider_option.test_only:
        return provider_id, model or "", f"Provider '{provider_id}' is not available in live mode"

    # Provider-scoped default avoids cross-provider contamination from global AI_MODEL_NAME.
    model_id = (model or DEFAULT_MODELS[provider_id]).strip()
    allowed_model_ids = {m.model_id for m in provider_option.models}
    if model_id not in allowed_model_ids:
        return provider_id, model_id, f"Model '{model_id}' is not allowed for provider '{provider_id}'"

    if settings.AI_MODE == "live" and not has_user_key and not _provider_key_present(provider_id):
        return provider_id, model_id, f"Provider '{provider_id}' is not configured on server"

    return provider_id, model_id, None
