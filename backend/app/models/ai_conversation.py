"""
AIConversation model for AI chat conversations scoped to projects.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    TIMESTAMP,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
import uuid

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.ai_message import AIMessage


class AIConversation(Base):
    """
    AI chat conversations scoped to projects.

    Each conversation belongs to a user within a project context
    and contains multiple messages.
    """

    __tablename__ = "ai_conversation"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project context",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Conversation owner",
    )

    # Conversation Info
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Conversation title (auto or user-set)",
    )

    # Context Snapshot (cached for performance)
    context_snapshot: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Cached context (optional)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index("idx_ai_conversation_project", project_id),
        Index("idx_ai_conversation_user", user_id),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="ai_conversations")
    user: Mapped["User"] = relationship(back_populates="ai_conversations")
    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
