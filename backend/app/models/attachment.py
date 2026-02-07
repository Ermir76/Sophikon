"""
Attachment model for file attachments on tasks, projects, comments.
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    BigInteger,
    Boolean,
    Text,
    TIMESTAMP,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid_utils import uuid7
from app.core.database import Base
from app.models.enums import StorageProvider
import uuid

if TYPE_CHECKING:
    from app.models.user import User


class Attachment(Base):
    """
    File attachments on tasks, projects, comments.

    Stores file metadata with reference to storage location (local or S3).
    Uses soft delete for recovery.
    """

    __tablename__ = "attachment"

    # Primary Key (app-generated)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )

    # Polymorphic Entity Reference
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Entity type (task, project, comment)",
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Entity ID (polymorphic)",
    )

    # Uploader
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # File Metadata
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original filename",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Size in bytes",
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Storage
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="S3 path or local path",
    )
    storage_provider: Mapped[StorageProvider] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'local'"),
    )

    # Description
    description: Mapped[str | None] = mapped_column(
        Text,
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
        comment="Upload timestamp",
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_attachment_entity",
            entity_type,
            entity_id,
            postgresql_where=text("NOT is_deleted"),
        ),
    )

    # Relationships
    uploaded_by: Mapped["User"] = relationship(back_populates="attachments")

    def __repr__(self) -> str:
        return f"<Attachment(id={self.id}, file_name='{self.file_name}')>"
