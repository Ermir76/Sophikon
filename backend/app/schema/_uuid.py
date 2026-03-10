"""
Shared UUID schema helpers.
"""

from typing import Annotated, Any
from uuid import UUID

from pydantic import BeforeValidator


def coerce_uuid(value: Any) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Invalid UUID format") from exc


SchemaUUID = Annotated[UUID, BeforeValidator(coerce_uuid)]
