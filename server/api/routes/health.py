from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from server.core.database import get_db
from pydantic import BaseModel

router = APIRouter()


from server.core.config import settings
from fastapi import Response


class DetailedHealthResponse(BaseModel):
    status: str
    services: dict
    version: str


@router.get("/health", response_model=DetailedHealthResponse)
def health_check(response: Response, db: Session = Depends(get_db)):
    """
    Detailed health check for all dependent services.
    Returns 503 if any critical service is down.
    """
    services = {"database": "unknown", "redis": "disabled"}

    # 1. Check Database
    try:
        db.execute(text("SELECT 1"))
        services["database"] = "connected"
    except Exception as e:
        services["database"] = f"disconnected: {str(e)}"

    # 2. Check Redis (if enabled)
    if settings.redis_url:
        try:
            import redis

            r = redis.from_url(settings.redis_url)
            r.ping()
            services["redis"] = "connected"
        except ImportError:
            services["redis"] = "error: redis-py not installed"
        except Exception as e:
            services["redis"] = f"disconnected: {str(e)}"

    # Determine overall status
    is_healthy = services["database"] == "connected"

    # Redis logic:
    if settings.redis_url and services["redis"] != "connected":
        if settings.environment.lower() == "production":
            is_healthy = False
        # In dev, allow Redis failure (soft dependency for local dev)

    status_code = (
        status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    response.status_code = status_code

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "services": services,
        "version": settings.app_version,
    }
