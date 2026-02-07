"""
Notification model for user notifications.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    Text,
    TIMESTAMP,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import NotificationType
import uuid

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """
    User notifications for events.

    Notification types include:
    - task_assigned, task_updated, mentioned
    - comment_added, deadline_approaching
    - invitation_received
    """

    __tablename__ = "notification"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Recipient
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Notification Content
    type: Mapped[NotificationType] = mapped_column(
        String(50),
        nullable=False,
        comment="Notification type (task_assigned, mentioned, etc.)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Related Entity (optional)
    entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Related entity type",
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Related entity ID",
    )

    # Actor (who triggered the notification)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

    # Read Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    read_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Email Status
    email_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(
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
            "idx_notification_user_unread",
            user_id,
            created_at.desc(),
            postgresql_where=text("NOT is_read"),
        ),
        Index("idx_notification_user", user_id, created_at.desc()),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="notifications", foreign_keys=[user_id]
    )
    actor: Mapped["User | None"] = relationship(foreign_keys=[actor_id])

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"
        )
