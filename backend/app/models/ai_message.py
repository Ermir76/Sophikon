"""
AIMessage model for individual messages in AI conversations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base
from app.models.enums import AIMessageRole

if TYPE_CHECKING:
    from app.models.ai_conversation import AIConversation


class AIMessage(Base):
    """
    Individual messages in AI conversations.

    Stores both user and assistant messages with token usage
    and latency metrics for analytics.
    """

    __tablename__ = "ai_message"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Key
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message Content
    role: Mapped[AIMessageRole] = mapped_column(
        String(20),
        nullable=False,
        comment="user, assistant, system",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Model Info (for assistant messages)
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Model used (for assistant)",
    )

    # Token Usage
    tokens_in: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Input tokens",
    )
    tokens_out: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Output tokens",
    )

    # Performance Metrics
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Response time in milliseconds",
    )
    finish_reason: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Stop reason",
    )

    # Tool/Function Calls
    tool_calls: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tool/function calls",
    )
    tool_results: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tool results",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="check_ai_message_role",
        ),
        Index("idx_ai_message_conversation", conversation_id, created_at),
    )

    # Relationships
    conversation: Mapped["AIConversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<AIMessage(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"
