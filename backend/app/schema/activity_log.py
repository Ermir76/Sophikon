"""
Pydantic schemas for project activity log endpoints.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.models.enums import AuditAction

ActivityEntityType = Literal[
    "project",
    "task",
    "resource",
    "assignment",
    "dependency",
    "project_member",
]


class ActivityActor(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    avatar_url: str | None = None


class ActivityChangeField(BaseModel):
    field: str
    old: Any = None
    new: Any = None


class ActivityChanges(BaseModel):
    fields: list[ActivityChangeField]


class ActivityLogItem(BaseModel):
    id: uuid.UUID
    user: ActivityActor | None = None
    action: AuditAction
    entity_type: ActivityEntityType
    entity_id: uuid.UUID | None = None
    entity_name: str | None = None
    changes: ActivityChanges | None = None
    created_at: datetime
