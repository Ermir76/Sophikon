"""
Project Model for project management and scheduling.
"""

from sqlalchemy import (
    String,
    Boolean,
    Text,
    TIMESTAMP,
    Date,
    DECIMAL,
    CheckConstraint,
    Index,
    func,
    text,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, date
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import ProjectStatus, ScheduleFrom
import uuid


class Project(Base):
    """
    Main project table containing scheduling configuration and settings.

    Supports both forward (from start) and backward (from finish) scheduling.
    """

    __tablename__ = "project"
    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )
    # Foreign Key to Owner
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Project Metadata
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # Scheduling Configuration
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    finish_date: Mapped[date] = mapped_column(
        Date,  # calculated from tasks
        nullable=True,
    )
    status_date: Mapped[date] = mapped_column(
        Date,  # Current progress date
        nullable=True,
    )

    # Scheduling Mode
    schedule_from: Mapped[ScheduleFrom] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'START'"),
        comment="'start' or 'finish'",
    )

    # Default Calendar for new tasks
    default_calendar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Project Status
    status: Mapped[ProjectStatus] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'PLANNING'"),
        comment="'planning', 'active', 'on_hold', 'completed', 'cancelled'",
    )

    # Financials
    budget: Mapped[float | None] = mapped_column(
        DECIMAL(15, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default=text("'USD'"),
    )

    # Settings(hours per day, working days per week, etc.)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("""'{
        "hours_per_day": 8,
        "hours_per_week": 40,
        "days_per_month": 20,
        "first_day_of_week": 1,
        "default_task_type": "FIXED_UNITS",
        "new_tasks_effort_driven": true,
        "auto_calculate": true
        }'::jsonb"""),
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
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

    # Indexes
    __table_args__ = (
        # Constraint for status
        CheckConstraint(
            "status IN ('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED')",
            name="check_project_status",
        ),
        # Constraint for schedule_from
        CheckConstraint(
            "schedule_from IN ('START', 'FINISH')",
            name="check_project_schedule_from",
        ),
        # Index for active projects
        Index(
            "idx_project_owner",
            owner_id,
            postgresql_where=(text("NOT is_deleted")),
        ),
        # Index for project expiration cleanup
        Index(
            "idx_project_status",
            status,
            postgresql_where=(text("NOT is_deleted")),
        ),
    )

    # Relationships (will be added after other models)
    # user: Mapped["User"] = relationship(back_populates="projects")
    # calendar: Mapped["Calendar"] = relationship(back_populates="projects")
    # tasks: Mapped[list["Task"]] = relationship(back_populates="project")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
