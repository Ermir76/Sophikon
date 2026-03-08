import re
import uuid

from app.service import comment_service
from app.service.comment_service import parse_mention_user_ids


def test_parse_mention_user_ids_extracts_and_deduplicates() -> None:
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    content = (
        f"Hi @[Alice](user:{user_a}) and @[Bob](user:{user_b}) "
        f"and again @[Alice](user:{user_a})"
    )

    mentions = parse_mention_user_ids(content)

    assert mentions == [user_a, user_b]


def test_parse_mention_user_ids_ignores_plain_handles() -> None:
    content = "Hello @alice and @bob without ID-backed tokens"
    mentions = parse_mention_user_ids(content)
    assert mentions == []


def test_parse_mention_user_ids_ignores_invalid_uuid_tokens(
    monkeypatch,
) -> None:
    user_id = "---------1111-1111-1111-111111111111"
    content = f"Hi @[Alice](user:{user_id})"
    loose_pattern = re.compile(
        r"@\[[^\]]+\]\(user:(?P<user_id>[0-9a-fA-F-]{8}-"
        r"[0-9a-fA-F-]{4}-[0-9a-fA-F-]{4}-[0-9a-fA-F-]{4}-[0-9a-fA-F-]{12})\)"
    )
    monkeypatch.setattr(comment_service, "MENTION_TOKEN_PATTERN", loose_pattern)

    mentions = parse_mention_user_ids(content)

    assert mentions == []
