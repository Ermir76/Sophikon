"""
User profile endpoints.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from app.api.deps.auth import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ValidationError
from app.core.rate_limit import limiter
from app.core.storage import (
    build_media_url,
    ensure_media_directories,
    get_avatar_directory,
    get_media_relative_path_from_url,
    get_media_root,
)
from app.models.user import User
from app.schema.auth import (
    AIPreferencesRequest,
    AIPreferencesResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.service import ai_service, auth_service

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def _safe_media_path(relative_path: Path) -> Path | None:
    """
    Resolve media-relative path and ensure it stays within media root.
    """
    media_root = get_media_root().resolve()
    candidate = (media_root / relative_path).resolve()
    try:
        candidate.relative_to(media_root)
    except ValueError:
        return None
    return candidate


def _delete_local_avatar_if_managed(avatar_url: str | None) -> None:
    """
    Delete existing avatar file when it is managed by local media storage.
    """
    relative_path = get_media_relative_path_from_url(avatar_url)
    if relative_path is None:
        return
    absolute_path = _safe_media_path(relative_path)
    if absolute_path is None:
        return
    if absolute_path.exists():
        absolute_path.unlink(missing_ok=True)


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


@router.post("/me/avatar", response_model=UserResponse)
@limiter.limit("30/minute")
async def upload_avatar(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...),
):
    extension = ALLOWED_AVATAR_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise ValidationError("Avatar must be PNG, JPEG, or WEBP")

    max_bytes = settings.MAX_AVATAR_UPLOAD_BYTES
    file_bytes = await file.read(max_bytes + 1)
    await file.close()

    if not file_bytes:
        raise ValidationError("Avatar file cannot be empty")
    if len(file_bytes) > max_bytes:
        raise ValidationError("Avatar file must be 2MB or smaller")

    ensure_media_directories()
    avatar_dir = get_avatar_directory()
    filename = f"{user.id}_{uuid7()}{extension}"
    avatar_path = avatar_dir / filename
    avatar_path.write_bytes(file_bytes)

    _delete_local_avatar_if_managed(user.avatar_url)
    relative_path = avatar_path.relative_to(get_media_root())
    avatar_url = build_media_url(relative_path)

    updated = await auth_service.update_user_profile(
        db,
        user=user,
        patch={"avatar_url": avatar_url},
    )
    return UserResponse.model_validate(updated)


@router.get("/me/ai-preferences", response_model=AIPreferencesResponse)
async def get_ai_preferences(
    user: Annotated[User, Depends(get_current_active_user)],
):
    prefs = (user.preferences or {}).get("ai", {})
    merged = {**ai_service._DEFAULT_AUTO_APPROVE, **prefs.get("auto_approve", {})}
    return AIPreferencesResponse(auto_approve=merged)


@router.patch("/me/ai-preferences", response_model=AIPreferencesResponse)
async def update_ai_preferences(
    body: AIPreferencesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    current = dict(user.preferences or {})
    current_ai = dict(current.get("ai", {}))
    current_auto = dict(current_ai.get("auto_approve", {}))
    current_auto.update(body.auto_approve)
    current_ai["auto_approve"] = current_auto
    current["ai"] = current_ai
    user.preferences = current
    await db.commit()
    merged = {**ai_service._DEFAULT_AUTO_APPROVE, **current_auto}
    return AIPreferencesResponse(auto_approve=merged)


@router.delete("/me/avatar", response_model=UserResponse)
@limiter.limit("30/minute")
async def delete_avatar(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    _delete_local_avatar_if_managed(user.avatar_url)
    updated = await auth_service.update_user_profile(
        db,
        user=user,
        patch={"avatar_url": None},
    )
    return UserResponse.model_validate(updated)
