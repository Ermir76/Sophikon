from app.service.providers.tool_adapters import as_openai_tools
from app.service.providers.tool_catalog import TOOL_DEFINITIONS


def test_as_openai_tools_maps_function_shape():
    tools = as_openai_tools(TOOL_DEFINITIONS[:1])
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == TOOL_DEFINITIONS[0]["name"]
