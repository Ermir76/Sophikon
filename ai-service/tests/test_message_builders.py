from uuid import uuid4

from app.schema.contracts import ChatRequest
from app.service.providers.message_builders import (
    build_claude_messages,
    build_gemini_contents,
    build_openai_messages,
)


def _request_payload(*, with_tool_results: bool = False) -> dict:
    return {
        "message": "final user message",
        "provider": "openai",
        "model": "gpt-5-mini",
        "project_context": {
            "project_id": str(uuid4()),
            "name": "Builder Project",
            "description": None,
            "status": "ACTIVE",
            "start_date": "2026-03-01",
            "finish_date": None,
            "updated_at": "2026-03-01T00:00:00Z",
            "tasks": [],
        },
        "conversation_id": str(uuid4()),
        "user_id": str(uuid4()),
        "history": [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
        ],
        "tool_results": (
            [{"tool_use_id": "tool-1", "content": "done", "is_error": False}]
            if with_tool_results
            else []
        ),
    }


def test_build_claude_messages_appends_tool_results_when_present():
    request = ChatRequest.model_validate(_request_payload(with_tool_results=True))
    messages = build_claude_messages(request)

    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"][0]["type"] == "tool_result"
    assert messages[-1]["content"][0]["tool_use_id"] == "tool-1"


def test_build_openai_messages_normalizes_roles_and_appends_message():
    request = ChatRequest.model_validate(_request_payload(with_tool_results=False))
    messages = build_openai_messages(request)

    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "final user message"


def test_build_gemini_contents_maps_assistant_role_to_model():
    request = ChatRequest.model_validate(_request_payload(with_tool_results=False))
    contents = build_gemini_contents(request)

    assert contents[0]["role"] == "user"
    assert contents[1]["role"] == "model"
    assert contents[-1]["parts"][0]["text"] == "final user message"
