
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd

from server.models.models import Asset
from server.pipelines.daily_ingestion import DailyIngestionPipeline

# --- Fixtures ---

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock(spec=Session)
    return session

@pytest.fixture
def mock_ohlc_ingester():
    """Mock OHLCIngester."""
    ingester = MagicMock()
    # Mock return DataFrame for fetch_ohlc
    df = pd.DataFrame({
        'Open': [100.0, 101.0],
        'High': [102.0, 103.0],
        'Low': [99.0, 100.0],
        'Close': [101.0, 102.0],
        'Volume': [1000, 2000]
    })
    ingester.fetch_ohlc = AsyncMock(return_value=df)
    ingester.store_ohlc = MagicMock(return_value=2)
    return ingester

@pytest.fixture
def mock_headline_ingester():
    """Mock HeadlineIngester."""
    ingester = MagicMock()
    headlines = [{'title': 'Test News', 'sentiment_score': 0.5}]
    ingester.fetch_headlines = AsyncMock(return_value=headlines)
    ingester.store_headlines = MagicMock(return_value=1)
    return ingester

@pytest.fixture
def test_pipeline(mock_ohlc_ingester, mock_headline_ingester):
    """Pipeline instance with mocks."""
    return DailyIngestionPipeline(
        ohlc_ingester=mock_ohlc_ingester,
        headline_ingester=mock_headline_ingester
    )

# --- Tests ---

@pytest.mark.asyncio
async def test_process_asset_success(test_pipeline, mock_db_session):
    """Test successful asset processing."""
    asset = Asset(symbol="TEST", name="Test Asset")
    
    success = await test_pipeline._process_asset(asset, days=30, db=mock_db_session)
    
    assert success is True
    test_pipeline.ohlc_ingester.fetch_ohlc.assert_awaited_once_with("TEST", 30)
    test_pipeline.headline_ingester.fetch_headlines.assert_awaited_once()
    
    # Check stats update
    assert test_pipeline.stats["price_records"] == 2
    assert test_pipeline.stats["headline_records"] == 1

@pytest.mark.asyncio
async def test_process_asset_failure(test_pipeline, mock_db_session):
    """Test asset processing failure."""
    asset = Asset(symbol="FAIL", name="Fail Asset")
    
    # Simulate fetch error
    test_pipeline.ohlc_ingester.fetch_ohlc = AsyncMock(side_effect=Exception("API Error"))
    
    success = await test_pipeline._process_asset(asset, days=30, db=mock_db_session)
    
    assert success is False
    assert test_pipeline.stats["price_records"] == 0

@pytest.mark.asyncio
async def test_run_full_pipeline(test_pipeline):
    """Test full pipeline execution."""
    
    # Mock DB interaction within run()
    mock_assets = [
        Asset(symbol="A1", name="Asset 1"),
        Asset(symbol="A2", name="Asset 2")
    ]
    
    with patch('server.pipelines.daily_ingestion.SessionLocal') as mock_session_cls:
        mock_db = mock_session_cls.return_value
        mock_db.query.return_value.all.return_value = mock_assets
        
        stats = await test_pipeline.run(days=10)
        
        assert stats["total_assets"] == 2
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 0
        
        # Verify loops
        assert test_pipeline.ohlc_ingester.fetch_ohlc.call_count == 2
