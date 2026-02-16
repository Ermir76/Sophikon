"""
AssignmentBaseline model for baseline snapshots of assignments.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment


class AssignmentBaseline(Base):
    """
    Baseline snapshots of assignments.

    Stores up to 11 baselines (0-10) per assignment for tracking
    work and cost variance over time.
    """

    __tablename__ = "assignment_baseline"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Key
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Baseline Number (0-10)
    baseline_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Baseline number (0-10)",
    )

    # Snapshot Data
    work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Snapshot work in minutes",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Snapshot start date",
    )
    finish_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Snapshot finish date",
    )
    cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Snapshot cost",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Baseline save timestamp",
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "baseline_number", name="uq_assignment_baseline_number"
        ),
        CheckConstraint(
            "baseline_number >= 0 AND baseline_number <= 10",
            name="check_assignment_baseline_number",
        ),
        Index("idx_assignment_baseline", assignment_id),
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(back_populates="baselines")

    def __repr__(self) -> str:
        return f"<AssignmentBaseline(id={self.id}, assignment_id={self.assignment_id}, baseline={self.baseline_number})>"
