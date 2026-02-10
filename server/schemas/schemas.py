"""
MarketMinds Pydantic Schemas
Request/Response schemas for API validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# --- Asset Schemas ---
class AssetBase(BaseModel):
    """Base schema for Asset."""

    symbol: str
    name: str
    asset_type: str


class AssetCreate(AssetBase):
    """Schema for creating an asset."""

    pass


class AssetResponse(AssetBase):
    """Schema for asset response."""

    model_config = ConfigDict(from_attributes=True)


# --- Price Schemas ---
class PriceBase(BaseModel):
    """Base schema for Price."""

    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: Optional[int] = None


class PriceCreate(PriceBase):
    """Schema for creating price data."""

    symbol: str


class PriceResponse(PriceBase):
    """Schema for price response."""

    id: int
    symbol: str

    model_config = ConfigDict(from_attributes=True)


class PriceListResponse(BaseModel):
    """Schema for list of prices."""

    symbol: str
    data: List[PriceResponse]
    count: int


# --- Headline Schemas ---
class HeadlineBase(BaseModel):
    """Base schema for Headline."""

    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    sentiment_score: Optional[Decimal] = None


class HeadlineCreate(HeadlineBase):
    """Schema for creating headline."""

    symbol: str
    date: date


class HeadlineResponse(HeadlineBase):
    """Schema for headline response."""

    id: int
    symbol: str
    date: date

    model_config = ConfigDict(from_attributes=True)


# --- DailySentiment Schemas ---
class DailySentimentBase(BaseModel):
    """Base schema for DailySentiment."""

    date: date
    avg_sentiment: Optional[Decimal] = None
    headline_count: Optional[int] = None
    top_headline: Optional[str] = None


class DailySentimentResponse(DailySentimentBase):
    """Schema for daily sentiment response."""

    id: int
    symbol: str

    model_config = ConfigDict(from_attributes=True)


class SentimentListResponse(BaseModel):
    """Schema for list of sentiment data."""

    symbol: str
    data: List[DailySentimentResponse]
    count: int


# --- Prediction Schemas ---
class PredictionRequest(BaseModel):
    """Schema for prediction request."""

    symbol: str


class PredictionResponse(BaseModel):
    """Schema for prediction response."""

    symbol: str
    current_price: Decimal
    predicted_price: Decimal
    direction: str  # "up" or "down"
    change_percent: Decimal
    sentiment_contribution: Decimal
    prediction_date: date
    model_version: str


# --- Health Check ---
class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    db: str
    version: str
