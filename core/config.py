"""Application configuration from environment."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Settings loaded from environment."""

    # App
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ruki",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ruki",
        alias="DATABASE_URL_SYNC",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Bot
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")

    # Encryption (Fernet key, base64)
    encryption_key: str = Field(default="", alias="ENCRYPTION_KEY")

    # JWT (for admin API)
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24, alias="JWT_EXPIRE_MINUTES")

    # Sentry
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

    # CORS (comma-separated origins for admin panel)
    cors_origins: str = Field(default="http://localhost:8000", alias="CORS_ORIGINS")

    # Rate limits (per user)
    rate_limit_create_task_per_hour: int = Field(default=5, alias="RATE_LIMIT_CREATE_TASK_PER_HOUR")
    rate_limit_create_bid_per_hour: int = Field(default=20, alias="RATE_LIMIT_CREATE_BID_PER_HOUR")
    rate_limit_send_message_per_minute: int = Field(default=30, alias="RATE_LIMIT_SEND_MESSAGE_PER_MINUTE")
    rate_limit_verification_per_day: int = Field(default=3, alias="RATE_LIMIT_VERIFICATION_PER_DAY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
