from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _coerce_uuid(value):
    if value is None or isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


SchemaUUID = Annotated[UUID, BeforeValidator(_coerce_uuid)]


class UiContext(BaseModel):
    current_view: str = Field(default="overview", max_length=64)
    selected_task_id: SchemaUUID | None = None
    selected_task_ids: list[SchemaUUID] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: SchemaUUID | None = None
    ui_context: UiContext | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=30)


class AIUsageMeta(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None


class AIChatEvent(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    type: Literal["start", "chunk", "done", "error"]
    conversation_id: SchemaUUID | None = None
    message_id: SchemaUUID | None = None
    content: str | None = None
    usage: AIUsageMeta | None = None
    error: str | None = None
    model: str | None = None


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
