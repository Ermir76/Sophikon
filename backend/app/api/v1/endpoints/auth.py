"""
Authentication endpoints: register, login, refresh, logout, me, email verification.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.core.auth_flow import (
    PASSWORD_RESET_REQUEST_GENERIC_MESSAGE,
    build_frontend_url,
    create_oauth_state,
    decode_oauth_state,
    validate_oauth_state,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    InvalidOperationError,
)
from app.core.rate_limit import limiter
from app.models.user import User
from app.schema.auth import (
    AuthResponse,
    ChangePasswordRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    ResendVerificationEmailRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.service import auth_service, email_service
from app.tasks.notification_tasks import schedule_verification_reminder_emails

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
GOOGLE_OAUTH_STATE_COOKIE_NAME = "oauth_google_state"
VERIFICATION_EMAIL_GENERIC_MESSAGE = (
    "If the email exists, a verification email was sent."
)


def _client_info(request: Request) -> tuple[str | None, str | None]:
    device_info = request.headers.get("User-Agent")
    ip = request.client.host if request.client else None
    return device_info, ip


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    is_persistent: bool,
) -> None:
    access_max_age = (
        settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 if is_persistent else None
    )
    refresh_max_age = (
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 if is_persistent else None
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        path="/api",
        max_age=access_max_age,
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        path="/api/v1/auth",
        max_age=refresh_max_age,
    )


def _oauth_error_redirect() -> RedirectResponse:
    response = RedirectResponse(
        url=build_frontend_url("/login", params={"oauth": "error"}),
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie(
        GOOGLE_OAUTH_STATE_COOKIE_NAME,
        path="/api/v1/auth/oauth/google/callback",
    )
    return response


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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.register_user(
        db, body.email, body.password, body.full_name, device_info, ip
    )
    _set_auth_cookies(
        response,
        access_token=access,
        refresh_token=refresh,
        is_persistent=True,
    )

    # Send verification email (don't fail registration if email fails)
    try:
        await email_service.send_verification_email(db, user.id, user.email)
        schedule_verification_reminder_emails(user_id=str(user.id))
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    device_info, ip = _client_info(request)
    user, access, refresh = await auth_service.login_user(
        db,
        body.email,
        body.password,
        device_info,
        ip,
        remember_me=body.remember_me,
    )
    _set_auth_cookies(
        response,
        access_token=access,
        refresh_token=refresh,
        is_persistent=body.remember_me,
    )

    return AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )


@router.get("/oauth/google")
@limiter.limit("20/minute")
async def oauth_google_start(
    request: Request,
    next: str | None = None,
):
    state_token = create_oauth_state(next_path=next)
    authorize_url = auth_service.build_google_oauth_authorize_url(state_token)

    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=GOOGLE_OAUTH_STATE_COOKIE_NAME,
        value=state_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        path="/api/v1/auth/oauth/google/callback",
        max_age=10 * 60,
    )
    return response


@router.get("/oauth/google/callback")
@limiter.limit("30/minute")
async def oauth_google_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error or not code or not state:
        return _oauth_error_redirect()

    state_cookie = request.cookies.get(GOOGLE_OAUTH_STATE_COOKIE_NAME)
    if state_cookie is None or not validate_oauth_state(state_cookie, state):
        return _oauth_error_redirect()

    try:
        decoded_state = decode_oauth_state(state_cookie)
    except Exception:
        return _oauth_error_redirect()

    try:
        device_info, ip = _client_info(request)
        _, access, refresh = await auth_service.login_with_google_code(
            db,
            code=code,
            device_info=device_info,
            ip=ip,
        )
    except AppException:
        logger.warning("Google OAuth callback failed", exc_info=True)
        return _oauth_error_redirect()
    except Exception:
        logger.exception("Unexpected Google OAuth callback failure")
        return _oauth_error_redirect()

    next_path = decoded_state.get("next")
    redirect_path = next_path if isinstance(next_path, str) else "/"
    response = RedirectResponse(
        url=build_frontend_url(redirect_path),
        status_code=status.HTTP_302_FOUND,
    )
    _set_auth_cookies(
        response,
        access_token=access,
        refresh_token=refresh,
        is_persistent=True,
    )
    response.delete_cookie(
        GOOGLE_OAUTH_STATE_COOKIE_NAME,
        path="/api/v1/auth/oauth/google/callback",
    )
    return response


@router.post("/password-reset", response_model=MessageResponse)
@limiter.limit("5/hour")
async def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.request_password_reset(db, body.email)
    return MessageResponse(message=PASSWORD_RESET_REQUEST_GENERIC_MESSAGE)


@router.post("/password-reset/confirm", response_model=MessageResponse)
@limiter.limit("20/hour")
async def confirm_password_reset(
    body: PasswordResetConfirmRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.confirm_password_reset(
        db,
        token=body.token,
        new_password=body.new_password,
    )
    return MessageResponse(message="Password has been reset")


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("20/hour")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    await auth_service.change_password(
        db,
        user=user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return MessageResponse(message="Password has been changed")


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise AuthenticationError("No refresh token found")

    device_info, ip = _client_info(request)
    user, access, new_refresh, is_persistent = await auth_service.refresh_tokens(
        db, refresh_token, device_info, ip
    )
    _set_auth_cookies(
        response,
        access_token=access,
        refresh_token=new_refresh,
        is_persistent=is_persistent,
    )

    return AuthResponse(
        tokens=TokenResponse(access_token="", refresh_token=""),
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        await auth_service.logout_user(db, refresh_token)

    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME, path="/api")
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME, path="/api/v1/auth")
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_active_user)]):
    return UserResponse.model_validate(user)


@router.get("/verify-email")
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    GET endpoint called directly from the email link.
    Verifies the token and redirects the browser to the frontend
    with ?status=success or ?status=error.
    """
    frontend_url = settings.FRONTEND_URL

    try:
        await email_service.verify_email_token(db, token)
        return RedirectResponse(
            url=f"{frontend_url}/verify-email?status=success",
            status_code=status.HTTP_302_FOUND,
        )
    except AppException:
        return RedirectResponse(
            url=f"{frontend_url}/verify-email?status=error",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/send-verification-email", response_model=MessageResponse)
@limiter.limit("3/hour")
async def resend_verification_email(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    if user.email_verified:
        raise InvalidOperationError("Email is already verified")

    await email_service.send_verification_email(db, user.id, user.email)
    return MessageResponse(message="Verification email sent")


@router.post("/resend-verification-email", response_model=MessageResponse)
@limiter.limit("5/hour")
async def resend_verification_email_public(
    body: ResendVerificationEmailRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.request_verification_email(db, body.email)
    return MessageResponse(message=VERIFICATION_EMAIL_GENERIC_MESSAGE)
