"""
Headlines API Routes
News headlines endpoints.
"""

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from server.api.dependencies import DBSession
from server.models.models import Asset, Headline
from server.schemas.schemas import HeadlineResponse
from server.core.sanitization import validate_symbol


router = APIRouter(prefix="/headlines", tags=["Headlines"])


@router.get("/{symbol}")
async def get_headlines(
    symbol: str,
    db: DBSession,
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days of headlines"
    ),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of headlines"
    ),
) -> dict:
    """
    Get news headlines for an asset with pagination.

    Args:
        symbol: Trading symbol (e.g., 'AAPL')
        days: Number of days of headlines (default: 7)
        offset: Pagination offset (default: 0)
        limit: Maximum number of headlines (default: 50)

    Returns:
        Dictionary with data and pagination metadata.

    Raises:
        404: Asset not found.
    """
    # Sanitize symbol
    symbol = validate_symbol(symbol)

    # Check asset exists
    asset = db.get(Asset, symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query total count for pagination metadata
    from sqlalchemy import func

    total_count = db.scalar(
        select(func.count()).select_from(Headline).where(Headline.symbol == symbol)
    )

    # Query headlines
    result = db.execute(
        select(Headline)
        .where(Headline.symbol == symbol)
        # .where(Headline.date >= start_date)  <-- Removed to support "time travel" (System time 2026 vs Real Data)
        # .where(Headline.date <= end_date)
        .order_by(Headline.date.desc())
        .offset(offset)
        .limit(limit)
    )

    headlines = result.scalars().all()

    # Convert to Pydantic models explicitly since we are returning a dict
    data = [HeadlineResponse.model_validate(h) for h in headlines]

    return {
        "data": data,
        "pagination": {
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "days": days,
        },
    }
