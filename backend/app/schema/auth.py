"""
Pydantic v2 schemas for authentication endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]

# ── Requests ──


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    remember_me: bool = False


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ResendVerificationEmailRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)
    timezone: str | None = Field(default=None, max_length=50)
    locale: str | None = Field(default=None, max_length=10)


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
    preferences: dict[str, JsonValue]
    timezone: str
    locale: str
    created_at: datetime


class AuthResponse(BaseModel):
    tokens: TokenResponse
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class AIPreferencesRequest(BaseModel):
    auto_approve: dict[str, bool] = Field(default_factory=dict, max_length=32)
    provider: str | None = Field(default=None, max_length=32)
    model: str | None = Field(default=None, max_length=128)


class AIModelOption(BaseModel):
    model_id: str
    label: str
    recommended: bool = False


class AIProviderOption(BaseModel):
    provider_id: str
    display_name: str
    requires_env_key: str
    available: bool
    models: list[AIModelOption]


class AIModelDefaults(BaseModel):
    provider: str
    model: str
    mode: str


class AIPreferencesResponse(BaseModel):
    auto_approve: dict[str, bool]
    provider: str | None = None
    model: str | None = None
    providers: list[AIProviderOption] = Field(default_factory=list)
    defaults: AIModelDefaults | None = None
