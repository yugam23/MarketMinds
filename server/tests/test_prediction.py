"""
Tests for Prediction Module
Tests for feature engineering and prediction service.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from server.models.models import Asset, Price, DailySentiment
from server.services.feature_engineering import FeatureEngineer
from server.services.prediction_service import PredictionService


class TestFeatureEngineer:
    """Tests for feature engineering."""

    def test_fetch_data_empty(self, db_session):
        """Test fetching with no data."""
        engineer = FeatureEngineer(db_session)
        df = engineer.fetch_data("TEST", date.today(), date.today())
        assert df.empty

    def test_fetch_data_merge(self, db_session):
        """Test merging price and sentiment."""
        # Create test data
        asset = Asset(symbol="FE", name="Test FE", asset_type="stock")
        db_session.add(asset)

        today = date.today()

        # Add Price
        price = Price(
            symbol="FE", date=today, open=100, high=110, low=90, close=105, volume=1000
        )
        db_session.add(price)

        # Add Sentiment
        sentiment = DailySentiment(
            symbol="FE", date=today, avg_sentiment=0.5, headline_count=1
        )
        db_session.add(sentiment)
        db_session.commit()

        # Fetch
        engineer = FeatureEngineer(db_session)
        df = engineer.fetch_data("FE", today, today)

        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]["close"] == 105.0
        assert df.iloc[0]["sentiment"] == 0.5

    def test_fill_missing_sentiment(self, db_session):
        """Test that missing sentiment keys are filled with 0."""
        # Create data with price but NO sentiment
        asset = Asset(symbol="NOSENT", name="No Sent", asset_type="stock")
        db_session.add(asset)

        today = date.today()
        price = Price(
            symbol="NOSENT",
            date=today,
            open=100,
            high=110,
            low=90,
            close=105,
            volume=1000,
        )
        db_session.add(price)
        db_session.commit()

        engineer = FeatureEngineer(db_session)
        df = engineer.fetch_data("NOSENT", today, today)

        assert df.iloc[0]["sentiment"] == 0.0

    def test_prepare_features(self, db_session):
        """Test feature scaling and transformation."""
        engineer = FeatureEngineer(db_session)

        # Mock DataFrame
        data = {
            "close": [100, 200],
            "volume": [10, 100],  # log1p -> ~2.4, ~4.6
            "sentiment": [0.5, -0.5],
        }
        df = pd.DataFrame(data)

        df_scaled = engineer.prepare_features(df)

        assert "close_scaled" in df_scaled.columns
        assert "volume_scaled" in df_scaled.columns
        assert "sentiment" in df_scaled.columns

        # Check scaling (MinMax 0-1)
        assert df_scaled["close_scaled"].min() == 0.0
        assert df_scaled["close_scaled"].max() == 1.0

    def test_create_sequences(self, db_session):
        """Test LSTM sequence creation."""
        engineer = FeatureEngineer(db_session, lookback_days=2)

        # Mock Scaled Data (4 days)
        data = np.array(
            [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2], [0.3, 0.3, 0.3], [0.4, 0.4, 0.4]]
        )
        df = pd.DataFrame(data, columns=["close_scaled", "volume_scaled", "sentiment"])

        X, y = engineer.create_sequences(df)

        # Length should be 4 - 2 = 2 sequences
        assert len(X) == 2
        assert len(y) == 2

        # First Sequence: days 0, 1. Target: day 2 close
        np.testing.assert_array_equal(X[0], data[0:2])
        assert y[0] == data[2][0]


class TestPredictionService:
    """Tests for prediction service."""

    @patch("server.ml.lstm_model.PricePredictorLSTM")
    def test_train_model_not_enough_data(self, MockLSTM, db_session):
        """Test training aborts if insufficient data."""
        service = PredictionService(db_session)
        # Mock fetch_data to return empty
        service.feature_engineer.fetch_data = MagicMock(return_value=pd.DataFrame())

        result = service.train_model("TEST")
        assert result["status"] == "failed"
        assert "Insufficient data" in result["message"]

    @patch("server.ml.lstm_model.PricePredictorLSTM")
    def test_predict_model_not_found(self, MockLSTM, db_session):
        """Test prediction fails if model load fails."""
        mock_instance = MockLSTM.return_value
        mock_instance.load.return_value = False

        service = PredictionService(db_session)
        result = service.predict_next_price("TEST")

        assert result["status"] == "failed"
        assert "Model not found" in result["message"]
