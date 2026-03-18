"""
Service-layer contracts (API-agnostic input payloads).
"""

from app.service.contracts.activity_log import (
    ActivityChangesData,
    ActivityEntityType,
    ActivityLogItemData,
)
from app.service.contracts.ai import (
    AIChatEvent,
    AIChatInput,
    AICompleteRequest,
    AIEstimateInput,
    AIEstimateItem,
    AIEstimateResult,
    AISuggestionAction,
    AISuggestionItem,
    AISuggestionsResult,
    AIUsageMeta,
    ChatHistoryItem,
    ConversationMessage,
    ConversationSummary,
    ProjectContext,
    ProjectContextTask,
    UiContext,
)
from app.service.contracts.assignment import AssignmentCreateInput, AssignmentPatchInput
from app.service.contracts.calendar import (
    CalendarCreateInput,
    CalendarExceptionCreateInput,
    CalendarExceptionPatchInput,
    CalendarPatchInput,
)
from app.service.contracts.comment import (
    CommentEntityContext,
    CommentItemData,
)
from app.service.contracts.dependency import DependencyCreateInput, DependencyPatchInput
from app.service.contracts.organization import (
    OrganizationCreateInput,
    OrganizationPatchInput,
)
from app.service.contracts.organization_member import (
    OrganizationMemberInviteInput,
    OrganizationMemberRolePatchInput,
)
from app.service.contracts.project_member import (
    ProjectInvitationAcceptInput,
    ProjectMemberInviteInput,
    ProjectMemberRolePatchInput,
    ProjectRoleName,
)
from app.service.contracts.realtime import (
    JsonValue,
    PresenceClientMessage,
    PresenceEntityType,
    PresenceStatus,
    RealtimeActor,
    RealtimeChannel,
    RealtimeEntityType,
    RealtimeErrorPayload,
    RealtimeEventPayload,
    SubscribeClientMessage,
)
from app.service.contracts.resource import ResourceCreateInput, ResourcePatchInput
from app.service.contracts.task_bulk import (
    TaskBulkUpdateInputItem,
    TaskBulkUpdatePatchInput,
    TaskCreateInput,
)

__all__ = [
    "AssignmentCreateInput",
    "AssignmentPatchInput",
    "ActivityChangesData",
    "ActivityEntityType",
    "ActivityLogItemData",
    "AIChatEvent",
    "AIChatInput",
    "AICompleteRequest",
    "ConversationMessage",
    "ConversationSummary",
    "AIEstimateInput",
    "AIEstimateItem",
    "AIEstimateResult",
    "AISuggestionAction",
    "AISuggestionItem",
    "AISuggestionsResult",
    "AIUsageMeta",
    "CalendarCreateInput",
    "CalendarExceptionCreateInput",
    "CalendarExceptionPatchInput",
    "CalendarPatchInput",
    "ChatHistoryItem",
    "CommentEntityContext",
    "CommentItemData",
    "DependencyCreateInput",
    "DependencyPatchInput",
    "JsonValue",
    "OrganizationCreateInput",
    "OrganizationMemberInviteInput",
    "OrganizationMemberRolePatchInput",
    "OrganizationPatchInput",
    "PresenceClientMessage",
    "PresenceEntityType",
    "PresenceStatus",
    "ProjectContext",
    "ProjectContextTask",
    "ProjectInvitationAcceptInput",
    "ProjectMemberInviteInput",
    "ProjectMemberRolePatchInput",
    "ProjectRoleName",
    "RealtimeActor",
    "RealtimeChannel",
    "RealtimeEntityType",
    "RealtimeErrorPayload",
    "RealtimeEventPayload",
    "ResourceCreateInput",
    "ResourcePatchInput",
    "SubscribeClientMessage",
    "TaskBulkUpdateInputItem",
    "TaskBulkUpdatePatchInput",
    "TaskCreateInput",
    "UiContext",
]
