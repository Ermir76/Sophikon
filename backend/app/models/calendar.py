"""
Calendar model for work calendars defining working hours.
"""

from sqlalchemy import (
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
import uuid


class Calendar(Base):
    """
    Work calendars defining working hours and holidays.

    Supports calendar inheritance (base calendars) and project-specific calendars.
    Global calendars have NULL project_id.
    """

    __tablename__ = "calendar"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Keys
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL = global calendar",
    )
    # Inheritance (e.g., "Night Shift" inherits from "Standard")
    base_calendar_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar.id", ondelete="SET NULL"),
        nullable=True,
        comment="Parent calendar for inheritance",
    )

    # Calendar Info
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    is_base: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Is this a base/template calendar?",
    )

    # Work Week Pattern (7-day array, Sunday=0)
    work_week: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("""'[
            null,
            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},
            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},
            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},
            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},
            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},
            null
        ]'::jsonb"""),
        comment="7-day work pattern (Sunday=0)",
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
    __table_args__ = (Index("idx_calendar_project", project_id),)

    # Relationships (will be added after other models)
    # project: Mapped["Project"] = relationship(back_populates="calendars")
    # base_calendar: Mapped["Calendar"] = relationship(remote_side=[id])
    # exceptions: Mapped[list["CalendarException"]] = relationship(back_populates="calendar")

    def __repr__(self) -> str:
        return f"<Calendar(id={self.id}, name='{self.name}', is_base={self.is_base})>"
