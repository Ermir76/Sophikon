"""
Service-layer AI contracts.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.service.contracts._uuid import ContractUUID


class UiContext(BaseModel):
    current_view: str = Field(default="overview", max_length=64)
    selected_task_id: ContractUUID | None = None
    selected_task_ids: list[ContractUUID] = Field(default_factory=list, max_length=200)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str | list[dict] = Field(default="")


class ToolResultInput(BaseModel):
    tool_use_id: str
    content: str
    is_error: bool = False


class AIChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: ContractUUID | None = None
    ui_context: UiContext | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=30)


class AIUsageMeta(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0
    model: str | None = None


class AIChatEvent(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    type: Literal[
        "start",
        "chunk",
        "done",
        "error",
        "tool_call",
        "tool_result",
        "approval_required",
        "ui_action",
        "plan",
        "plan_approved",
        "reasoning",
    ]
    conversation_id: ContractUUID | None = None
    message_id: ContractUUID | None = None
    content: str | None = None
    usage: AIUsageMeta | None = None
    # NOTE: two error fields exist because this model is reused in both directions:
    # - `error`   — read when parsing incoming ai-service events (ai-service ChatEvent uses this field)
    # - `message` — written when building outgoing frontend events (streaming.py uses this field)
    # TODO: align ai-service ChatEvent to use `message` instead of `error`, then drop `error` here
    #       so there is one field, one contract, one direction.
    error: str | None = None
    model: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    approval_id: str | None = None
    action: str | None = None
    steps: list[dict] | None = None
    success: bool | None = None
    data: dict | list | str | int | float | bool | None = None
    payload: dict | None = None
    message: str | None = None


class AIEstimateInput(BaseModel):
    task_ids: list[ContractUUID] = Field(default_factory=list, max_length=100)
    task_name: str | None = Field(default=None, max_length=500)
    task_description: str | None = Field(default=None, max_length=4000)
    include_reasoning: bool = True
    ui_context: UiContext | None = None

    @model_validator(mode="after")
    def validate_task_inputs(self) -> "AIEstimateInput":
        if self.task_ids or self.task_name:
            return self
        raise ValueError("Provide task_ids or task_name")


class AIEstimateItem(BaseModel):
    task_id: ContractUUID | None = None
    task_name: str
    optimistic_minutes: int
    likely_minutes: int
    pessimistic_minutes: int
    recommended_minutes: int
    confidence: float
    reasoning: str | None = None


class AIEstimateResult(BaseModel):
    estimates: list[AIEstimateItem]
    usage: AIUsageMeta


class NonePayload(BaseModel):
    pass


class UpdateTaskPayload(BaseModel):
    task_id: ContractUUID
    percent_complete: float | None = None
    duration: int | None = None
    priority: int | None = None
    notes: str | None = None


class AddDependencyPayload(BaseModel):
    predecessor_id: ContractUUID
    successor_id: ContractUUID
    dependency_type: str = "FS"
    lag: int = 0


class SetPriorityPayload(BaseModel):
    task_id: ContractUUID
    priority: int


class NoneSuggestionAction(BaseModel):
    type: Literal["NONE"] = "NONE"
    payload: NonePayload = Field(default_factory=NonePayload)


class UpdateTaskSuggestionAction(BaseModel):
    type: Literal["UPDATE_TASK"] = "UPDATE_TASK"
    payload: UpdateTaskPayload


class AddDependencySuggestionAction(BaseModel):
    type: Literal["ADD_DEPENDENCY"] = "ADD_DEPENDENCY"
    payload: AddDependencyPayload


class SetPrioritySuggestionAction(BaseModel):
    type: Literal["SET_PRIORITY"] = "SET_PRIORITY"
    payload: SetPriorityPayload


AISuggestionAction = Annotated[
    NoneSuggestionAction
    | UpdateTaskSuggestionAction
    | AddDependencySuggestionAction
    | SetPrioritySuggestionAction,
    Field(discriminator="type"),
]


class AISuggestionItem(BaseModel):
    id: str
    type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    title: str
    description: str
    affected_task_id: ContractUUID | None = None
    suggested_action: AISuggestionAction | None = None


class AISuggestionsResult(BaseModel):
    suggestions: list[AISuggestionItem]
    usage: AIUsageMeta


class ProjectContextTask(BaseModel):
    id: ContractUUID
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
    project_id: ContractUUID
    name: str
    description: str | None = None
    status: str
    start_date: date
    finish_date: date | None = None
    updated_at: datetime
    tasks: list[ProjectContextTask] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Complete request (POST /v1/complete on ai-service)
# ---------------------------------------------------------------------------


class AICompleteRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    system_prompt: str = ""
    provider: str
    model: str
    api_key: str | None = None
    conversation_id: ContractUUID | None = None


# ---------------------------------------------------------------------------
# Plan approval contracts
# ---------------------------------------------------------------------------


class PlanApprovalInput(BaseModel):
    approved: bool
    feedback: str | None = Field(default=None, max_length=2000)


# ---------------------------------------------------------------------------
# Conversation contracts
# ---------------------------------------------------------------------------


class ConversationSummary(BaseModel):
    id: ContractUUID
    title: str | None = None
    status: str
    mode: str
    created_at: datetime
    updated_at: datetime


class ConversationMessage(BaseModel):
    id: ContractUUID
    role: str
    content: str
    created_at: datetime
