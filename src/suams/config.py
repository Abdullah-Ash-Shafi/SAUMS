"""Application configuration settings loaded from environment variables."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    PROJECT_NAME: str = "SUAMS - Smart University Academic Management System"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SUAMS_SECRET_KEY", "default-insecure-secret-key-change-in-prod-ruet-3206")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = os.getenv("SUAMS_DATABASE_URL", "sqlite:///./suams.db")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings: Settings = Settings()
