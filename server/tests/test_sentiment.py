"""
Tests for Sentiment Analysis Module
Tests for FinBERT, VADER, and sentiment engine services.
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestVADERAnalyzer:
    """Tests for VADER sentiment analyzer."""

    def test_init(self):
        """Test VADER initialization."""
        from server.ml.finbert_analyzer import VADERAnalyzer

        analyzer = VADERAnalyzer()
        assert analyzer.sia is None  # Lazy loading
        assert analyzer._initialized is False

    def test_analyze_single(self):
        """Test single text analysis."""
        from server.ml.finbert_analyzer import VADERAnalyzer

        analyzer = VADERAnalyzer()

        # Positive sentiment
        score = analyzer.analyze_single("Great earnings report, stock surging!")
        assert score > 0.1

        # Negative sentiment
        score = analyzer.analyze_single("Terrible crash, investors panic")
        assert score < -0.1

        # Neutral
        score = analyzer.analyze_single("Company reports quarterly results")
        assert -0.3 < score < 0.3

    def test_analyze_batch(self):
        """Test batch text analysis."""
        from server.ml.finbert_analyzer import VADERAnalyzer

        analyzer = VADERAnalyzer()

        texts = [
            "Stock rallies on positive news",
            "Markets decline amid uncertainty",
            "Trading volume remains steady",
        ]

        scores = analyzer.analyze(texts)

        assert len(scores) == 3
        assert all(isinstance(s, float) for s in scores)
        assert all(-1 <= s <= 1 for s in scores)


class TestSentimentAnalyzer:
    """Tests for combined sentiment analyzer."""

    def test_init_without_finbert(self):
        """Test initialization with VADER only."""
        from server.ml.finbert_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer(use_finbert=False)
        assert analyzer.use_finbert is False

    def test_analyze_with_vader_fallback(self):
        """Test that VADER fallback works."""
        from server.ml.finbert_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer(use_finbert=False)

        scores = analyzer.analyze(["Stock price increases"])
        assert len(scores) == 1
        assert isinstance(scores[0], float)

    def test_analyze_empty_list(self):
        """Test empty input returns empty list."""
        from server.ml.finbert_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer(use_finbert=False)

        scores = analyzer.analyze([])
        assert scores == []


class TestSentimentScoringService:
    """Tests for sentiment scoring service."""

    def test_score_pending_headlines_no_pending(self, db_session):
        """Test with no pending headlines."""
        from server.services.sentiment_engine import SentimentScoringService

        service = SentimentScoringService(use_finbert=False)
        count = service.score_pending_headlines(db_session, limit=10)
        assert count == 0

    def test_score_pending_headlines(self, db_session):
        """Test scoring pending headlines."""
        from server.models.models import Asset, Headline
        from server.services.sentiment_engine import SentimentScoringService

        # Create test data
        asset = Asset(symbol="SENT", name="Sentiment Test", asset_type="stock")
        db_session.add(asset)

        headline = Headline(
            symbol="SENT",
            date=date.today(),
            title="Company announces great earnings",
            source="TestSource",
            url="https://example.com/test",
            sentiment_score=None,  # Unscored
        )
        db_session.add(headline)
        db_session.commit()

        # Score headlines
        service = SentimentScoringService(use_finbert=False)
        count = service.score_pending_headlines(db_session, limit=10)

        assert count == 1

        # Verify score was added
        db_session.refresh(headline)
        assert headline.sentiment_score is not None
        assert isinstance(headline.sentiment_score, Decimal)


class TestDailySentimentService:
    """Tests for daily sentiment aggregation."""

    def test_compute_for_date_no_headlines(self, db_session):
        """Test with no headlines returns zeros."""
        from server.services.sentiment_engine import DailySentimentService

        service = DailySentimentService()
        result = service.compute_for_date(db_session, "NOPE", date.today())

        assert result["avg_sentiment"] == 0.0
        assert result["headline_count"] == 0
        assert result["top_headline"] is None

    def test_compute_for_date_with_headlines(self, db_session):
        """Test aggregation with scored headlines."""
        from server.models.models import Asset, Headline
        from server.services.sentiment_engine import DailySentimentService

        # Create test data
        asset = Asset(symbol="AGG", name="Aggregate Test", asset_type="stock")
        db_session.add(asset)

        today = date.today()

        # Add scored headlines
        headlines = [
            Headline(
                symbol="AGG",
                date=today,
                title="Positive news",
                source="S1",
                url="https://example.com/1",
                sentiment_score=Decimal("0.5"),
            ),
            Headline(
                symbol="AGG",
                date=today,
                title="Very negative news",
                source="S2",
                url="https://example.com/2",
                sentiment_score=Decimal("-0.8"),
            ),
            Headline(
                symbol="AGG",
                date=today,
                title="Neutral update",
                source="S3",
                url="https://example.com/3",
                sentiment_score=Decimal("0.0"),
            ),
        ]
        db_session.add_all(headlines)
        db_session.commit()

        # Compute aggregates
        service = DailySentimentService()
        result = service.compute_for_date(db_session, "AGG", today)

        assert result["headline_count"] == 3
        # Average: (0.5 + -0.8 + 0.0) / 3 = -0.1
        assert -0.15 < result["avg_sentiment"] < -0.05
        # Top headline should be "Very negative news" (highest absolute)
        assert result["top_headline"] == "Very negative news"

    def test_compute_and_store(self, db_session):
        """Test computing and storing daily sentiment."""
        from server.models.models import Asset, Headline, DailySentiment
        from server.services.sentiment_engine import DailySentimentService

        # Create test data
        asset = Asset(symbol="STORE", name="Store Test", asset_type="stock")
        db_session.add(asset)

        today = date.today()
        headline = Headline(
            symbol="STORE",
            date=today,
            title="Good news",
            source="S",
            url="https://example.com/1",
            sentiment_score=Decimal("0.7"),
        )
        db_session.add(headline)
        db_session.commit()

        # Store
        service = DailySentimentService()
        record = service.compute_and_store(db_session, "STORE", today)

        assert record is not None
        assert record.symbol == "STORE"
        assert record.headline_count == 1
        assert float(record.avg_sentiment) == 0.7


class TestCreateAnalyzer:
    """Tests for analyzer factory function."""

    def test_create_analyzer_vader(self):
        """Test creating VADER-only analyzer."""
        from server.ml.finbert_analyzer import create_analyzer

        analyzer = create_analyzer(use_finbert=False)
        assert analyzer.use_finbert is False

    def test_create_analyzer_finbert(self):
        """Test creating FinBERT analyzer."""
        from server.ml.finbert_analyzer import create_analyzer

        analyzer = create_analyzer(use_finbert=True)
        assert analyzer.use_finbert is True
