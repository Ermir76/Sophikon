from app.models.user import User


def get_catalog_provider(catalog: dict, provider_id: str | None) -> dict | None:
    if provider_id is None:
        return None
    for provider in catalog.get("providers", []):
        if provider.get("provider_id") == provider_id:
            return provider
    return None


def recommended_model_id(provider: dict) -> str | None:
    models = provider.get("models", [])
    for model in models:
        if model.get("recommended"):
            return model.get("model_id")
    if models:
        return models[0].get("model_id")
    return None


def is_valid_model_for_provider(catalog: dict, provider_id: str, model_id: str) -> bool:
    provider = get_catalog_provider(catalog, provider_id)
    if provider is None:
        return False
    return any(m.get("model_id") == model_id for m in provider.get("models", []))


def is_provider_available(catalog: dict, provider_id: str) -> bool:
    provider = get_catalog_provider(catalog, provider_id)
    if provider is None:
        return False
    return bool(provider.get("available", False))


def read_user_ai_preferences(user: User) -> dict:
    prefs = dict(user.preferences or {})
    return dict(prefs.get("ai", {}))


def resolve_effective_provider_model(
    user: User, catalog: dict
) -> tuple[str | None, str | None]:
    ai_prefs = read_user_ai_preferences(user)
    defaults = catalog.get("defaults", {})
    provider = ai_prefs.get("provider") or defaults.get("provider")
    model = ai_prefs.get("model") or defaults.get("model")

    if provider and model and is_valid_model_for_provider(catalog, provider, model):
        return provider, model
    default_provider = defaults.get("provider")
    if default_provider:
        provider_obj = get_catalog_provider(catalog, default_provider)
        if provider_obj is not None:
            return default_provider, recommended_model_id(provider_obj)

    providers = catalog.get("providers", [])
    if providers:
        first_provider = providers[0]
        return first_provider.get("provider_id"), recommended_model_id(first_provider)
    return None, None
