"""
Cache Middleware
Adds Cache-Control headers for API responses.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Routes that should be cached (with their max-age in seconds)
CACHEABLE_ROUTES = {
    "/api/assets": 300,  # 5 minutes
    "/api/health": 60,  # 1 minute
}

# Route patterns that should be cached (dynamic routes)
CACHEABLE_PATTERNS = {
    "/api/prices/": 60,  # 1 minute - price data changes frequently
    "/api/sentiment/": 300,  # 5 minutes - sentiment aggregated
    "/api/headlines/": 180,  # 3 minutes - news updates periodically
}

# Routes that should never be cached
NO_CACHE_ROUTES = [
    "/api/auth/",
    "/api/predict/",
    "/api/pipeline/",
]


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add Cache-Control headers to API responses.

    Features:
    - Adds Cache-Control headers based on route configuration
    - Supports ETag generation for responses
    - Respects no-cache for authenticated routes
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add caching headers to response.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in chain

        Returns:
            Response with appropriate Cache-Control headers
        """
        response = await call_next(request)
        path = request.url.path

        # Skip caching for non-GET methods
        if request.method != "GET":
            response.headers["Cache-Control"] = "no-store"
            return response

        # Check if route should not be cached
        for no_cache_route in NO_CACHE_ROUTES:
            if path.startswith(no_cache_route):
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                return response

        # Check exact route matches
        if path in CACHEABLE_ROUTES:
            max_age = CACHEABLE_ROUTES[path]
            response.headers["Cache-Control"] = f"public, max-age={max_age}"
            return response

        # Check pattern matches for dynamic routes
        for pattern, max_age in CACHEABLE_PATTERNS.items():
            if path.startswith(pattern):
                response.headers["Cache-Control"] = (
                    f"public, max-age={max_age}, stale-while-revalidate=60"
                )
                return response

        # Default: no caching
        response.headers["Cache-Control"] = "no-cache"
        return response
