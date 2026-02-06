"""
Assignment model for resource assignments to tasks.
"""

from sqlalchemy import (
    String,
    TIMESTAMP,
    Date,
    Integer,
    DECIMAL,
    CheckConstraint,
    Index,
    ForeignKey,
    UniqueConstraint,
    func,
    text,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, date
from uuid_utils import uuid7
from app.core.database import Base
import uuid


class Assignment(Base):
    """
    Resource assignments to tasks.

    Links resources to tasks with allocation percentages and work tracking.
    """

    __tablename__ = "assignment"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Allocation
    units: Mapped[float] = mapped_column(
        DECIMAL(5, 2),  # 1.00 = 100%
        nullable=False,
        server_default=text("1.0"),
    )

    # Work (in minutes)
    work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    actual_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    remaining_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # Dates (May differ from task dates)
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    finish_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    actual_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    actual_finish: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Work Contour (How the work is distributed over time)
    work_contour: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'FLAT'"),
    )

    # Custom Contour Data (if work_contour is 'CONTOURED')
    contour_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Costs
    cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )
    actual_cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )
    remaining_cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    # Which rate table to use (A, B, C, D)
    rate_table: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        server_default=text("'A'"),
    )

    # Progress
    percent_work_complete: Mapped[float] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("0"),
    )

    # Confirmed by resource (by timesheet approval)
    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint(
            task_id,
            resource_id,
            name="uq_assignment_task_resource",
        ),
        CheckConstraint(
            "work_contour IN ('FLAT', 'BACK_LOADED', 'FRONT_LOADED', 'DOUBLE_PEAK', 'EARLY_PEAK', 'LATE_PEAK', 'BELL', 'TURTLE', 'CONTOURED')",
            name="check_assignment_work_contour",
        ),
        Index(
            "idx_assignment_task",
            task_id,
        ),
        Index(
            "idx_assignment_resource",
            resource_id,
        ),
    )

    # Relationships (will be added later)
    # task: Mapped["Task"] = relationship(back_populates="assignments")
    # resource: Mapped["Resource"] = relationship(back_populates="assignments")

    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, task_id={self.task_id}, resource_id={self.resource_id})>"
