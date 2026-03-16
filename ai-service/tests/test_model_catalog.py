from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.service.model_catalog import validate_provider_and_model


def test_validate_provider_and_model_accepts_valid_pair_in_mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "mock")
    provider, model, error = validate_provider_and_model("openai", "gpt-5-mini")
    assert provider == "openai"
    assert model == "gpt-5-mini"
    assert error is None


def test_validate_provider_and_model_rejects_unknown_provider():
    provider, model, error = validate_provider_and_model("unsupported", "foo")
    assert provider == "unsupported"
    assert model == "foo"
    assert error == "Unsupported AI provider: unsupported"


def test_validate_provider_and_model_rejects_invalid_model_for_provider():
    provider, model, error = validate_provider_and_model("openai", "claude-3-7-sonnet-latest")
    assert provider == "openai"
    assert model == "claude-3-7-sonnet-latest"
    assert error == "Model 'claude-3-7-sonnet-latest' is not allowed for provider 'openai'"


def test_validate_provider_and_model_rejects_missing_provider_key_in_live_mode(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    provider, model, error = validate_provider_and_model("openai", "gpt-5-mini")
    assert provider == "openai"
    assert model == "gpt-5-mini"
    assert error == "Provider 'openai' is not configured on server"


def test_validate_provider_and_model_uses_provider_default_when_model_omitted(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "mock")
    monkeypatch.setattr(settings, "AI_MODEL_NAME", "claude-3-7-sonnet-latest")

    provider, model, error = validate_provider_and_model("openai", None)

    assert provider == "openai"
    assert model == "gpt-5-mini"
    assert error is None


def test_models_endpoint_returns_catalog_payload(monkeypatch):
    monkeypatch.setattr(settings, "AI_MODE", "live")
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "AI_MODEL_NAME", "gpt-5-mini")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    client = TestClient(app)
    response = client.get(
        "/v1/brain/models",
        headers={"X-AI-Service-Secret": settings.AI_SERVICE_SHARED_SECRET},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "providers" in payload
    assert payload["defaults"]["provider"] == "openai"
    assert payload["defaults"]["model"] == "gpt-5-mini"
    openai = next(
        provider for provider in payload["providers"] if provider["provider_id"] == "openai"
    )
    assert openai["available"] is True
