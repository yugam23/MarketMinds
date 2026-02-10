"""
MarketMinds Sentiment Engine Service
Orchestrates sentiment analysis and daily aggregation.

Responsibilities:
- Score headlines with sentiment
- Aggregate daily sentiment by asset
- Store results in database
- Provide sentiment data via API
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.core.database import SessionLocal
from server.models.models import Headline, DailySentiment, Asset
from server.ml.finbert_analyzer import SentimentAnalyzer, create_analyzer

logger = logging.getLogger(__name__)


# =============================================================================
# Sentiment Scoring Service
# =============================================================================


class SentimentScoringService:
    """
    Scores headlines with sentiment and updates database.

    This service:
    1. Finds unscored headlines in the database
    2. Processes them through the sentiment analyzer
    3. Updates headlines with sentiment scores

    Example:
        service = SentimentScoringService()
        count = service.score_pending_headlines(limit=100)
        print(f"Scored {count} headlines")
    """

    def __init__(
        self, analyzer: SentimentAnalyzer | None = None, use_finbert: bool = True
    ):
        """
        Initialize scoring service.

        Args:
            analyzer: Pre-configured analyzer (or creates new one)
            use_finbert: Whether to use FinBERT (True) or VADER (False)
        """
        self.analyzer = analyzer or create_analyzer(use_finbert=use_finbert)

    def score_pending_headlines(
        self, db: Session, limit: int = 100, batch_size: int = 16
    ) -> int:
        """
        Score all unscored headlines in database.

        Args:
            db: Database session
            limit: Maximum headlines to process
            batch_size: Batch size for analyzer

        Returns:
            Number of headlines scored
        """
        # Find headlines without sentiment scores
        pending = (
            db.query(Headline)
            .filter(Headline.sentiment_score.is_(None))
            .limit(limit)
            .all()
        )

        if not pending:
            logger.info("No pending headlines to score")
            return 0

        logger.info(f"Scoring {len(pending)} headlines...")

        # Extract texts
        texts = [h.title for h in pending]

        # Analyze in batches
        scores = self.analyzer.analyze(texts, batch_size=batch_size)

        # Update database
        for headline, score in zip(pending, scores):
            headline.sentiment_score = Decimal(str(score))

        db.commit()
        logger.info(f"Scored {len(pending)} headlines")

        return len(pending)

    def score_headlines_for_symbol(
        self, db: Session, symbol: str, force_rescore: bool = False
    ) -> int:
        """
        Score all headlines for a specific symbol.

        Args:
            db: Database session
            symbol: Asset symbol
            force_rescore: Re-score even if already scored

        Returns:
            Number of headlines scored
        """
        query = db.query(Headline).filter(Headline.symbol == symbol)

        if not force_rescore:
            query = query.filter(Headline.sentiment_score.is_(None))

        headlines = query.all()

        if not headlines:
            return 0

        texts = [h.title for h in headlines]
        scores = self.analyzer.analyze(texts)

        for headline, score in zip(headlines, scores):
            headline.sentiment_score = Decimal(str(score))

        db.commit()
        return len(headlines)


# =============================================================================
# Daily Sentiment Aggregation Service
# =============================================================================


class DailySentimentService:
    """
    Computes and stores daily sentiment aggregates.

    For each asset and date, aggregates:
    - Average sentiment score
    - Number of headlines
    - Most impactful headline (highest absolute sentiment)

    Example:
        service = DailySentimentService()
        result = service.compute_for_date("AAPL", date.today())
    """

    def compute_for_date(
        self, db: Session, symbol: str, target_date: date
    ) -> dict[str, Any]:
        """
        Compute daily sentiment aggregate for a symbol and date.

        Args:
            db: Database session
            symbol: Asset symbol
            target_date: Date to compute for

        Returns:
            Dictionary with avg_sentiment, headline_count, top_headline
        """
        # Get scored headlines for this date
        headlines = (
            db.query(Headline)
            .filter(
                Headline.symbol == symbol,
                Headline.date == target_date,
                Headline.sentiment_score.isnot(None),
            )
            .all()
        )

        if not headlines:
            return {"avg_sentiment": 0.0, "headline_count": 0, "top_headline": None}

        # Extract scores as floats
        scores = [float(h.sentiment_score) for h in headlines]

        # Find most impactful headline (highest absolute sentiment)
        abs_scores = [abs(s) for s in scores]
        top_idx = np.argmax(abs_scores)
        top_headline = headlines[top_idx].title

        return {
            "avg_sentiment": round(np.mean(scores), 4),
            "headline_count": len(scores),
            "top_headline": top_headline,
        }

    def store_daily_sentiment(
        self, db: Session, symbol: str, target_date: date, data: dict[str, Any]
    ) -> DailySentiment:
        """
        Store or update daily sentiment record.

        Args:
            db: Database session
            symbol: Asset symbol
            target_date: Date for the record
            data: Sentiment data from compute_for_date

        Returns:
            The created or updated DailySentiment record
        """
        # Check for existing record
        existing = (
            db.query(DailySentiment)
            .filter(DailySentiment.symbol == symbol, DailySentiment.date == target_date)
            .first()
        )

        if existing:
            # Update existing
            existing.avg_sentiment = Decimal(str(data["avg_sentiment"]))
            existing.headline_count = data["headline_count"]
            existing.top_headline = data["top_headline"]
            record = existing
        else:
            # Create new
            record = DailySentiment(
                symbol=symbol,
                date=target_date,
                avg_sentiment=Decimal(str(data["avg_sentiment"])),
                headline_count=data["headline_count"],
                top_headline=data["top_headline"],
            )
            db.add(record)

        db.commit()
        return record

    def compute_and_store(
        self, db: Session, symbol: str, target_date: date
    ) -> DailySentiment | None:
        """
        Compute and store daily sentiment in one step.

        Args:
            db: Database session
            symbol: Asset symbol
            target_date: Date to process

        Returns:
            DailySentiment record or None if no data
        """
        data = self.compute_for_date(db, symbol, target_date)

        if data["headline_count"] == 0:
            return None

        return self.store_daily_sentiment(db, symbol, target_date, data)

    def process_date_range(
        self, db: Session, symbol: str, start_date: date, end_date: date
    ) -> list[DailySentiment]:
        """
        Process sentiment for a range of dates.

        Args:
            db: Database session
            symbol: Asset symbol
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)

        Returns:
            List of created DailySentiment records
        """
        records = []
        current = start_date

        while current <= end_date:
            record = self.compute_and_store(db, symbol, current)
            if record:
                records.append(record)
            current += timedelta(days=1)

        return records


# =============================================================================
# Sentiment Pipeline
# =============================================================================


class SentimentPipeline:
    """
    Complete sentiment processing pipeline.

    Orchestrates:
    1. Scoring pending headlines
    2. Computing daily aggregates
    3. Processing all tracked assets

    Example:
        pipeline = SentimentPipeline()
        stats = await pipeline.run()
    """

    def __init__(self, use_finbert: bool = True):
        """
        Initialize pipeline.

        Args:
            use_finbert: Use FinBERT (True) or VADER (False)
        """
        self.scorer = SentimentScoringService(use_finbert=use_finbert)
        self.aggregator = DailySentimentService()
        self.stats = {
            "headlines_scored": 0,
            "daily_records_created": 0,
            "assets_processed": 0,
        }

    def run(self, days_back: int = 30) -> dict:
        """
        Run complete sentiment pipeline.

        Args:
            days_back: How many days to compute aggregates for

        Returns:
            Statistics dictionary
        """
        db = SessionLocal()

        try:
            logger.info("=" * 60)
            logger.info("Starting Sentiment Pipeline")
            logger.info("=" * 60)

            # Reset stats
            self.stats = {
                "headlines_scored": 0,
                "daily_records_created": 0,
                "assets_processed": 0,
            }

            # Step 1: Score all pending headlines
            logger.info("Step 1: Scoring pending headlines...")
            scored = self._score_all_pending(db)
            self.stats["headlines_scored"] = scored

            # Step 2: Compute daily aggregates for all assets
            logger.info("Step 2: Computing daily aggregates...")
            assets = db.query(Asset).all()

            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)

            for asset in assets:
                records = self.aggregator.process_date_range(
                    db, asset.symbol, start_date, end_date
                )
                self.stats["daily_records_created"] += len(records)
                self.stats["assets_processed"] += 1
                logger.info(f"  {asset.symbol}: {len(records)} daily records")

            logger.info("=" * 60)
            logger.info("Sentiment Pipeline Complete")
            logger.info(f"Headlines scored: {self.stats['headlines_scored']}")
            logger.info(f"Daily records: {self.stats['daily_records_created']}")
            logger.info(f"Assets processed: {self.stats['assets_processed']}")
            logger.info("=" * 60)

        finally:
            db.close()

        return self.stats

    def _score_all_pending(self, db: Session, max_iterations: int = 10) -> int:
        """Score all pending headlines in batches."""
        total = 0

        for _ in range(max_iterations):
            scored = self.scorer.score_pending_headlines(db, limit=100)
            total += scored

            if scored < 100:  # Less than limit means we're done
                break

        return total


# =============================================================================
# Convenience Functions
# =============================================================================


def run_sentiment_pipeline(use_finbert: bool = True, days_back: int = 30) -> dict:
    """
    Run the complete sentiment pipeline.

    Args:
        use_finbert: Use FinBERT (True) or VADER only (False)
        days_back: Days of history to process

    Returns:
        Pipeline statistics
    """
    pipeline = SentimentPipeline(use_finbert=use_finbert)
    return pipeline.run(days_back=days_back)


def score_single_headline(text: str, use_finbert: bool = True) -> float:
    """
    Score a single headline text.

    Args:
        text: Headline text to analyze
        use_finbert: Use FinBERT or VADER

    Returns:
        Sentiment score in [-1, +1]
    """
    analyzer = create_analyzer(use_finbert=use_finbert)
    return analyzer.analyze_single(text)
