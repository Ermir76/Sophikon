"""
ProjectInvitation model for email invitations to join projects.
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.role import Role
    from app.models.user import User


class ProjectInvitation(Base):
    """
    Email invitations to join projects.

    Supports inviting users by email with a specific role.
    Invitations expire after 7 days and can be revoked.
    """

    __tablename__ = "project_invitation"

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
    )
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who sent the invitation",
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Role to assign when accepted",
    )

    # Invitation Details
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Invitee email address",
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="SHA-256 hash of invitation token",
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Personal message from inviter",
    )

    # Expiration & Status
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Expires 7 days from creation",
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When invitation was accepted",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Invitation cancelled flag",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (
        # Index for pending invitations by project
        Index(
            "idx_invitation_project_pending",
            project_id,
            postgresql_where=(text("NOT is_revoked AND accepted_at IS NULL")),
        ),
        # Index for pending invitations by email
        Index(
            "idx_invitation_email_pending",
            email,
            postgresql_where=(text("NOT is_revoked AND accepted_at IS NULL")),
        ),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="invitations")
    invited_by: Mapped["User"] = relationship(back_populates="sent_invitations")
    role: Mapped["Role"] = relationship()

    def __repr__(self) -> str:
        return f"<ProjectInvitation(id={self.id}, project_id={self.project_id}, email='{self.email}')>"
