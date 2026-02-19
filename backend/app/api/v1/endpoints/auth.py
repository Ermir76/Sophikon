"""
Authentication endpoints: register, login, refresh, logout, me, email verification.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schema.auth import (
    AuthResponse,
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.service import auth_service, email_service

logger = logging.getLogger(__name__)

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
@limiter.limit("5/hour")
async def register(
    body: UserRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.register_user(
        db, body.email, body.password, body.full_name, device_info, ip
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Send verification email (don't fail registration if email fails)
    try:
        frontend_url = request.headers.get("Origin", "http://localhost:5173")
        await email_service.send_verification_email(
            db, user.id, user.email, frontend_url
        )
    except Exception:
        logger.warning("Failed to send verification email on register", exc_info=True)

    return AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    body: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.login_user(
        db, body.email, body.password, device_info, ip
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found",
        )

    device_info, ip = _client_info(request)
    user, access, new_refresh = await auth_service.refresh_tokens(
        db, refresh_token, device_info, ip
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=new_refresh,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        await auth_service.logout_user(db, refresh_token)

    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    await email_service.verify_email_token(db, token)
    return MessageResponse(message="Email verified successfully")


@router.post("/send-verification-email", response_model=MessageResponse)
@limiter.limit("3/hour")
async def resend_verification_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    frontend_url = request.headers.get("Origin", "http://localhost:5173")
    await email_service.send_verification_email(db, user.id, user.email, frontend_url)
    return MessageResponse(message="Verification email sent")
