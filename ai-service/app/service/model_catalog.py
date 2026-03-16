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


MODEL_CATALOG: dict[str, ProviderOption] = {
    "anthropic": ProviderOption(
        provider_id="anthropic",
        display_name="Anthropic",
        requires_env_key="ANTHROPIC_API_KEY",
        models=(
            ModelOption("claude-3-7-sonnet-latest", "Claude 3.7 Sonnet", recommended=True),
            ModelOption("claude-3-5-sonnet-latest", "Claude 3.5 Sonnet"),
            ModelOption("claude-3-5-haiku-latest", "Claude 3.5 Haiku"),
        ),
    ),
    "openai": ProviderOption(
        provider_id="openai",
        display_name="OpenAI",
        requires_env_key="OPENAI_API_KEY",
        models=(
            ModelOption("gpt-5-mini", "GPT-5 mini", recommended=True),
            ModelOption("gpt-5", "GPT-5"),
            ModelOption("gpt-4.1-mini", "GPT-4.1 mini"),
        ),
    ),
    "gemini": ProviderOption(
        provider_id="gemini",
        display_name="Google Gemini",
        requires_env_key="GEMINI_API_KEY",
        models=(
            ModelOption("gemini-2.5-flash", "Gemini 2.5 Flash", recommended=True),
            ModelOption("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ),
    ),
}

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-3-7-sonnet-latest",
    "openai": "gpt-5-mini",
    "gemini": "gemini-2.5-flash",
}


def _provider_key_present(provider_id: str) -> bool:
    if provider_id == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    if provider_id == "openai":
        return bool(settings.OPENAI_API_KEY)
    if provider_id == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return False


def get_catalog_payload() -> dict:
    providers = []
    for provider in MODEL_CATALOG.values():
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
) -> tuple[str, str, str | None]:
    """
    Returns: (provider_id, model_id, error_message)
    """
    provider_id = (provider or settings.AI_PROVIDER or DEFAULT_PROVIDER).lower().strip()
    provider_option = MODEL_CATALOG.get(provider_id)
    if provider_option is None:
        return provider_id, model or "", f"Unsupported AI provider: {provider_id}"

    # Provider-scoped default avoids cross-provider contamination from global AI_MODEL_NAME.
    model_id = (model or DEFAULT_MODELS[provider_id]).strip()
    allowed_model_ids = {m.model_id for m in provider_option.models}
    if model_id not in allowed_model_ids:
        return provider_id, model_id, f"Model '{model_id}' is not allowed for provider '{provider_id}'"

    if settings.AI_MODE == "live" and not _provider_key_present(provider_id):
        return provider_id, model_id, f"Provider '{provider_id}' is not configured on server"

    return provider_id, model_id, None
