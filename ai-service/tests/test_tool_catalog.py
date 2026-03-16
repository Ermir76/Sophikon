from app.service.providers.tool_catalog import TOOL_DEFINITIONS


def test_tool_catalog_is_non_empty_and_contains_core_tools():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert len(names) > 10
    assert "get_tasks" in names
    assert "create_task" in names
    assert "delete_task" in names
