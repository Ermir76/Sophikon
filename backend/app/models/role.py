"""
Role model for RBAC (Role-Based Access Control).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base
from app.models.enums import RoleScope

if TYPE_CHECKING:
    from app.models.project_member import ProjectMember
    from app.models.user import User


class Role(Base):
    """
    Role-based access control for both system-level and project-level permissions.

    System roles (admin, user) are seeded and cannot be modified/deleted.
    Project roles (owner, manager, member, viewer) can be customized per project.
    """

    __tablename__ = "role"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Role Identity
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Permissions (JSONB array of strings)
    # Format: ["resource:action"] e.g. ["project:*", "task:read", "task:update"]
    permissions: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Permission array: ['resource:action']",
    )

    # Role Type
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="System roles cannot be modified/deleted",
    )

    # Scope: 'system' or 'project'
    scope: Mapped[RoleScope] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'project'"),
        comment="'system' or 'project'",
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

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "scope IN ('system', 'project')", name="check_role_scope_valid"
        ),
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="system_role")
    project_members: Mapped[list["ProjectMember"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', scope='{self.scope}')>"
