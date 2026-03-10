"""
Service contracts for comment use-cases.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from app.models.enums import CommentEntityType


@dataclass(frozen=True, slots=True)
class CommentEntityContext:
    entity_type: CommentEntityType
    entity_id: UUID
    project_id: UUID
    entity_name: str | None = None


class CommentAuthorData(TypedDict):
    id: UUID
    full_name: str | None
    avatar_url: str | None


class CommentItemData(TypedDict):
    id: UUID
    entity_type: CommentEntityType
    entity_id: UUID
    author: CommentAuthorData
    content: str
    mentions: list[UUID]
    parent_comment_id: UUID | None
    is_edited: bool
    edited_at: datetime | None
    created_at: datetime
    replies: list["CommentItemData"]
