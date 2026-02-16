"""
OrganizationMember model for organization-level membership and roles.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class OrganizationMember(Base):
    """
    Organization membership with role-based access.

    Links users to organizations with a role (owner, admin, member).
    This is separate from project-level roles (project_member table).
    """

    __tablename__ = "organization_member"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role (stored as string enum, not FK — simpler than project roles)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Organization role: owner, admin, member",
    )

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
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

    # Constraints & Indexes
    __table_args__ = (
        # One membership per user per organization
        UniqueConstraint(
            "organization_id", "user_id", name="uq_organization_member_user"
        ),
        # Validate role values
        CheckConstraint(
            "role IN ('owner', 'admin', 'member')",
            name="check_org_member_role",
        ),
        # Index for finding user's organizations
        Index("idx_org_member_user", user_id),
        # Index for finding organization's members
        Index("idx_org_member_org", organization_id),
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="organization_memberships")

    def __repr__(self) -> str:
        return f"<OrganizationMember(id={self.id}, org_id={self.organization_id}, user_id={self.user_id}, role='{self.role}')>"
