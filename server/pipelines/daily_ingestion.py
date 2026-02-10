"""
MarketMinds Daily Ingestion Pipeline
Automated scheduler for daily data refresh.

Schedule: Daily at 5:00 PM EST (after market close)

Pipeline Steps:
1. Fetch OHLC data for all tracked assets
2. Fetch headlines for the same period
3. Store data in database
4. Trigger sentiment scoring (Phase 3)
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from server.core.database import SessionLocal
from server.core.config import settings
from server.models.models import Asset
from server.services.data_ingestion import (
    OHLCIngester,
    HeadlineIngester,
    create_ohlc_ingester,
    create_headline_ingester,
)

logger = logging.getLogger(__name__)


class DailyIngestionPipeline:
    """
    Orchestrates daily data ingestion for all tracked assets.

    This pipeline runs after market close to fetch:
    - Latest OHLC price data from yfinance
    - Recent news headlines from NewsAPI

    The pipeline is fault-tolerant and continues processing
    remaining assets even if one fails.

    Example:
        pipeline = DailyIngestionPipeline()
        await pipeline.run()  # Manual execution
        pipeline.schedule()   # Start scheduled execution
    """

    def __init__(
        self,
        ohlc_ingester: OHLCIngester | None = None,
        headline_ingester: HeadlineIngester | None = None,
        on_complete: Callable[[str, bool], Awaitable[None]] | None = None,
    ):
        """
        Initialize the pipeline.

        Args:
            ohlc_ingester: Custom OHLC ingester (uses default if None)
            headline_ingester: Custom headline ingester (uses default if None)
            on_complete: Callback function called after each asset
        """
        self.ohlc_ingester = ohlc_ingester or create_ohlc_ingester()
        self.headline_ingester = headline_ingester or create_headline_ingester()
        self.on_complete = on_complete
        self.scheduler: AsyncIOScheduler | None = None

        # Pipeline statistics
        self.stats = {
            "last_run": None,
            "total_assets": 0,
            "success_count": 0,
            "failure_count": 0,
            "price_records": 0,
            "headline_records": 0,
        }

    async def run(self, days: int = 30) -> dict:
        """
        Execute the daily pipeline for all tracked assets.

        Args:
            days: Number of historical days to fetch

        Returns:
            Dictionary with pipeline execution statistics
        """
        logger.info("=" * 60)
        logger.info("Starting Daily Ingestion Pipeline")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        # Reset stats
        self.stats = {
            "last_run": datetime.now().isoformat(),
            "total_assets": 0,
            "success_count": 0,
            "failure_count": 0,
            "price_records": 0,
            "headline_records": 0,
        }

        # Get database session
        db: Session = SessionLocal()

        try:
            # Fetch all tracked assets
            assets = db.query(Asset).all()
            self.stats["total_assets"] = len(assets)

            if not assets:
                logger.warning("No assets to process - add assets to database first")
                return self.stats

            logger.info(f"Processing {len(assets)} assets")

            # Process each asset
            for asset in assets:
                success = await self._process_asset(asset, days, db)

                if success:
                    self.stats["success_count"] += 1
                else:
                    self.stats["failure_count"] += 1

                # Call completion callback if provided
                if self.on_complete:
                    try:
                        await self.on_complete(asset.symbol, success)
                    except Exception as e:
                        logger.error(f"Callback failed for {asset.symbol}: {e}")

            logger.info("=" * 60)
            logger.info("Pipeline Complete")
            logger.info(
                f"Success: {self.stats['success_count']}/{self.stats['total_assets']}"
            )
            logger.info(
                f"Prices: {self.stats['price_records']}, Headlines: {self.stats['headline_records']}"
            )
            logger.info("=" * 60)

        finally:
            db.close()

        return self.stats

    async def _process_asset(self, asset: Asset, days: int, db: Session) -> bool:
        """
        Process a single asset: fetch and store data.

        Args:
            asset: Asset model instance
            days: Number of historical days
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        symbol = asset.symbol
        logger.info(f"Processing: {symbol} ({asset.name})")

        try:
            # Step 1: Fetch OHLC data
            logger.info(f"  → Fetching OHLC for {symbol}")
            ohlc_df = await self.ohlc_ingester.fetch_ohlc(symbol, days)
            price_count = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.ohlc_ingester.store_ohlc(symbol, ohlc_df, db)
            )
            self.stats["price_records"] += price_count
            logger.info(f"  ✓ Stored {price_count} price records")

            # Step 2: Fetch headlines
            logger.info(f"  → Fetching headlines for {symbol}")
            headlines = await self.headline_ingester.fetch_headlines(symbol, days=7)
            headline_count = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.headline_ingester.store_headlines(symbol, headlines, db),
            )
            self.stats["headline_records"] += headline_count
            logger.info(f"  ✓ Stored {headline_count} headlines")

            logger.info(f"  ✓ {symbol} completed successfully")
            return True

        except Exception as e:
            logger.error(f"  ✗ {symbol} failed: {e}")
            return False

    async def run_for_symbol(self, symbol: str, days: int = 30) -> bool:
        """
        Run pipeline for a specific symbol only.

        Args:
            symbol: Asset symbol to process
            days: Number of historical days

        Returns:
            True if successful
        """
        db: Session = SessionLocal()

        try:
            asset = db.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                logger.error(f"Asset not found: {symbol}")
                return False

            return await self._process_asset(asset, days, db)

        finally:
            db.close()

    def schedule(
        self, hour: int | None = None, minute: int = 30, timezone: str | None = None
    ) -> AsyncIOScheduler:
        """
        Start the scheduled pipeline.

        Default: 2 hours after market close (e.g., 5:30 PM) in market timezone.

        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            timezone: Timezone for scheduling

        Returns:
            The scheduler instance
        """
        if hour is None:
            hour = settings.market_close_hour + 2  # Run 2 hours after close

        if timezone is None:
            timezone = settings.market_timezone

        self.scheduler = AsyncIOScheduler()

        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)

        self.scheduler.add_job(
            self.run,
            trigger=trigger,
            id="daily_ingestion",
            name="Daily Data Ingestion Pipeline",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Pipeline scheduled at {hour:02d}:{minute:02d} {timezone}")

        return self.scheduler

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Pipeline scheduler stopped")


# =============================================================================
# Convenience Functions
# =============================================================================


async def run_daily_pipeline(days: int = 30) -> dict:
    """
    Execute the daily pipeline immediately.

    This is the main entry point for manual pipeline execution.

    Args:
        days: Number of historical days to fetch

    Returns:
        Pipeline statistics dictionary
    """
    pipeline = DailyIngestionPipeline()
    return await pipeline.run(days)


def start_pipeline_scheduler(
    hour: int | None = None, minute: int = 30, timezone: str | None = None
) -> DailyIngestionPipeline:
    """
    Start the daily pipeline scheduler.

    Args:
        hour: Hour to run daily
        minute: Minute to run
        timezone: Timezone for scheduling

    Returns:
        The pipeline instance (can be used to stop later)
    """
    pipeline = DailyIngestionPipeline()
    pipeline.schedule(hour=hour, minute=minute, timezone=timezone)
    return pipeline


# =============================================================================
# Asset Seeding Helper
# =============================================================================


async def seed_default_assets(db: Session) -> list[str]:
    """
    Seed the database with default tracked assets.

    Default assets:
    - AAPL (Apple Inc.)
    - MSFT (Microsoft)
    - GOOGL (Alphabet)
    - TSLA (Tesla)
    - BTC-USD (Bitcoin)
    - ETH-USD (Ethereum)

    Returns:
        List of seeded symbols
    """
    # Load Indian stocks from JSON
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "indian_stocks.json"
    )

    try:
        with open(data_path, "r") as f:
            default_assets = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Indian stocks data not found at {data_path}, using fallback.")
        default_assets = [
            {
                "symbol": "RELIANCE.NS",
                "name": "Reliance Industries Ltd",
                "asset_type": "stock",
            },
            {
                "symbol": "TCS.NS",
                "name": "Tata Consultancy Services",
                "asset_type": "stock",
            },
        ]

    seeded = []

    for asset_data in default_assets:
        existing = db.query(Asset).filter(Asset.symbol == asset_data["symbol"]).first()

        if not existing:
            asset = Asset(**asset_data)
            db.add(asset)
            seeded.append(asset_data["symbol"])
            logger.info(f"Seeded asset: {asset_data['symbol']}")

    db.commit()
    return seeded
