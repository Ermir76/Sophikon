"""
Authentication endpoints: register, login, refresh, logout, me.
"""

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schema.auth import (
    AuthResponse,
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.service import auth_service
from app.core.config import settings

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
    response = AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),  # Empty in body
        user=UserResponse.model_validate(user),
    )

    # Set cookies
    request.response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    request.response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return response


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
    response = AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )

    request.response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    request.response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return response


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        # Fallback to body for backward compatibility or testing if needed,
        # otherwise raise 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found",
        )

    device_info, ip = _client_info(request)
    user, access, new_refresh = await auth_service.refresh_tokens(
        db, refresh_token, device_info, ip
    )

    response = AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )

    request.response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    request.response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=new_refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        await auth_service.logout_user(db, refresh_token)

    response = MessageResponse(message="Logged out successfully")
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME)
    return response


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(user)
