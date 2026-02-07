"""
ProjectMember model for project team membership with RBAC roles.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
import uuid

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.role import Role
    from app.models.resource import Resource


class ProjectMember(Base):
    """
    Project team membership with RBAC roles.

    Links users to projects with specific project-level roles (owner, manager, member, viewer).
    Optionally links to a resource if the user is also a resource on the project.
    """

    __tablename__ = "project_member"

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Project role: owner, manager, member, viewer",
    )

    # Optional Resource Link
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="SET NULL"),
        nullable=True,
        comment="Linked resource if user is also a resource",
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
        # One membership per user per project
        UniqueConstraint("project_id", "user_id", name="uq_project_member_user"),
        # Index for finding user's projects
        Index("idx_project_member_user", user_id),
        # Index for finding project's members
        Index("idx_project_member_project", project_id),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_memberships")
    role: Mapped["Role"] = relationship(back_populates="project_members")
    resource: Mapped["Resource | None"] = relationship(back_populates="project_member")

    def __repr__(self) -> str:
        return f"<ProjectMember(id={self.id}, project_id={self.project_id}, user_id={self.user_id})>"
