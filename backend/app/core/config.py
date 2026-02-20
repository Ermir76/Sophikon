# Tools to load settings from environment variables
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
    DATABASE_URL: str = ""  # Required - must be in .env

    # Security
    SECRET_KEY: str = ""  # Required - must be in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://app.sophikon.eu",
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


# Create one settings object that the whole app can use
settings = Settings()
