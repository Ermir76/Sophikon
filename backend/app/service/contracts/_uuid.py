"""
UUID helpers for service-layer contracts.
"""

from typing import Annotated, Any
from uuid import UUID

from pydantic import BeforeValidator


def coerce_uuid(value: Any) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid UUID format") from exc


ContractUUID = Annotated[UUID, BeforeValidator(coerce_uuid)]
