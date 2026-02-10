"""
MarketMinds Custom Exceptions
Application-specific error classes for better error handling.
"""


class MarketMindsError(Exception):
    """Base exception for all MarketMinds errors."""

    pass


class ExternalAPIError(MarketMindsError):
    """Raised when an external API (yfinance, NewsAPI) fails."""

    def __init__(
        self, message: str, api_name: str = "Unknown", retry_after: int | None = None
    ):
        self.api_name = api_name
        self.retry_after = retry_after
        super().__init__(f"{api_name} API Error: {message}")


class RateLimitError(ExternalAPIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, api_name: str, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            api_name=api_name,
            retry_after=retry_after,
        )


class DataValidationError(MarketMindsError):
    """Raised when data validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(f"Validation Error: {message}")


class AssetNotFoundError(MarketMindsError):
    """Raised when a requested asset is not found."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Asset not found: {symbol}")


class ModelNotLoadedError(MarketMindsError):
    """Raised when ML model is not loaded or unavailable."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Model not loaded: {model_name}")
