"""
Tests for Data Ingestion Service
Tests for OHLC and headline ingestion with mocked external APIs.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from server.models.models import Asset, Price
from server.services.data_ingestion import OHLCIngester, HeadlineIngester


class TestOHLCIngester:
    """Tests for OHLC price data ingestion."""

    def test_init(self):
        """Test ingester initialization."""
        ingester = OHLCIngester(throttle_seconds=2.0)
        assert ingester.throttle == 2.0
        assert ingester.MAX_RETRIES == 3

    @pytest.mark.asyncio
    async def test_fetch_ohlc_success(self):
        """Test successful OHLC data fetch."""
        ingester = OHLCIngester(throttle_seconds=0.01)  # Fast for testing

        # Create mock DataFrame
        mock_df = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [105.0, 106.0],
                "Low": [99.0, 100.0],
                "Close": [104.0, 105.0],
                "Volume": [1000000, 1100000],
            },
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"]),
        )

        with patch.object(ingester, "_fetch_sync", return_value=mock_df):
            result = await ingester.fetch_ohlc("RELIANCE.NS", days=7)

        assert not result.empty
        assert len(result) == 2
        assert "Open" in result.columns
        assert "Close" in result.columns

    @pytest.mark.asyncio
    async def test_fetch_ohlc_empty_data(self):
        """Test that empty data raises ExternalAPIError."""
        from server.core.exceptions import ExternalAPIError

        ingester = OHLCIngester(throttle_seconds=0.01)

        with patch.object(ingester, "_fetch_sync", return_value=pd.DataFrame()):
            with pytest.raises(ExternalAPIError) as exc_info:
                await ingester.fetch_ohlc("INVALID", days=7)

            assert "No data returned" in str(exc_info.value)

    def test_store_ohlc(self, db_session):
        """Test storing OHLC data to database."""
        # Create test asset first
        asset = Asset(symbol="TEST", name="Test Stock", asset_type="stock")
        db_session.add(asset)
        db_session.commit()

        ingester = OHLCIngester()

        # Create test DataFrame
        test_df = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [99.0, 100.0, 101.0],
                "Close": [104.0, 105.0, 106.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.DatetimeIndex(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )

        count = ingester.store_ohlc("TEST", test_df, db_session)

        assert count == 3

        # Verify data in database
        prices = db_session.query(Price).filter(Price.symbol == "TEST").all()
        assert len(prices) == 3
        assert prices[0].open == Decimal("100.0")
        assert prices[0].close == Decimal("104.0")

    def test_store_ohlc_updates_existing(self, db_session):
        """Test that existing records are updated, not duplicated."""
        # Create test asset and initial price
        asset = Asset(symbol="UPD", name="Update Test", asset_type="stock")
        db_session.add(asset)

        existing_price = Price(
            symbol="UPD",
            date=datetime(2024, 1, 1).date(),
            open=Decimal("90.0"),
            high=Decimal("95.0"),
            low=Decimal("89.0"),
            close=Decimal("94.0"),
            volume=500000,
        )
        db_session.add(existing_price)
        db_session.commit()

        ingester = OHLCIngester()

        # New data with updated values
        test_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Close": [104.0],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex(["2024-01-01"]),
        )

        count = ingester.store_ohlc("UPD", test_df, db_session)

        assert count == 1

        # Verify only one record exists with updated values
        prices = db_session.query(Price).filter(Price.symbol == "UPD").all()
        assert len(prices) == 1
        assert prices[0].open == Decimal("100.0")  # Updated value
        assert prices[0].volume == 1000000  # Updated value


class TestHeadlineIngester:
    """Tests for news headline ingestion."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        ingester = HeadlineIngester(api_key="", cache=None)
        assert ingester.client is None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch("server.services.data_ingestion.NewsApiClient") as mock_client:
            ingester = HeadlineIngester(api_key="test-key", cache=None)
            mock_client.assert_called_once_with(api_key="test-key")

    @pytest.mark.asyncio
    async def test_fetch_headlines_no_client(self):
        """Test that missing client returns empty list."""
        ingester = HeadlineIngester(api_key="", cache=None)
        result = await ingester.fetch_headlines("RELIANCE.NS", days=7)
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_headlines_success(self):
        """Test successful headline fetch."""
        mock_client = MagicMock()
        mock_client.get_everything.return_value = {
            "articles": [
                {
                    "title": "Reliance announces new product",
                    "source": {"name": "TechNews"},
                    "url": "https://example.com/article1",
                    "publishedAt": "2024-01-15T10:00:00Z",
                },
                {
                    "title": "RELIANCE stock rises",
                    "source": {"name": "Finance Daily"},
                    "url": "https://example.com/article2",
                    "publishedAt": "2024-01-15T11:00:00Z",
                },
            ]
        }

        with patch(
            "server.services.data_ingestion.NewsApiClient", return_value=mock_client
        ):
            ingester = HeadlineIngester(api_key="test-key", cache=None)
            result = await ingester.fetch_headlines("RELIANCE.NS", days=7)

        assert len(result) == 2
        assert result[0]["title"] == "Reliance announces new product"

    def test_store_headlines(self, db_session):
        """Test storing headlines to database."""
        # Create test asset
        asset = Asset(symbol="NEWS", name="News Test", asset_type="stock")
        db_session.add(asset)
        db_session.commit()

        ingester = HeadlineIngester(api_key="", cache=None)

        articles = [
            {
                "title": "Test headline 1",
                "source": {"name": "Source 1"},
                "url": "https://example.com/1",
                "publishedAt": "2024-01-15T10:00:00Z",
            },
            {
                "title": "Test headline 2",
                "source": {"name": "Source 2"},
                "url": "https://example.com/2",
                "publishedAt": "2024-01-15T11:00:00Z",
            },
            {
                "title": "[Removed]",  # Should be skipped
                "source": {"name": "Source 3"},
                "url": "https://example.com/3",
                "publishedAt": "2024-01-15T12:00:00Z",
            },
        ]

        count = ingester.store_headlines("NEWS", articles, db_session)

        assert count == 2  # Only 2 valid headlines

    def test_store_headlines_no_duplicates(self, db_session):
        """Test that duplicate headlines are not stored."""
        from server.models.models import Headline

        # Create test asset and existing headline
        asset = Asset(symbol="DUP", name="Duplicate Test", asset_type="stock")
        db_session.add(asset)

        existing = Headline(
            symbol="DUP",
            date=datetime(2024, 1, 15).date(),
            title="Existing headline",
            source="Source",
            url="https://example.com/existing",
        )
        db_session.add(existing)
        db_session.commit()

        ingester = HeadlineIngester(api_key="", cache=None)

        articles = [
            {
                "title": "Existing headline",  # Duplicate - should be skipped
                "source": {"name": "Source"},
                "url": "https://example.com/new",
                "publishedAt": "2024-01-15T10:00:00Z",
            },
            {
                "title": "New headline",  # New - should be stored
                "source": {"name": "Source"},
                "url": "https://example.com/new2",
                "publishedAt": "2024-01-15T11:00:00Z",
            },
        ]

        count = ingester.store_headlines("DUP", articles, db_session)

        assert count == 1  # Only the new headline

        headlines = db_session.query(Headline).filter(Headline.symbol == "DUP").all()
        assert len(headlines) == 2  # 1 existing + 1 new
