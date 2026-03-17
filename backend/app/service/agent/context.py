"""
AgentContext — per-run context for a single agent invocation.

No global state. Every run gets its own context instance.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


@dataclass
class AgentContext:
    project_id: UUID
    user_id: UUID
    conversation_id: UUID
    db: AsyncSession
    project: Project
    provider: str
    model: str
    api_key: str  # user's own key; forwarded to ai-service in Phase 3
