"""
Prices API Routes
OHLCV price data endpoints.
"""

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from server.api.dependencies import DBSession
from server.models.models import Asset, Price
from server.schemas.schemas import PriceResponse, PriceListResponse
from server.core.sanitization import validate_symbol


router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("/{symbol}", response_model=PriceListResponse)
async def get_prices(
    symbol: str,
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of data"),
) -> PriceListResponse:
    """
    Get OHLCV price data for an asset.

    Args:
        symbol: Trading symbol (e.g., 'AAPL')
        days: Number of days of historical data (default: 30)

    Returns:
        Price data with OHLCV values.

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

    # Query prices
    result = db.execute(
        select(Price)
        .where(Price.symbol == symbol.upper())
        .where(Price.date >= start_date)
        .where(Price.date <= end_date)
        .order_by(Price.date.asc())
    )
    prices = result.scalars().all()

    return PriceListResponse(symbol=symbol.upper(), data=prices, count=len(prices))


@router.get("/{symbol}/latest", response_model=PriceResponse)
async def get_latest_price(symbol: str, db: DBSession) -> Price:
    """
    Get the most recent price for an asset.

    Args:
        symbol: Trading symbol.

    Returns:
        Latest price data.

    Raises:
        404: No price data found.
    """
    symbol = validate_symbol(symbol)

    result = db.execute(
        select(Price).where(Price.symbol == symbol).order_by(Price.date.desc()).limit(1)
    )
    price = result.scalar_one_or_none()

    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}",
        )

    return price
