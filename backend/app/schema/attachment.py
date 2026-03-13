"""
Pydantic schemas for task attachment endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentResponse(BaseModel):
    """Attachment response payload for task-scoped endpoints."""

    id: uuid.UUID
    task_id: uuid.UUID
    uploaded_by_id: uuid.UUID
    file_name: str
    file_size: int
    mime_type: str
    description: str | None
    created_at: datetime
    download_url: str


class AttachmentUploadForm(BaseModel):
    """Optional metadata accepted on upload."""

    description: str | None = Field(default=None, max_length=500)
