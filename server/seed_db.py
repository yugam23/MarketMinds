import asyncio
import logging
import sys
import os

# Add server directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.core.config import settings
from server.core.database import init_db
from server.services.data_ingestion import OHLCIngester
from server.models.models import Asset
from server.pipelines.daily_ingestion import seed_default_assets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_data():
    logger.info("Starting data seed...")

    # Initialize DB (create tables if needed)
    init_db()

    # DB Connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check for assets, seed defaults if missing
        assets = db.query(Asset).all()
        if not assets:
            logger.info("No assets found. Seeding Indian stocks.")
            seeded_symbols = await seed_default_assets(db)
            # Refresh asset list
            assets = db.query(Asset).all()

        ingester = OHLCIngester()
        headline_ingester = create_headline_ingester()

        for asset in assets:
            logger.info(f"Processing {asset.symbol}...")

            # Fetch OHLC
            logger.info(f"  Fetching 365 days of history...")
            try:
                df = await ingester.fetch_ohlc(asset.symbol, days=365)
                if not df.empty:
                    ingester.store_ohlc(asset.symbol, df, db)
                    logger.info(f"  Stored {len(df)} records")
                else:
                    logger.warning(f"  No price data")
            except Exception as e:
                logger.error(f"  Failed to fetch prices: {e}")

            # Fetch Headlines
            logger.info(f"  Fetching 7 days of headlines...")
            try:
                headlines = await headline_ingester.fetch_headlines(
                    asset.symbol, days=7
                )
                if headlines:
                    headline_ingester.store_headlines(asset.symbol, headlines, db)
                    logger.info(f"  Stored {len(headlines)} headlines")
                else:
                    logger.info(f"  No headlines found")
            except Exception as e:
                logger.error(f"  Failed to fetch headlines: {e}")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        db.close()
        logger.info("Seeding complete.")


if __name__ == "__main__":
    from server.services.data_ingestion import (
        create_headline_ingester,
    )  # Local import to avoid circular dep issues if any

    asyncio.run(seed_data())
