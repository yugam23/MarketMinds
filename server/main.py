"""
MarketMinds FastAPI Application
Main entry point for the backend server.

Features:
- REST API for stock prices, sentiment, and predictions
- JWT authentication with refresh tokens
- Rate limiting and security headers
- GZip compression for responses
- Cache-Control headers for performance
- Prometheus metrics and Sentry error tracking
- ML model prewarming on startup
"""

import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Add project root to sys.path to allow running from server directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.config import settings
from server.core.database import init_db
from server.api.routes import (
    health,
    assets,
    prices,
    sentiment,
    headlines,
    predict,
    pipeline,
)

# Imports for Monitoring
from prometheus_fastapi_instrumentator import Instrumentator
from server.core.monitoring import setup_logging, setup_sentry

# Imports for Security & Limiter
from server.core.security_headers import SecurityHeadersMiddleware
from server.core.cache_middleware import CacheMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from server.core.limiter import limiter

# Import model prewarming
from server.core.model_prewarm import prewarm_all_models

# Setup monitoring
setup_logging()
setup_sentry()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
    - Initialize database
    - Prewarm ML models for faster first predictions

    Shutdown:
    - Cleanup resources
    """
    # === Startup ===
    logger.info("Starting MarketMinds API...")

    # Initialize database
    init_db()
    logger.info("✓ Database initialized")

    # Prewarm ML models (runs in background, doesn't block startup)
    if not settings.debug:
        # Only prewarm in production mode to speed up dev restarts
        try:
            prewarm_all_models()
        except Exception as e:
            logger.warning(f"Model prewarming failed: {e}")

    logger.info("✓ MarketMinds API ready")

    yield

    # === Shutdown ===
    logger.info("Shutting down MarketMinds API...")
    # Add cleanup logic here if needed


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sentiment-augmented price prediction platform for stocks and cryptocurrencies.",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# === Middleware Stack ===
# Order matters: last added = first executed

# 1. Instrument Prometheus (should be first to capture all requests)
Instrumentator().instrument(app).expose(app)

# 2. GZip Compression (compress responses > 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 3. Cache-Control Headers
app.add_middleware(CacheMiddleware)

# 4. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 5. Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 6. CORS (should be near the end to allow other middleware to process first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Include Routers ===
app.include_router(health.router, tags=["Health"])
app.include_router(assets.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(headlines.router, prefix="/api")
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to MarketMinds API",
        "version": settings.app_version,
        "docs": "/api/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
