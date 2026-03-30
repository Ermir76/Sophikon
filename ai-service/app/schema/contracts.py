from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

CacheTag = Annotated[str, Field(min_length=1, max_length=64)]


class PromptCacheMetadata(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    ttl_seconds: int | None = Field(default=None, ge=1, le=86_400)
    tags: list[CacheTag] = Field(default_factory=list, max_length=8)


class CompleteRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list, max_length=200)
    tools: list[dict] = Field(default_factory=list, max_length=50)
    system_prompt: str = Field(default="", max_length=16000)
    provider: str | None = Field(default=None, max_length=32)
    model: str | None = Field(default=None, max_length=128)
    api_key: str | None = None
    conversation_id: UUID | None = None
    prompt_cache: PromptCacheMetadata | None = None


class AIUsageMeta(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None


class ChatEvent(BaseModel):
    type: Literal["start", "chunk", "done", "error", "tool_call", "reasoning"]
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    content: str | None = None
    usage: AIUsageMeta | None = None
    error: str | None = None
    model: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
