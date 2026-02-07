"""
ResourceAvailability model for resource availability periods.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Date,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from uuid_utils import uuid7
from app.core.database import Base
import uuid

if TYPE_CHECKING:
    from app.models.resource import Resource


class ResourceAvailability(Base):
    """
    Resource availability periods (for part-time, contractors, etc.).

    Defines time periods when a resource is available at a specific
    capacity (e.g., 50% for part-time workers).
    """

    __tablename__ = "resource_availability"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Key
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Availability Period
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Period start date",
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Period end date (NULL = indefinite)",
    )

    # Availability Units (1.0 = 100%)
    units: Mapped[float] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        comment="Availability (1.0 = 100%)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (Index("idx_resource_availability", resource_id, start_date),)

    # Relationships
    resource: Mapped["Resource"] = relationship(back_populates="availability_periods")

    def __repr__(self) -> str:
        return f"<ResourceAvailability(id={self.id}, resource_id={self.resource_id}, units={self.units})>"
