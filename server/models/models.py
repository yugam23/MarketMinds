"""
MarketMinds ORM Models
SQLAlchemy models for assets, prices, headlines, sentiment, and predictions.
Uses modern SQLAlchemy 2.0 style with DeclarativeBase and Mapped types.
"""

from datetime import date as date_type, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    Date,
    DateTime,
    Numeric,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Asset(Base):
    """
    Tracked financial asset (stock or cryptocurrency).

    Attributes:
        symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD')
        name: Full name of the asset
        asset_type: 'stock' or 'crypto'
    """

    __tablename__ = "assets"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    asset_type: Mapped[str] = mapped_column(String(20))

    # Relationships
    prices: Mapped[List["Price"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    headlines: Mapped[List["Headline"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    daily_sentiments: Mapped[List["DailySentiment"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Asset(symbol={self.symbol!r}, name={self.name!r})"


class Price(Base):
    """
    OHLCV price data for an asset.

    Attributes:
        symbol: Foreign key to Asset
        date: Trading date
        open, high, low, close: Price data
        volume: Trading volume
    """

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_price_symbol_date"),
        Index("idx_prices_symbol_date", "symbol", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), ForeignKey("assets.symbol"))
    date: Mapped[date_type] = mapped_column(Date)
    open: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    high: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    low: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    close: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="prices")

    def __repr__(self) -> str:
        return f"Price(symbol={self.symbol!r}, date={self.date}, close={self.close})"


class Headline(Base):
    """
    News headline with sentiment score.

    Attributes:
        symbol: Foreign key to Asset
        date: Publication date
        title: Headline text
        source: News source
        url: Article URL
        sentiment_score: FinBERT score [-1, 1]
    """

    __tablename__ = "headlines"
    __table_args__ = (Index("idx_headlines_symbol_date", "symbol", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), ForeignKey("assets.symbol"))
    date: Mapped[date_type] = mapped_column(Date)
    title: Mapped[str] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="headlines")

    def __repr__(self) -> str:
        return f"Headline(symbol={self.symbol!r}, title={self.title[:30]!r}...)"


class DailySentiment(Base):
    """
    Aggregated daily sentiment for an asset.

    Attributes:
        symbol: Foreign key to Asset
        date: Aggregation date
        avg_sentiment: Average sentiment score
        headline_count: Number of headlines analyzed
        top_headline: Most impactful headline
    """

    __tablename__ = "daily_sentiment"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_sentiment_symbol_date"),
        Index("idx_daily_sentiment_symbol_date", "symbol", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), ForeignKey("assets.symbol"))
    date: Mapped[date_type] = mapped_column(Date)
    avg_sentiment: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    headline_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    top_headline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="daily_sentiments")

    def __repr__(self) -> str:
        return f"DailySentiment(symbol={self.symbol!r}, date={self.date}, avg={self.avg_sentiment})"


class Prediction(Base):
    """
    ML model prediction record.

    Attributes:
        symbol: Foreign key to Asset
        prediction_date: Date the prediction is for
        predicted_price: Model's predicted price
        actual_price: Actual price (filled after)
        model_version: Version tag for the model
        confidence: Model confidence score
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), ForeignKey("assets.symbol"))
    prediction_date: Mapped[date_type] = mapped_column(Date)
    predicted_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    actual_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    model_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="predictions")

    def __repr__(self) -> str:
        return f"Prediction(symbol={self.symbol!r}, date={self.prediction_date}, predicted={self.predicted_price})"
