"""
Rate Limiting Configuration
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from server.core.config import settings

# Initialize limiter
# slowapi limiter expects storage_uri for external storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url if settings.redis_url else "memory://",
)

# Limits
# Limits
RATE_LIMIT_GLOBAL = "100/minute"
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_READ = "100/minute"  # For high-traffic GET endpoints
RATE_LIMIT_WRITE = "20/minute"  # For POST/PUT/DELETE
RATE_LIMIT_PREDICT = "10/minute"  # For expensive inference
RATE_LIMIT_TRAIN = "3/hour"  # For heavy training jobs
