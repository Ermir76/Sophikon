"""
Comment model for comments on tasks, projects, and other entities.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Comment(Base):
    """
    Comments on tasks, projects, and other entities.

    Supports threading via parent_comment_id and @mentions via mentions array.
    Uses soft delete for recovery.
    """

    __tablename__ = "comment"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Polymorphic Entity Reference
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Entity type (task, project)",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Entity ID (polymorphic)",
    )

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Threading (reply-to)
    parent_comment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comment.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Mentions (array of user IDs)
    mentions: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        server_default=text("'{}'"),
        comment="Array of mentioned user IDs",
    )

    # Edit Tracking
    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_comment_entity",
            entity_type,
            entity_id,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_comment_author",
            author_id,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_comment_parent",
            parent_comment_id,
            postgresql_where=text("parent_comment_id IS NOT NULL"),
        ),
    )

    # Relationships
    author: Mapped["User"] = relationship(back_populates="comments")
    parent_comment: Mapped["Comment | None"] = relationship(
        back_populates="replies", remote_side="Comment.id"
    )
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent_comment")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id})>"
