from app.service.providers.message_builders import to_gemini_contents, to_openai_messages


def test_to_openai_messages_plain_text():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "What is the status?"},
    ]
    result = to_openai_messages(messages)
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"
    assert result[2]["role"] == "user"
    assert result[2]["content"] == "What is the status?"


def test_to_openai_messages_assistant_tool_use():
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Let me check tasks."},
                {"type": "tool_use", "id": "tool-1", "name": "get_tasks", "input": {"filter_status": "all"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tool-1", "content": '{"tasks": []}'},
            ],
        },
    ]
    result = to_openai_messages(messages)

    # assistant turn becomes role=assistant with tool_calls
    assert result[0]["role"] == "assistant"
    assert len(result[0]["tool_calls"]) == 1
    assert result[0]["tool_calls"][0]["function"]["name"] == "get_tasks"

    # tool result turn becomes role=tool
    assert result[1]["role"] == "tool"
    assert result[1]["tool_call_id"] == "tool-1"


def test_to_gemini_contents_maps_assistant_role_to_model():
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]
    contents = to_gemini_contents(messages)
    assert contents[0]["role"] == "user"
    assert contents[1]["role"] == "model"


def test_to_gemini_contents_tool_use_and_result():
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "tool-1", "name": "get_tasks", "input": {}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tool-1", "content": '{"tasks":[]}'},
            ],
        },
    ]
    contents = to_gemini_contents(messages)

    assert contents[0]["role"] == "model"
    assert contents[0]["parts"][0]["function_call"]["name"] == "get_tasks"

    assert contents[1]["role"] == "user"
    assert contents[1]["parts"][0]["function_response"]["name"] == "get_tasks"
