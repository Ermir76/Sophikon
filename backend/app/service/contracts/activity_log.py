"""
Service contracts for activity log use-cases.
"""

from datetime import datetime
from typing import Literal, TypedDict
from uuid import UUID

from app.models.enums import AuditAction

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]

ActivityEntityType = Literal[
    "project",
    "task",
    "resource",
    "assignment",
    "dependency",
    "project_member",
    "comment",
]


class ActivityActorData(TypedDict):
    id: UUID
    full_name: str | None
    avatar_url: str | None


class ActivityChangeFieldData(TypedDict):
    field: str
    old: JsonValue
    new: JsonValue


class ActivityChangesData(TypedDict):
    fields: list[ActivityChangeFieldData]


class ActivityLogItemData(TypedDict):
    id: UUID
    user: ActivityActorData | None
    action: AuditAction
    entity_type: ActivityEntityType
    entity_id: UUID | None
    entity_name: str | None
    changes: ActivityChangesData | None
    created_at: datetime
