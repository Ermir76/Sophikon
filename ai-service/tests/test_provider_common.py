from uuid import uuid4

from app.schema.contracts import ChatRequest
from app.service.providers.common import (
    build_system_prompt,
    chunk_text,
    estimate_tokens,
    stringify_content,
)


def _request_payload() -> dict:
    return {
        "message": "status",
        "provider": "openai",
        "model": "gpt-5-mini",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "Provider Common Project",
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


def test_estimate_tokens_has_minimum_one():
    assert estimate_tokens("") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 40) == 10


def test_stringify_content_handles_list_payload():
    value = [{"type": "text", "text": "hello"}]
    encoded = stringify_content(value)
    assert "hello" in encoded
    assert encoded.startswith("[")


def test_chunk_text_splits_deterministically():
    chunks = chunk_text("abcdefghij", chunk_size=4)
    assert chunks == ["abcd", "efgh", "ij"]


def test_build_system_prompt_contains_project_context_summary():
    request = ChatRequest.model_validate(_request_payload())
    prompt = build_system_prompt(request)
    assert "Provider Common Project" in prompt
    assert "Project status: ACTIVE" in prompt
    assert "calculate_schedule" in prompt
