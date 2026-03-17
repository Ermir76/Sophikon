import json


def estimate_tokens(value: str) -> int:
    return max(1, len(value) // 4)


def stringify_content(value: str | list[dict]) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def chunk_text(value: str, chunk_size: int = 48) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]
