"""
Pydantic v2 schemas for authentication endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Requests ──


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ── Responses ──


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None
    is_active: bool
    email_verified: bool
    timezone: str
    locale: str
    created_at: datetime


class AuthResponse(BaseModel):
    tokens: TokenResponse
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
