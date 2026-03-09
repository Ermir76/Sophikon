from uuid import uuid4

from app.service.ws_protocol import (
    build_error_payload,
    parse_notification_client_message,
    parse_project_client_message,
)


def test_parse_project_client_message_subscribe():
    parsed = parse_project_client_message(
        {"type": "subscribe", "channels": ["activity", "project"]}
    )

    assert parsed.kind == "subscribe"
    assert parsed.channels == {"activity", "project"}


def test_parse_project_client_message_presence():
    entity_id = uuid4()
    parsed = parse_project_client_message(
        {
            "type": "presence",
            "status": "editing",
            "entity_type": "task",
            "entity_id": str(entity_id),
        }
    )

    assert parsed.kind == "presence"
    assert parsed.status == "editing"
    assert parsed.entity_type == "task"
    assert str(parsed.entity_id) == str(entity_id)


def test_parse_project_client_message_unknown():
    parsed = parse_project_client_message({"type": "ping"})
    assert parsed.kind == "unknown"


def test_parse_project_client_message_non_dict_is_malformed():
    parsed = parse_project_client_message([])
    assert parsed.kind == "malformed"


def test_parse_project_client_message_invalid_shape_is_malformed():
    parsed = parse_project_client_message({"type": "presence", "status": "editing"})
    assert parsed.kind == "malformed"


def test_parse_notification_client_message_unknown_for_valid_dict():
    parsed = parse_notification_client_message({"type": "ping"})
    assert parsed.kind == "unknown"


def test_parse_notification_client_message_non_dict_is_malformed():
    parsed = parse_notification_client_message([])
    assert parsed.kind == "malformed"


def test_build_error_payload():
    payload = build_error_payload("INVALID_MESSAGE", "Malformed websocket payload")
    assert payload == {
        "type": "error",
        "code": "INVALID_MESSAGE",
        "message": "Malformed websocket payload",
    }
