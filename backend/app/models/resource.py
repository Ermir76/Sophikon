"""
Resource model for project resources (people, materials, costs).
"""

from sqlalchemy import (
    String,
    Boolean,
    TIMESTAMP,
    DECIMAL,
    CheckConstraint,
    Index,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import ResourceType, CostAccrual
import uuid


class Resource(Base):
    """
    Project resources (people, materials, costs).

    Supports work resources (people), material resources (consumables),
    and cost resources (fixed costs).
    """

    __tablename__ = "resource"

    # Primary Key
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
    )

    # Basic Info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    initials: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Resource Type
    type: Mapped[ResourceType] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'WORK'"),
    )
    material_label: Mapped[str | None] = mapped_column(
        String(50),  # tons, gallons, etc.
        nullable=True,
    )

    # Availability
    max_units: Mapped[float] = mapped_column(
        DECIMAL(5, 2),  # 1.0 = 100%
        nullable=False,
        server_default=text("1.0"),
    )

    # Calendar
    calendar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar.id"),
        nullable=True,
    )

    # Classification
    group_name: Mapped[str | None] = mapped_column(
        String(100),  # department, team, etc.
        nullable=True,
    )
    code: Mapped[str | None] = mapped_column(
        String(50),  # Resource code
        nullable=True,
    )

    # Flags (Placeholders for role)
    is_generic: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    # Cost (default rates - can be overridden by resource_rate)
    standard_rate: Mapped[float] = mapped_column(
        DECIMAL(15, 4),
        nullable=False,
        server_default=text("0"),
    )
    overtime_rate: Mapped[float] = mapped_column(
        DECIMAL(15, 4),
        nullable=False,
        server_default=text("0"),
    )
    cost_per_use: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )
    accrue_at: Mapped[CostAccrual] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'PRORATED'"),
    )

    # Link to User Account (If the resource is a team member)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

    # External ID (for imports)
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "type IN ('WORK', 'MATERIAL', 'COST')",
            name="check_resource_type",
        ),
        CheckConstraint(
            "accrue_at IN ('START', 'END', 'PRORATED')",
            name="check_resource_accrue_at",
        ),
        Index(
            "idx_resource_project",
            project_id,
            postgresql_where=text("is_active"),
        ),
        Index(
            "idx_resource_user",
            user_id,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
    )

    # Relationships (will be added later)
    # project: Mapped["Project"] = relationship(back_populates="resources")
    # user: Mapped["User"] = relationship(back_populates="resources")
    # assignments: Mapped[list["Assignment"]] = relationship(back_populates="resource")

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, name='{self.name}', type='{self.type}')>"
