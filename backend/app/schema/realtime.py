"""
Typed schemas for realtime websocket messages.
"""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field

from app.models.enums import AuditAction
from app.schema.notification import NotificationItem

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


def _coerce_uuid(value):
    if value is None or isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


SchemaUUID = Annotated[UUID, BeforeValidator(_coerce_uuid)]


class RealtimeActor(BaseModel):
    id: SchemaUUID
    full_name: str | None = None
    avatar_url: str | None = None


class RealtimePresenceUser(BaseModel):
    id: SchemaUUID
    full_name: str | None = None
    avatar_url: str | None = None
    status: PresenceStatus
    entity_type: PresenceEntityType
    entity_id: SchemaUUID | None = None


class PresenceSnapshotMessage(BaseModel):
    type: Literal["presence_snapshot"] = "presence_snapshot"
    project_id: SchemaUUID
    users: list[RealtimePresenceUser]


class PresenceUpdateMessage(BaseModel):
    type: Literal["presence_update"] = "presence_update"
    project_id: SchemaUUID
    users: list[RealtimePresenceUser]


class RealtimeErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


class RealtimeEventMessage(BaseModel):
    type: str
    project_id: SchemaUUID
    actor: RealtimeActor | None = None
    entity_type: RealtimeEntityType
    action: AuditAction
    entity_id: SchemaUUID | None = None
    entity_name: str | None = None
    occurred_at: datetime
    metadata: dict[str, Any] | None = Field(default=None)


class SubscribeMessage(BaseModel):
    type: Literal["subscribe"]
    channels: list[RealtimeChannel]


class PresenceMessage(BaseModel):
    type: Literal["presence"]
    status: PresenceStatus
    entity_type: PresenceEntityType
    entity_id: SchemaUUID | None = None


class NotificationSnapshotMessage(BaseModel):
    type: Literal["notification_snapshot"] = "notification_snapshot"
    unread_count: int


class NotificationCreatedMessage(BaseModel):
    type: Literal["notification_created"] = "notification_created"
    notification: NotificationItem
    unread_count: int


class NotificationUpdatedMessage(BaseModel):
    type: Literal["notification_updated"] = "notification_updated"
    notification_id: SchemaUUID
    is_read: bool
    read_at: datetime | None = None
    unread_count: int


class NotificationsReadAllMessage(BaseModel):
    type: Literal["notifications_read_all"] = "notifications_read_all"
    unread_count: int
