"""
Pydantic schemas for notification endpoints.
"""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, computed_field, model_validator

from app.models.enums import NotificationType
from app.schema._patch import reject_explicit_nulls_for_fields_set


def _coerce_uuid(value):
    if value is None or isinstance(value, uuid.UUID):
        return value

    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


SchemaUUID = Annotated[uuid.UUID, BeforeValidator(_coerce_uuid)]


class NotificationActor(BaseModel):
    id: SchemaUUID
    full_name: str | None = None
    avatar_url: str | None = None


class NotificationItem(BaseModel):
    id: SchemaUUID
    type: NotificationType
    title: str
    message: str | None = None
    entity_type: str | None = None
    entity_id: SchemaUUID | None = None
    actor: NotificationActor | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    page: int
    per_page: int
    unread_count: int

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page


class NotificationSettings(BaseModel):
    email_task_assigned: bool = True
    email_mentioned: bool = True
    email_deadline_approaching: bool = True
    push_enabled: bool = False


class NotificationSettingsUpdate(BaseModel):
    email_task_assigned: bool | None = None
    email_mentioned: bool | None = None
    email_deadline_approaching: bool | None = None
    push_enabled: bool | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "NotificationSettingsUpdate":
        # Keep settings PATCH strict: settings keys may be omitted, but never null.
        reject_explicit_nulls_for_fields_set(self)
        return self


class NotificationReadAllResponse(BaseModel):
    updated_count: int
    unread_count: int
