"""
TimeEntry model for time logging with approval workflow.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base
from app.models.enums import BillingStatus, TimeEntryStatus

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.task import Task
    from app.models.user import User


class TimeEntry(Base):
    """
    Time logging with approval workflow.

    Tracks regular and overtime work on tasks with billable/non-billable
    status and approval flow (draft → submitted → approved/rejected).
    """

    __tablename__ = "time_entry"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        comment="Who logged time",
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Task worked on",
    )
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related assignment",
    )

    # Work Data
    work_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date worked",
    )
    regular_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Regular work in minutes",
    )
    overtime_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Overtime work in minutes",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of work",
    )

    # Billing
    is_billable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )
    billing_status: Mapped[BillingStatus] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'UNBILLED'"),
    )

    # Approval Workflow
    status: Mapped[TimeEntryStatus] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'SUBMITTED'"),
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="Approver",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
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
            "billing_status IN ('UNBILLED', 'BILLED', 'NON_BILLABLE')",
            name="check_time_entry_billing_status",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')",
            name="check_time_entry_status",
        ),
        Index("idx_time_entry_user_date", user_id, work_date),
        Index("idx_time_entry_task", task_id),
        Index(
            "idx_time_entry_assignment",
            assignment_id,
            postgresql_where=text("assignment_id IS NOT NULL"),
        ),
        Index(
            "idx_time_entry_status",
            status,
            postgresql_where=text("status = 'SUBMITTED'"),
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="time_entries", foreign_keys=[user_id]
    )
    task: Mapped["Task"] = relationship(back_populates="time_entries")
    assignment: Mapped["Assignment | None"] = relationship(
        back_populates="time_entries"
    )
    approver: Mapped["User | None"] = relationship(foreign_keys=[approved_by_id])

    def __repr__(self) -> str:
        return (
            f"<TimeEntry(id={self.id}, user_id={self.user_id}, date={self.work_date})>"
        )
