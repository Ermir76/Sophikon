# Tools to load settings from environment variables
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# All settings for the app live here
# These values come from the .env file or from system environment variables
class Settings(BaseSettings):
    # App
    APP_NAME: str = "Sophikon"
    VERSION: str = "1.0.0"
    ENV: str = "development"  # "development" or "production"
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "change-me-set-your-database-url"

    # Security
    SECRET_KEY: str = "change-me-generate-a-real-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://app.sophikon.org",
    ]

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting (disabled in development by default)
    RATE_LIMIT_ENABLED: bool = True

    # Email (SMTP)
    MAIL_SERVER: str = ""  # Required - must be in .env
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""  # Required - must be in .env
    MAIL_PASSWORD: str = ""  # Required - must be in .env
    MAIL_FROM: str = ""  # Required - must be in .env
    MAIL_FROM_NAME: str = "Sophikon"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # AI (optional for now)
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Tell pydantic to read values from a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_required_secrets(self):
        if not self.SECRET_KEY or self.SECRET_KEY == "change-me-generate-a-real-key":
            raise ValueError(
                "SECRET_KEY must be set to a secure random value. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if (
            not self.DATABASE_URL
            or self.DATABASE_URL == "change-me-set-your-database-url"
        ):
            raise ValueError("DATABASE_URL must be set in .env or environment")
        return self


# Create one settings object that the whole app can use
settings = Settings()
