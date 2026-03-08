"""
Pydantic schemas for comment endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CommentEntityType


class CommentAuthor(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    avatar_url: str | None = None


class CommentCreate(BaseModel):
    entity_type: CommentEntityType
    entity_id: uuid.UUID
    content: str = Field(min_length=1, max_length=5000)
    parent_comment_id: uuid.UUID | None = None


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentItem(BaseModel):
    id: uuid.UUID
    entity_type: CommentEntityType
    entity_id: uuid.UUID
    author: CommentAuthor
    content: str
    mentions: list[uuid.UUID]
    parent_comment_id: uuid.UUID | None = None
    is_edited: bool
    edited_at: datetime | None = None
    created_at: datetime
    replies: list["CommentItem"] = Field(default_factory=list)


class CommentListResponse(BaseModel):
    data: list[CommentItem]


CommentItem.model_rebuild()
