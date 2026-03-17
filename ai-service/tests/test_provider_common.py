from app.service.providers.common import (
    chunk_text,
    estimate_tokens,
    stringify_content,
)


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
