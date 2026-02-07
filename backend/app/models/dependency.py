"""
Dependency model for task dependencies (predecessor-successor relationships).
"""

from sqlalchemy import (
    String,
    Boolean,
    TIMESTAMP,
    Integer,
    CheckConstraint,
    Index,
    ForeignKey,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import DependencyType, LagFormat
import uuid


class Dependency(Base):
    """
    Task dependencies (predecessor-successor relationships).

    Supports Finish-to-Start (FS), Finish-to-Finish (FF),
    Start-to-Start (SS), and Start-to-Finish (SF) relationships
    with lag/lead time.
    """

    __tablename__ = "dependency"

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
    )
    predecessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task.id", ondelete="CASCADE"),
        nullable=False,
    )
    successor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Dependency Type
    type: Mapped[DependencyType] = mapped_column(
        String(2),
        nullable=False,
        server_default=text("'FS'"),
    )

    # Lag/Lead
    lag: Mapped[int] = mapped_column(
        Integer,  # In minutes (negative for lead)
        nullable=False,
        server_default=text("0"),
        comment="Lag in minutes (negative for lead)",
    )
    lag_format: Mapped[LagFormat] = mapped_column(
        String(10),  #
        nullable=False,
        server_default=text("'DURATION'"),
    )

    # Can dissable without deleting
    is_disabled: Mapped[bool] = mapped_column(
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
            predecessor_id,
            successor_id,
            name="uq_dependency_predecessor_successor",
        ),
        CheckConstraint(
            "predecessor_id != successor_id",
            name="check_dependency_no_self_reference",
        ),
        CheckConstraint(
            "type IN ('FS', 'FF', 'SS', 'SF')",
            name="check_dependency_type",
        ),
        CheckConstraint(
            "lag_format IN ('DURATION', 'PERCENT')",
            name="check_dependency_lag_format",
        ),
        Index(
            "idx_dependency_project",
            project_id,
        ),
        Index(
            "idx_dependency_predecessor",
            predecessor_id,
        ),
        Index(
            "idx_dependency_successor",
            successor_id,
        ),
    )

    # Relationships (will be added later)
    # project: Mapped["Project"] = relationship(back_populates="dependencies")
    # predecessor: Mapped["Task"] = relationship(foreign_keys=[predecessor_id])
    # successor: Mapped["Task"] = relationship(foreign_keys=[successor_id])

    def __repr__(self) -> str:
        return f"<Dependency(id={self.id}, type='{self.type}', predecessor={self.predecessor_id}, successor={self.successor_id})>"
