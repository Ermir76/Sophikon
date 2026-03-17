from app.service.providers.tool_adapters import as_openai_tools

_SAMPLE_TOOL = {
    "name": "get_tasks",
    "description": "Get all tasks for the project.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filter_status": {"type": "string"},
        },
    },
}


def test_as_openai_tools_maps_function_shape():
    tools = as_openai_tools([_SAMPLE_TOOL])
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == _SAMPLE_TOOL["name"]
