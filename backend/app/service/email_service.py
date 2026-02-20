"""
Email service for sending transactional emails.

Uses fastapi-mail with SMTP (Gmail or any provider).
"""

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_token
from app.models.email_verification import EmailVerification
from app.models.user import User

logger = logging.getLogger(__name__)

# Lazy-initialized FastMail client
_fm: FastMail | None = None


def _get_mail_client() -> FastMail:
    """Get or create the FastMail client (lazy singleton)."""
    global _fm
    if _fm is None:
        _fm = FastMail(
            ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_SERVER,
                MAIL_STARTTLS=settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=True,
            )
        )
    return _fm


async def send_verification_email(
    db: AsyncSession, user_id: uuid.UUID, email: str
) -> None:
    """
    Generate a verification token, save its hash, and send the email.
    """
    # Invalidate any existing unused tokens for this user
    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.user_id == user_id,
            EmailVerification.used_at.is_(None),
        )
    )
    for old_token in result.scalars().all():
        await db.delete(old_token)

    # Generate token
    token = secrets.token_urlsafe(32)

    # Save hashed token to database
    verification = EmailVerification(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(verification)
    await db.commit()

    # Build verification link — points to the backend API GET endpoint.
    # The backend verifies the token and redirects to the frontend.
    verify_url = f"{settings.BACKEND_URL}/api/v1/auth/verify-email?token={token}"

    # Send email
    html = f"""
    <h2>Verify your email address</h2>
    <p>Welcome to Sophikon! Click the link below to verify your email:</p>
    <p><a href="{verify_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background-color: #2563eb;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 600;
    ">Verify Email</a></p>
    <p>Or copy this link: {verify_url}</p>
    <p>This link expires in 24 hours.</p>
    <p>If you didn't create an account, you can ignore this email.</p>
    """

    message = MessageSchema(
        subject="Verify your email - Sophikon",
        recipients=[NameEmail(name="", email=email)],
        body=html,
        subtype=MessageType.html,
    )

    await _get_mail_client().send_message(message)


async def verify_email_token(db: AsyncSession, token: str) -> None:
    """
    Validate a verification token and mark the user's email as verified.

    Raises HTTPException if token is invalid, expired, or already used.
    """
    token_hash = hash_token(token)

    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.token_hash == token_hash,
            EmailVerification.used_at.is_(None),
        )
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if verification.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Mark token as used
    verification.used_at = datetime.now(UTC)

    # Mark user's email as verified
    user_result = await db.execute(select(User).where(User.id == verification.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user.email_verified = True
    await db.commit()
