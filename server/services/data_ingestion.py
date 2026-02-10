"""
MarketMinds Data Ingestion Service
Fetches OHLC price data from yfinance and headlines from NewsAPI.

Architecture:
- OHLCIngester: Handles stock/crypto price data with retry logic
- HeadlineIngester: Fetches news with Redis caching
- Both use exponential backoff for resilience
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
from typing import Any

import pandas as pd
import yfinance as yf
from newsapi import NewsApiClient
from sqlalchemy.orm import Session

from server.core.config import settings
from server.core.exceptions import ExternalAPIError, RateLimitError
from server.models.models import Asset, Price, Headline

logger = logging.getLogger(__name__)


# =============================================================================
# OHLC Price Data Ingester (yfinance)
# =============================================================================


class OHLCIngester:
    """
    Fetches OHLC (Open-High-Low-Close) price data from yfinance.

    Features:
    - Rate limiting (configurable throttle)
    - Exponential backoff retry logic
    - Support for stocks and cryptocurrencies
    - Data validation before storage

    Example:
        ingester = OHLCIngester(throttle_seconds=1.0)
        df = await ingester.fetch_ohlc("AAPL", days=30)
    """

    MAX_RETRIES = 3

    def __init__(self, throttle_seconds: float = 1.0):
        """
        Initialize the OHLC ingester.

        Args:
            throttle_seconds: Delay between API calls to avoid rate limiting
        """
        self.throttle = throttle_seconds
        self.market_exchange = settings.market_exchange

    def _normalize_symbol(self, symbol: str) -> str:
        """Ensure symbol has correct suffix for Indian markets."""
        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            return symbol

        # Crypto handling (keep as is if it has -USD)
        if "-USD" in symbol:
            return symbol

        if self.market_exchange == "BSE":
            return f"{symbol}.BO"
        return f"{symbol}.NS"

    async def fetch_ohlc(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch OHLC data with retry logic.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD')
            days: Number of historical days to fetch

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume

        Raises:
            ExternalAPIError: If all retry attempts fail
        """
        end_date = datetime.now(ZoneInfo(settings.market_timezone))
        start_date = end_date - timedelta(days=days)

        # Normalize symbol for Indian markets
        query_symbol = self._normalize_symbol(symbol)

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Fetching OHLC for {query_symbol} (attempt {attempt + 1})")

                # yfinance is synchronous, run in executor
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(
                    None, self._fetch_sync, query_symbol, start_date, end_date
                )

                # Throttle to avoid rate limiting
                await asyncio.sleep(self.throttle)

                if df.empty:
                    raise ExternalAPIError(
                        message=f"No data returned for {query_symbol}",
                        api_name="yfinance",
                    )

                logger.info(f"Fetched {len(df)} rows for {query_symbol}")
                return df

            except ExternalAPIError:
                raise
            except Exception as e:
                logger.warning(f"yfinance attempt {attempt + 1} failed: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    raise ExternalAPIError(
                        message=f"Failed after {self.MAX_RETRIES} attempts: {e}",
                        api_name="yfinance",
                    )
                # Exponential backoff
                await asyncio.sleep(2**attempt)

        # Should not reach here, but satisfy type checker
        raise ExternalAPIError(message="Unexpected error", api_name="yfinance")

    def _fetch_sync(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Synchronous yfinance fetch (called in executor)."""
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        return df

    def store_ohlc(self, symbol: str, df: pd.DataFrame, db: Session) -> int:
        """
        Store OHLC data in database, updating existing records.

        Args:
            symbol: Asset symbol
            df: DataFrame with OHLC data
            db: Database session

        Returns:
            Number of records stored/updated
        """
        count = 0

        for index, row in df.iterrows():
            # index is DatetimeIndex
            date_val = index.date() if hasattr(index, "date") else index

            # Check if price record exists
            existing = (
                db.query(Price)
                .filter(Price.symbol == symbol, Price.date == date_val)
                .first()
            )

            if existing:
                # Update existing record
                existing.open = Decimal(str(row["Open"]))
                existing.high = Decimal(str(row["High"]))
                existing.low = Decimal(str(row["Low"]))
                existing.close = Decimal(str(row["Close"]))
                existing.volume = (
                    int(row["Volume"]) if pd.notna(row["Volume"]) else None
                )
            else:
                # Create new record
                price = Price(
                    symbol=symbol,
                    date=date_val,
                    open=Decimal(str(row["Open"])),
                    high=Decimal(str(row["High"])),
                    low=Decimal(str(row["Low"])),
                    close=Decimal(str(row["Close"])),
                    volume=int(row["Volume"]) if pd.notna(row["Volume"]) else None,
                )
                db.add(price)

            count += 1

        db.commit()
        logger.info(f"Stored {count} price records for {symbol}")
        return count


# =============================================================================
# News Headlines Ingester (NewsAPI)
# =============================================================================


class HeadlineIngester:
    """
    Fetches news headlines from NewsAPI with caching.

    Features:
    - Redis caching (24-hour TTL)
    - Rate limit awareness (100 req/day on free tier)
    - Relevancy-based search

    Example:
        ingester = HeadlineIngester(api_key="your-key", cache=redis_client)
        articles = await ingester.fetch_headlines("AAPL", days=7)
    """

    CACHE_TTL = 86400  # 24 hours in seconds

    def __init__(self, api_key: str, cache: Any | None = None):
        """
        Initialize the headline ingester.

        Args:
            api_key: NewsAPI API key
            cache: Redis client for caching (optional)
        """
        if not api_key:
            logger.warning("NewsAPI key not provided - headlines will be unavailable")
            self.client = None
        else:
            self.client = NewsApiClient(api_key=api_key)
        self.cache = cache

    async def fetch_headlines(
        self, symbol: str, days: int = 7, page_size: int = 50
    ) -> list[dict]:
        """
        Fetch headlines with caching.

        Args:
            symbol: Asset symbol to search for
            days: How many days back to search
            page_size: Maximum number of articles

        Returns:
            List of article dictionaries with title, source, url, publishedAt

        Raises:
            ExternalAPIError: If API call fails
            RateLimitError: If rate limit is exceeded
        """
        if not self.client:
            logger.warning("NewsAPI client not available")
            return []

        cache_key = f"headlines:{symbol}:{days}"

        # Check cache first
        if self.cache:
            try:
                cached = await self._get_cache(cache_key)
                if cached:
                    logger.info(f"Cache hit for {symbol} headlines")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")

        # Fetch from API
        try:
            logger.info(f"Fetching headlines for {symbol} from NewsAPI")

            # Build search query - search for company name variations
            # Extract base symbol for Indian stocks (RELIANCE.NS -> RELIANCE)
            base_symbol = symbol.replace(".NS", "").replace(".BO", "")

            # More specific query for Indian market
            query = f'"{base_symbol}" AND (stock OR market OR finance OR "price" OR NSE OR BSE OR India OR Nifty OR Sensex)'

            now = datetime.now(ZoneInfo(settings.market_timezone))
            from_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")

            # NewsAPI is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_everything(
                    q=query,
                    # from_param=from_date,  <-- Removed to avoid "future date" errors if system time is ahead
                    language="en",
                    sort_by="relevancy",
                    page_size=page_size,
                ),
            )

            articles = response.get("articles", [])
            logger.info(f"Fetched {len(articles)} headlines for {symbol}")

            # Cache the results
            if self.cache and articles:
                try:
                    await self._set_cache(cache_key, json.dumps(articles))
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

            return articles

        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg:
                raise RateLimitError(api_name="NewsAPI", retry_after=3600)
            raise ExternalAPIError(message=str(e), api_name="NewsAPI")

    def store_headlines(self, symbol: str, articles: list[dict], db: Session) -> int:
        """
        Store headlines in database.

        Args:
            symbol: Asset symbol
            articles: List of article dictionaries from NewsAPI
            db: Database session

        Returns:
            Number of headlines stored
        """
        count = 0

        for article in articles:
            title = article.get("title", "")
            if not title or title == "[Removed]":
                continue

            # Parse publication date
            published_at = article.get("publishedAt", "")
            try:
                pub_date = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                pub_date = datetime.now().date()

            # Check for duplicate (same title and date)
            existing = (
                db.query(Headline)
                .filter(
                    Headline.symbol == symbol,
                    Headline.title == title[:500],  # Truncate for comparison
                )
                .first()
            )

            if existing:
                continue

            headline = Headline(
                symbol=symbol,
                date=pub_date,
                title=title[:500],  # Truncate to fit schema
                source=article.get("source", {}).get("name", "Unknown")[:100],
                url=article.get("url", "")[:1000],
                sentiment_score=None,  # Will be filled by sentiment engine
            )
            db.add(headline)
            count += 1

        db.commit()
        logger.info(f"Stored {count} headlines for {symbol}")
        return count

    async def _get_cache(self, key: str) -> str | None:
        """Get value from Redis cache."""
        if hasattr(self.cache, "get"):
            # Async redis
            if asyncio.iscoroutinefunction(self.cache.get):
                return await self.cache.get(key)
            return self.cache.get(key)
        return None

    async def _set_cache(self, key: str, value: str) -> None:
        """Set value in Redis cache with TTL."""
        if hasattr(self.cache, "setex"):
            if asyncio.iscoroutinefunction(self.cache.setex):
                await self.cache.setex(key, self.CACHE_TTL, value)
            else:
                self.cache.setex(key, self.CACHE_TTL, value)


# =============================================================================
# Factory Functions for Easy Instantiation
# =============================================================================


def create_ohlc_ingester(throttle: float = 1.0) -> OHLCIngester:
    """Create an OHLC ingester with default settings."""
    return OHLCIngester(throttle_seconds=throttle)


def create_headline_ingester(cache: Any | None = None) -> HeadlineIngester:
    """Create a headline ingester using settings API key."""
    return HeadlineIngester(api_key=settings.news_api_key, cache=cache)
