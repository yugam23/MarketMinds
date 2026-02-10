"""
Assets API Routes
CRUD operations for tracked financial assets.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from server.api.dependencies import DBSession
from server.models.models import Asset
from server.schemas.schemas import AssetCreate, AssetResponse


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/", response_model=List[AssetResponse])
async def list_assets(db: DBSession) -> List[Asset]:
    """
    List all tracked assets.

    Returns:
        List of all assets with symbol, name, and type.
    """
    result = db.execute(select(Asset))
    return result.scalars().all()


@router.get("/{symbol}", response_model=AssetResponse)
async def get_asset(symbol: str, db: DBSession) -> Asset:
    """
    Get a specific asset by symbol.

    Args:
        symbol: Trading symbol (e.g., 'AAPL')

    Returns:
        Asset details.

    Raises:
        404: Asset not found.
    """
    asset = db.get(Asset, symbol.upper())
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )
    return asset


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(asset_data: AssetCreate, db: DBSession) -> Asset:
    """
    Create a new tracked asset.

    Args:
        asset_data: Asset creation data.

    Returns:
        Created asset.

    Raises:
        409: Asset already exists.
    """
    # Check if exists
    existing = db.get(Asset, asset_data.symbol.upper())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset {asset_data.symbol} already exists",
        )

    asset = Asset(
        symbol=asset_data.symbol.upper(),
        name=asset_data.name,
        asset_type=asset_data.asset_type,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(symbol: str, db: DBSession) -> None:
    """
    Delete a tracked asset.

    Args:
        symbol: Trading symbol.

    Raises:
        404: Asset not found.
    """
    asset = db.get(Asset, symbol.upper())
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )
    db.delete(asset)
    db.commit()
