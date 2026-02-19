"""
EmailVerification model for email verification flow.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class EmailVerification(Base):
    """
    Temporary tokens for email verification flow.

    Tokens are single-use and expire after 24 hours.
    """

    __tablename__ = "email_verification"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Foreign Key to User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Token (SHA-256 hash)
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="SHA-256 hash of verification token",
    )

    # Token Lifecycle
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Expiration (24 hours)",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When token was used",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (Index("idx_email_verification_user", user_id),)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="email_verifications")

    def __repr__(self) -> str:
        return f"<EmailVerification(id={self.id}, user_id={self.user_id})>"
