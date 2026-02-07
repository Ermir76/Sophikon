"""
Task model for work breakdown structure (WBS) and scheduling.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    Text,
    TIMESTAMP,
    Date,
    Integer,
    DECIMAL,
    CheckConstraint,
    Index,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import TaskType, ConstraintType, CostAccrual
import uuid

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.calendar import Calendar
    from app.models.assignment import Assignment
    from app.models.dependency import Dependency
    from app.models.task_baseline import TaskBaseline
    from app.models.time_entry import TimeEntry


class Task(Base):
    """
    Work breakdown structure (WBS) tasks with full scheduling data.

    Supports hierarchical task structure, dependencies, resource assignments,
    and earned value management (EVM) metrics.
    """

    __tablename__ = "task"

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
        index=True,
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task.id"),
        nullable=True,
    )

    # WBS Structure
    wbs_code: Mapped[str] = mapped_column(
        String(50),  # "1.2.3"
        nullable=False,
    )
    outline_level: Mapped[int] = mapped_column(
        Integer,  # Depth in hierarchy
        nullable=False,
        server_default=text("1"),
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,  # Sort order within siblings
    )

    # Basic Info
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Task Type Flags
    is_milestone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    is_summary: Mapped[bool] = mapped_column(
        Boolean,  # Has children
        nullable=False,
        server_default=text("FALSE"),
    )
    is_critical: Mapped[bool] = mapped_column(
        Boolean,  # On critical path(calculated)
        nullable=False,
        server_default=text("FALSE"),
    )

    # Calendar
    calendar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar.id"),
        nullable=True,
    )

    # Duration and Work (in minutes)
    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("480"),
    )
    work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    actual_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    actual_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    remaining_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("480"),
    )
    remaining_work: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # Dates
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

    # Progress
    percent_complete: Mapped[float] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("0"),
    )
    percent_work_complete: Mapped[float] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        server_default=text("0"),
    )

    # Task Type and Scheduling
    task_type: Mapped[TaskType] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'FIXED_UNITS'"),
    )
    effort_driven: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    # Constraints
    constraint_type: Mapped[ConstraintType] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'ASAP'"),
    )
    constraint_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    deadline: Mapped[date | None] = mapped_column(
        Date,  # Soft deadline (shows indicator if late)
        nullable=True,
    )

    # Slack (in minutes) calculated by scheduler
    total_slack: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    free_slack: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    # Priority
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("500"),
    )

    # Costs (calculated from assignments)
    fixed_cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )
    fixed_cost_accrual: Mapped[CostAccrual] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'PRORATED'"),
    )
    total_cost: Mapped[float] = mapped_column(
        DECIMAL(15, 2),  # Calculated
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

    # Earned Value Management (EVM)
    bcws: Mapped[float] = mapped_column(
        DECIMAL(15, 2),  # Budgeted Cost of Work Scheduled
        nullable=False,
        server_default=text("0"),
    )
    bcwp: Mapped[float] = mapped_column(
        DECIMAL(15, 2),  # Budgeted Cost of Work Performed
        nullable=False,
        server_default=text("0"),
    )
    acwp: Mapped[float] = mapped_column(
        DECIMAL(15, 2),  # Actual Cost of Work Performed
        nullable=False,
        server_default=text("0"),
    )

    # External Integration (for import from other systems)
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Soft Delete
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

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "percent_complete >= 0 AND percent_complete <= 100",
            name="check_task_percent_complete",
        ),
        CheckConstraint(
            "percent_work_complete >= 0 AND percent_work_complete <= 100",
            name="check_task_percent_work_complete",
        ),
        CheckConstraint(
            "task_type IN ('FIXED_UNITS', 'FIXED_DURATION', 'FIXED_WORK')",
            name="check_task_type",
        ),
        CheckConstraint(
            "constraint_type IN ('ASAP', 'ALAP', 'MSO', 'MFO', 'SNET', 'SNLT', 'FNET', 'FNLT')",
            name="check_task_constraint_type",
        ),
        CheckConstraint(
            "fixed_cost_accrual IN ('START', 'END', 'PRORATED')",
            name="check_task_fixed_cost_accrual",
        ),
        CheckConstraint(
            "priority >= 0 AND priority <= 1000",
            name="check_task_priority",
        ),
        Index(
            "idx_task_project",
            project_id,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_task_parent",
            parent_task_id,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_task_project_order",
            project_id,
            order_index,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_task_project_wbs",
            project_id,
            wbs_code,
            postgresql_where=text("NOT is_deleted"),
        ),
        Index(
            "idx_task_dates",
            project_id,
            start_date,
            finish_date,
            postgresql_where=text("NOT is_deleted"),
        ),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tasks")
    calendar: Mapped["Calendar | None"] = relationship(back_populates="tasks")
    parent: Mapped["Task | None"] = relationship(
        back_populates="children", remote_side="Task.id"
    )
    children: Mapped[list["Task"]] = relationship(back_populates="parent")
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    predecessors: Mapped[list["Dependency"]] = relationship(
        back_populates="successor",
        foreign_keys="Dependency.successor_id",
        cascade="all, delete-orphan",
    )
    successors: Mapped[list["Dependency"]] = relationship(
        back_populates="predecessor",
        foreign_keys="Dependency.predecessor_id",
        cascade="all, delete-orphan",
    )
    baselines: Mapped[list["TaskBaseline"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    time_entries: Mapped[list["TimeEntry"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name='{self.name}', wbs='{self.wbs_code}')>"
