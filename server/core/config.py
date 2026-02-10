"""
MarketMinds Configuration
Environment-based settings using Pydantic Settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MarketMinds"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./marketminds.db"

    # API Keys
    news_api_key: str = ""

    # Redis (optional for dev)
    redis_url: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ML Settings
    model_dir: str = "./models"

    # Market Settings
    market_exchange: str = "NSE"  # Options: NSE, BSE
    market_timezone: str = "Asia/Kolkata"
    market_open_hour: int = 9  # 9:15 AM
    market_close_hour: int = 15  # 3:30 PM
    currency_symbol: str = "₹"
    currency_code: str = "INR"

    # Security
    SECRET_KEY: str = "your-secret-key-please-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Monitoring
    SENTRY_DSN: str = ""  # Optional: Set to enable Sentry error tracking
    ENVIRONMENT: str = "development"  # development, staging, production


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
