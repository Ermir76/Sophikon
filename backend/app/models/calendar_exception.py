"""
CalendarException model for holidays and special working days.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Date,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.calendar import Calendar


class CalendarException(Base):
    """
    Holidays and special working days.

    Exceptions can be non-working (holidays) or working (special days).
    Supports recurrence patterns for annual events.
    """

    __tablename__ = "calendar_exception"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Key
    calendar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Exception Info
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Exception name (e.g., 'Christmas')",
    )

    # Date Range
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Working Status
    is_working: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
        comment="Is this a working exception?",
    )

    # Custom Work Times (if is_working=TRUE) Overrides work_week
    work_times: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Custom hours if is_working=TRUE",
    )

    # Recurrence Pattern (e.g., yearly holidays)
    recurrence: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Recurrence pattern (e.g., {'type': 'yearly', 'month': 12, 'day': 25})",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index("idx_calendar_exception_calendar", calendar_id),
        Index("idx_calendar_exception_dates", calendar_id, start_date, end_date),
    )

    # Relationships
    calendar: Mapped["Calendar"] = relationship(back_populates="exceptions")

    def __repr__(self) -> str:
        return f"<CalendarException(id={self.id}, name='{self.name}', start={self.start_date})>"
