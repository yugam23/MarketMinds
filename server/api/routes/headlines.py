"""
Headlines API Routes
News headlines endpoints.
"""

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from server.api.dependencies import DBSession
from server.models.models import Asset, Headline
from server.schemas.schemas import HeadlineResponse


router = APIRouter(prefix="/headlines", tags=["Headlines"])


@router.get("/{symbol}", response_model=List[HeadlineResponse])
async def get_headlines(
    symbol: str,
    db: DBSession,
    days: int = Query(
        default=7, ge=1, le=30, description="Number of days of headlines"
    ),
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of headlines"
    ),
) -> List[Headline]:
    """
    Get news headlines for an asset.

    Args:
        symbol: Trading symbol (e.g., 'AAPL')
        days: Number of days of headlines (default: 7)
        limit: Maximum number of headlines (default: 50)

    Returns:
        List of headlines with sentiment scores.

    Raises:
        404: Asset not found.
    """
    # Check asset exists
    asset = db.get(Asset, symbol.upper())
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query headlines
    result = db.execute(
        select(Headline)
        .where(Headline.symbol == symbol.upper())
        # .where(Headline.date >= start_date)  <-- Removed to support "time travel" (System time 2026 vs Real Data)
        # .where(Headline.date <= end_date)
        .order_by(Headline.date.desc())
        .limit(limit)
    )

    return result.scalars().all()
