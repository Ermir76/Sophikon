from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sophikon AI Service"
    VERSION: str = "0.1.0"
    ENV: str = "development"

    AI_MODE: str = "mock"
    AI_PROVIDER: str = "gemini"
    AI_MODEL_NAME: str = "sophikon-mock-v1"

    AI_SERVICE_SHARED_SECRET: str = "dev-ai-shared-secret"

    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
