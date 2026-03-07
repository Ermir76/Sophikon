"""
AI endpoints.

POST /projects/{project_id}/ai/chat         - Stream AI chat responses
POST /projects/{project_id}/ai/estimate     - Generate AI task estimates
GET  /projects/{project_id}/ai/suggestions  - Get AI project suggestions
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    ProjectAccess,
    check_role,
    get_current_active_user,
    get_project_or_404,
)
from app.core.database import get_db
from app.models.user import User
from app.schema.ai import (
    AIChatRequest,
    AIEstimateRequest,
    AIEstimateResponse,
    AISuggestionsResponse,
)
from app.service import ai_service

router = APIRouter(prefix="/projects/{project_id}/ai", tags=["ai"])


@router.post("/chat")
async def chat_with_ai(
    body: AIChatRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member", "viewer")
    stream = await ai_service.prepare_chat_stream(
        db,
        project=access.project,
        user_id=user.id,
        body=body,
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


@router.post("/estimate", response_model=AIEstimateResponse)
async def estimate_with_ai(
    body: AIEstimateRequest,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member")
    return await ai_service.estimate_for_project(
        db,
        project=access.project,
        user_id=user.id,
        body=body,
    )


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
