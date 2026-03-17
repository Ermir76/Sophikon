"""
AgentProjectMemory model — persistent cross-session memory for the PM agent.

One row per project. The agent reads this at the start of every conversation
and updates it when a conversation ends. Stores key decisions, patterns, and
preferences that cannot be derived from the DB.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ai_conversation import AIConversation
    from app.models.project import Project


class AgentProjectMemory(Base):
    """
    Cross-session persistent memory for the PM agent, scoped to a project.

    The agent curates this content — it accumulates key decisions, user
    preferences, and observed patterns across all conversations for this project.
    Max ~600 tokens of content to keep context injection bounded.
    """

    __tablename__ = "agent_project_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="One memory record per project",
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Agent-curated key decisions, patterns, preferences (~600 tokens max)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    updated_by_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversation.id", ondelete="SET NULL"),
        nullable=True,
        comment="Last conversation that updated this memory",
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="agent_memory")
    updated_by_conversation: Mapped["AIConversation | None"] = relationship()

    def __repr__(self) -> str:
        return f"<AgentProjectMemory(project_id={self.project_id})>"
