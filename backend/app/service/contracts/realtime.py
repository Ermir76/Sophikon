"""
Service-layer realtime contracts.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import AuditAction
from app.service.contracts._uuid import ContractUUID

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]

RealtimeChannel = Literal[
    "tasks",
    "resources",
    "members",
    "activity",
    "project",
    "comments",
]
PresenceStatus = Literal["viewing", "editing"]
PresenceEntityType = Literal[
    "project",
    "task",
    "resource",
    "assignment",
    "dependency",
    "project_member",
]
RealtimeEntityType = Literal[
    "project",
    "task",
    "resource",
    "assignment",
    "dependency",
    "project_member",
    "comment",
]


class RealtimeActor(BaseModel):
    id: ContractUUID
    full_name: str | None = None
    avatar_url: str | None = None


class RealtimeEventPayload(BaseModel):
    type: str
    project_id: ContractUUID
    actor: RealtimeActor | None = None
    entity_type: RealtimeEntityType
    action: AuditAction
    entity_id: ContractUUID | None = None
    entity_name: str | None = None
    occurred_at: datetime
    metadata: dict[str, JsonValue] | None = Field(default=None)


class RealtimeErrorPayload(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


class SubscribeClientMessage(BaseModel):
    type: Literal["subscribe"]
    channels: list[RealtimeChannel] = Field(max_length=32)


class PresenceClientMessage(BaseModel):
    type: Literal["presence"]
    status: PresenceStatus
    entity_type: PresenceEntityType
    entity_id: ContractUUID | None = None
