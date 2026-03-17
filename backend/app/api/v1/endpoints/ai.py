"""
AI endpoints.

POST /projects/{project_id}/ai/chat                              - Stream AI chat (agentic loop)
POST /projects/{project_id}/ai/approvals/{approval_id}           - Resolve a pending tool approval
POST /projects/{project_id}/ai/plan-approval/{conversation_id}   - Approve or redirect agent plan
GET  /projects/{project_id}/ai/conversations                     - List past conversations
GET  /projects/{project_id}/ai/conversations/{conversation_id}   - Load conversation history
POST /projects/{project_id}/ai/estimate                          - Generate AI task estimates
GET  /projects/{project_id}/ai/suggestions                       - Get AI project suggestions
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.project import (
    ProjectAccess,
    check_role,
    get_project_or_404,
)
from app.core.database import get_db
from app.models.user import User
from app.schema.ai import (
    AIApprovalRequest,
    AIChatRequest,
    AIEstimateRequest,
    AIEstimateResponse,
    AIPlanApprovalRequest,
    AISuggestionsResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummaryResponse,
    MessageResponse,
)
from app.service import ai_service
from app.service.agent import executor
from app.service.contracts.ai import AIChatInput, AIEstimateInput

router = APIRouter(prefix="/projects/{project_id}/ai", tags=["ai"])


def _to_chat_input(body: AIChatRequest) -> AIChatInput:
    return AIChatInput.model_validate(body.model_dump(mode="python"))


def _to_estimate_input(body: AIEstimateRequest) -> AIEstimateInput:
    return AIEstimateInput.model_construct(**body.model_dump(mode="python"))


@router.post("/chat")
async def chat_with_ai(
    body: AIChatRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member", "viewer")
    service_body = _to_chat_input(body)
    stream = await ai_service.prepare_chat_stream(
        db,
        project=access.project,
        user=user,
        body=service_body,
    )

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/approvals/{approval_id}", status_code=200)
async def resolve_approval(
    approval_id: str,
    body: AIApprovalRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    check_role(access, "owner", "manager", "member")
    await executor.resolve_tool_approval(approval_id, body.approved)
    return {"ok": True}


@router.post("/plan-approval/{conversation_id}", status_code=200)
async def resolve_plan_approval(
    conversation_id: UUID,
    body: AIPlanApprovalRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    check_role(access, "owner", "manager", "member")
    from app.service.agent.loop import resolve_plan_approval

    await resolve_plan_approval(
        str(conversation_id),
        approved=body.approved,
        feedback=body.feedback,
    )
    return {"ok": True}


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member", "viewer")
    conversations = await ai_service.list_conversations(
        db,
        project_id=access.project.id,
        user_id=user.id,
    )
    return ConversationListResponse(
        conversations=[
            ConversationSummaryResponse(
                id=c.id,
                title=c.title,
                status=c.status,
                mode=c.mode,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations  # c is ConversationSummary contract
        ]
    )


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationDetailResponse
)
async def get_conversation(
    conversation_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member", "viewer")
    conversation, messages = await ai_service.get_conversation_messages(
        db,
        conversation_id=conversation_id,
        project_id=access.project.id,
        user_id=user.id,
    )
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        mode=conversation.mode,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages  # m is ConversationMessage contract
        ],
    )


@router.post("/estimate", response_model=AIEstimateResponse)
async def estimate_with_ai(
    body: AIEstimateRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member")
    result = await ai_service.estimate_for_project(
        db,
        project=access.project,
        user_id=user.id,
        body=_to_estimate_input(body),
    )
    return result


@router.get("/suggestions", response_model=AISuggestionsResponse)
async def get_ai_suggestions(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    check_role(access, "owner", "manager", "member", "viewer")
    return await ai_service.suggestions_for_project(
        db,
        project=access.project,
        user_id=user.id,
        limit=limit,
    )
