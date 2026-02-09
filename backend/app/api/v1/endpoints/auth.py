"""
Authentication endpoints: register, login, refresh, logout, me.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schema.auth import (
    AuthResponse,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_info(request: Request) -> tuple[str | None, str | None]:
    device_info = request.headers.get("User-Agent")
    ip = request.client.host if request.client else None
    return device_info, ip


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.register_user(
        db, body.email, body.password, body.full_name, device_info, ip
    )
    return AuthResponse(
        tokens=TokenResponse(access_token=access, refresh_token=refresh),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.login_user(
        db, body.email, body.password, device_info, ip
    )
    return AuthResponse(
        tokens=TokenResponse(access_token=access, refresh_token=refresh),
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    body: TokenRefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    device_info, ip = _client_info(request)
    user, access, new_refresh = await auth_service.refresh_tokens(
        db, body.refresh_token, device_info, ip
    )
    return AuthResponse(
        tokens=TokenResponse(access_token=access, refresh_token=new_refresh),
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout_user(db, body.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(user)
