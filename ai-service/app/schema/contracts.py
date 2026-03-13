from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UiContext(BaseModel):
    current_view: str = Field(default="overview", max_length=64)
    selected_task_id: UUID | None = None
    selected_task_ids: list[UUID] = Field(default_factory=list, max_length=200)


class ProjectContextTask(BaseModel):
    id: UUID
    name: str
    notes: str | None = None
    start_date: date
    finish_date: date
    duration: int
    percent_complete: float
    priority: int
    is_summary: bool
    updated_at: datetime | None = None


class ProjectContext(BaseModel):
    project_id: UUID
    name: str
    description: str | None = None
    status: str
    start_date: date
    finish_date: date | None = None
    updated_at: datetime
    tasks: list[ProjectContextTask] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str | list[dict]


class ToolResultInput(BaseModel):
    tool_use_id: str
    content: str
    is_error: bool = False


class ChatRequest(BaseModel):
    message: str | None = Field(default=None, max_length=4000)
    project_context: ProjectContext
    conversation_id: UUID | None = None
    user_id: UUID
    ui_context: UiContext | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list)
    tool_results: list[ToolResultInput] = Field(default_factory=list)


class AIUsageMeta(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None


class ChatEvent(BaseModel):
    type: Literal["start", "chunk", "done", "error", "tool_call"]
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    content: str | None = None
    usage: AIUsageMeta | None = None
    error: str | None = None
    model: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None


class EstimateTaskInput(BaseModel):
    task_id: UUID | None = None
    task_name: str = Field(min_length=1, max_length=500)
    task_description: str | None = None
    duration: int | None = Field(default=None, ge=0)


class EstimateRequest(BaseModel):
    project_context: ProjectContext
    task_inputs: list[EstimateTaskInput] = Field(default_factory=list, max_length=100)
    include_reasoning: bool = True


class EstimateItem(BaseModel):
    task_id: UUID | None = None
    task_name: str
    optimistic_minutes: int
    likely_minutes: int
    pessimistic_minutes: int
    recommended_minutes: int
    confidence: float
    reasoning: str | None = None


class EstimateResponse(BaseModel):
    estimates: list[EstimateItem]
    usage: AIUsageMeta


class SuggestionAction(BaseModel):
    type: Literal["NONE", "UPDATE_TASK", "ADD_DEPENDENCY", "SET_PRIORITY"]
    # NOTE: Temporary generic payload contract.
    # TODO: Replace with typed payload models per action type (discriminated union)
    # before expanding suggestion generation/automation beyond current deterministic logic.
    payload: dict = Field(default_factory=dict)


class SuggestionItem(BaseModel):
    id: str
    type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    title: str
    description: str
    affected_task_id: UUID | None = None
    suggested_action: SuggestionAction | None = None


class SuggestionsRequest(BaseModel):
    project_context: ProjectContext
    limit: int = Field(default=5, ge=1, le=20)
    ui_context: UiContext | None = None


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]
    usage: AIUsageMeta
