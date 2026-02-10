"""
MarketMinds Configuration
Environment-based settings using Pydantic Settings.
"""

from functools import lru_cache
from typing import Any
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
    debug: bool = False  # Default to False for security
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "sqlite:///./marketminds.db"

    # API Keys
    news_api_key: str = ""

    # Redis (optional for dev)
    redis_url: str = ""

    # CORS
    # In production, this must be set via env var as comma-separated list
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from string."""
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

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
    # Default is ONLY for dev. usage. Production MUST set this env var.
    SECRET_KEY: str = "dev-secret-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Monitoring
    SENTRY_DSN: str = ""  # Optional: Set to enable Sentry error tracking

    def model_post_init(self, __context: Any) -> None:
        """Validate settings after initialization."""
        if self.environment.lower() == "production":
            # Enforce secure secret key in production
            if self.SECRET_KEY == "dev-secret-key-change-me":
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set to a secure value in production environment!"
                )

            # Warn if debug is on in production
            if self.debug:
                import logging

                logging.warning(
                    "SECURITY WARNING: Debug mode is enabled in production!"
                )

            # Enforce CORS configuration in production
            # We check if the value is still the default dev value
            default_cors = "http://localhost:3000,http://localhost:5173"
            if self.cors_origins_str == default_cors:
                raise ValueError(
                    "CRITICAL: CORS_ORIGINS must be explicitly set in production environment!"
                )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
