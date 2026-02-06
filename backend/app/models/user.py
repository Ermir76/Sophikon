"""
User model for authentication and profile management.
"""

from sqlalchemy import String, Boolean, TIMESTAMP, text, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
import uuid


class User(Base):
    """
    Core user account table for authentication and profile management.

    Supports both password-based and OAuth authentication.
    """

    __tablename__ = "user"

    # Primary Key - UUIDv7 for time-ordered sorting (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid7
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # NULL for OAuth users
        comment="bcrypt hash, NULL for OAuth users",
    )

    # Profile
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # System Role (Foreign Key - will add relationship after Role model)
    system_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        # FK will be added in migration: REFERENCES role(id)
    )

    # OAuth Support
    oauth_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="OAuth provider: 'google', 'github', etc.",
    )
    oauth_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider's user ID",
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    # User Preferences (JSONB for flexibility)
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="User settings: theme, notifications, etc.",
    )

    # Localization
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'UTC'"),
    )
    locale: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'en-US'"),
    )

    # Timestamps
    last_login_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
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
    __table_args__ = (
        # Unique constraint for OAuth (only when provider is not NULL)
        Index(
            "idx_user_oauth",
            oauth_provider,
            oauth_id,
            unique=True,
            postgresql_where=(oauth_provider.isnot(None)),
        ),
    )

    # Relationships (will be added after other models are created)
    # system_role: Mapped["Role"] = relationship(back_populates="users")
    # projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    # refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"
        )
