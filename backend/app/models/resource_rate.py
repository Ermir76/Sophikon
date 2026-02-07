"""
ResourceRate model for cost rate tables with effective dates.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import RateTable
import uuid

if TYPE_CHECKING:
    from app.models.resource import Resource


class ResourceRate(Base):
    """
    Cost rate tables (A-E) with effective dates.

    Allows multiple rate tables per resource with different
    effective dates for rate changes over time.
    """

    __tablename__ = "resource_rate"

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

    # Rate Table (A-E)
    rate_table: Mapped[RateTable] = mapped_column(
        nullable=False,
        server_default=text("'A'"),
        comment="Rate table (A, B, C, D, E)",
    )

    # Effective Date
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Effective from date",
    )

    # Rate Data
    standard_rate: Mapped[float] = mapped_column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Hourly rate",
    )
    overtime_rate: Mapped[float] = mapped_column(
        DECIMAL(15, 4),
        nullable=False,
        server_default=text("0"),
        comment="Overtime hourly rate",
    )
    cost_per_use: Mapped[float] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
        comment="Per-use cost",
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
            "resource_id",
            "rate_table",
            "effective_date",
            name="uq_resource_rate_table_date",
        ),
        CheckConstraint(
            "rate_table IN ('A', 'B', 'C', 'D', 'E')",
            name="check_resource_rate_table",
        ),
        Index("idx_resource_rate_resource", resource_id),
    )

    # Relationships
    resource: Mapped["Resource"] = relationship(back_populates="rates")

    def __repr__(self) -> str:
        return f"<ResourceRate(id={self.id}, resource_id={self.resource_id}, table='{self.rate_table}')>"
