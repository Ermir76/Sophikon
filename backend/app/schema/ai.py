from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schema._uuid import SchemaUUID


class UiContext(BaseModel):
    current_view: str = Field(default="overview", max_length=64)
    selected_task_id: SchemaUUID | None = None
    selected_task_ids: list[SchemaUUID] = Field(default_factory=list, max_length=200)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(max_length=32768)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: SchemaUUID | None = None
    ui_context: UiContext | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=30)


class AIUsageMeta(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None


class AIApprovalRequest(BaseModel):
    approved: bool


class AIPlanApprovalRequest(BaseModel):
    approved: bool
    feedback: str | None = Field(default=None, max_length=2000)


class ConversationSummaryResponse(BaseModel):
    id: SchemaUUID
    title: str | None = None
    status: str
    mode: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]


class MessageResponse(BaseModel):
    id: SchemaUUID
    role: str
    content: str
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    id: SchemaUUID
    title: str | None = None
    status: str
    mode: str
    messages: list[MessageResponse]


class AIEstimateRequest(BaseModel):
    task_ids: list[SchemaUUID] = Field(default_factory=list, max_length=100)
    task_name: str | None = Field(default=None, max_length=500)
    task_description: str | None = Field(default=None, max_length=4000)
    include_reasoning: bool = True
    ui_context: UiContext | None = None

    @model_validator(mode="after")
    def validate_task_inputs(self) -> "AIEstimateRequest":
        if self.task_ids or self.task_name:
            return self
        raise ValueError("Provide task_ids or task_name")


class AIEstimateItem(BaseModel):
    task_id: SchemaUUID | None = None
    task_name: str
    optimistic_minutes: int
    likely_minutes: int
    pessimistic_minutes: int
    recommended_minutes: int
    confidence: float
    reasoning: str | None = None


class AIEstimateResponse(BaseModel):
    estimates: list[AIEstimateItem]
    usage: AIUsageMeta


class AISuggestionAction(BaseModel):
    type: Literal["NONE", "UPDATE_TASK", "ADD_DEPENDENCY", "SET_PRIORITY"]
    # NOTE: Temporary generic payload contract.
    # TODO: Replace with typed payload models per action type (discriminated union)
    # before expanding suggestion generation/automation beyond current deterministic logic.
    payload: dict = Field(default_factory=dict)


class AISuggestionItem(BaseModel):
    id: str
    type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    title: str
    description: str
    affected_task_id: SchemaUUID | None = None
    suggested_action: AISuggestionAction | None = None


class AISuggestionsResponse(BaseModel):
    suggestions: list[AISuggestionItem]
    usage: AIUsageMeta


class ProjectContextTask(BaseModel):
    id: SchemaUUID
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
    project_id: SchemaUUID
    name: str
    description: str | None = None
    status: str
    start_date: date
    finish_date: date | None = None
    updated_at: datetime
    tasks: list[ProjectContextTask] = Field(default_factory=list)


class AIServiceEstimateTaskInput(BaseModel):
    task_id: SchemaUUID | None = None
    task_name: str
    task_description: str | None = None
    duration: int | None = None


class AIServiceChatRequest(BaseModel):
    message: str
    project_context: ProjectContext
    conversation_id: SchemaUUID | None = None
    user_id: SchemaUUID
    ui_context: UiContext | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list)


class AIServiceEstimateRequest(BaseModel):
    project_context: ProjectContext
    task_inputs: list[AIServiceEstimateTaskInput]
    include_reasoning: bool = True


class AIServiceSuggestionsRequest(BaseModel):
    project_context: ProjectContext
    limit: int = Field(default=5, ge=1, le=20)
    ui_context: UiContext | None = None
