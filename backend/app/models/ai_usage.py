"""
AIUsage model for AI usage tracking and cost management.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AIUsage(Base):
    """
    AI usage tracking for cost management and rate limiting.

    Aggregates token usage by user, feature, and date for
    billing and analytics purposes.
    """

    __tablename__ = "ai_usage"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Foreign Key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # Usage Info
    feature: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Feature (chat, estimation, suggestion)",
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Model used",
    )

    # Token Usage
    tokens_in: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Input tokens",
    )
    tokens_out: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="Output tokens",
    )

    # Cost
    estimated_cost: Mapped[float] = mapped_column(
        DECIMAL(10, 6),
        nullable=False,
        server_default=text("0"),
        comment="Estimated cost in USD",
    )

    # Date (for aggregation)
    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (
        Index("idx_ai_usage_user_date", user_id, usage_date),
        Index("idx_ai_usage_date", usage_date),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_usage")

    def __repr__(self) -> str:
        return (
            f"<AIUsage(id={self.id}, user_id={self.user_id}, feature='{self.feature}')>"
        )
