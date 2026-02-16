"""
ActivityLog model for audit trail of all project changes.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base
from app.models.enums import AuditAction

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class ActivityLog(Base):
    """
    Audit trail of all project changes.

    Logs all CRUD operations with actor info, changes made,
    and client metadata for security and compliance.
    """

    __tablename__ = "activity_log"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys (nullable for deleted entities)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Actor",
    )

    # Action Info
    action: Mapped[AuditAction] = mapped_column(
        String(50),
        nullable=False,
        comment="Action (created, updated, deleted, restored)",
    )

    # Entity Reference
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Entity type (task, resource, etc.)",
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    entity_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Entity name (for display after delete)",
    )

    # Changes (for updates)
    changes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="What changed (for updates)",
    )

    # Client Metadata
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        comment="Client IP",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Browser/client",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Action timestamp",
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_activity_log_project",
            project_id,
            created_at.desc(),
            postgresql_where=text("project_id IS NOT NULL"),
        ),
        Index("idx_activity_log_user", user_id, created_at.desc()),
        Index("idx_activity_log_entity", entity_type, entity_id),
    )

    # Relationships
    project: Mapped["Project | None"] = relationship(back_populates="activity_logs")
    user: Mapped["User | None"] = relationship(back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"
