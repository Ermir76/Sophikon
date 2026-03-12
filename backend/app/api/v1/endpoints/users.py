"""
User profile endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schema.auth import UpdateProfileRequest, UserResponse
from app.service import auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_me(
    body: UpdateProfileRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    patch = body.model_dump(mode="python", exclude_unset=True)
    updated = await auth_service.update_user_profile(db, user=user, patch=patch)
    return UserResponse.model_validate(updated)
