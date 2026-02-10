"""
Feature Engineering Service
Prepares data for LSTM model training and prediction.
"""

import logging
from datetime import date, timedelta
from typing import Tuple

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.preprocessing import MinMaxScaler

from server.models.models import Price, DailySentiment

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Handles data preparation for the Prediction Model.

    Features used:
    - Close Price (Normalized)
    - Volume (Log-transform + Normalized)
    - Daily Sentiment Score (Already -1 to 1)

    Process:
    1. Fetch price and sentiment data
    2. Merge on date
    3. handle missing values
    4. Normalize/Scale
    5. Create sequences (sliding window)
    """

    def __init__(self, db: Session, lookback_days: int = 7):
        self.db = db
        self.lookback = lookback_days
        # Scalers should ideally be fit per symbol and persisted,
        # but for this MVP we'll fit them on the fly during training/inference.
        self.price_scaler = MinMaxScaler(feature_range=(0, 1))
        self.volume_scaler = MinMaxScaler(feature_range=(0, 1))

    def fetch_data(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Fetch and merge price and sentiment data."""
        # 1. Fetch Prices
        prices_query = (
            select(Price)
            .where(Price.symbol == symbol)
            .where(Price.date >= start_date)
            .where(Price.date <= end_date)
            .order_by(Price.date.asc())
        )
        prices = self.db.scalars(prices_query).all()

        if not prices:
            logger.warning(f"No price data found for {symbol}")
            return pd.DataFrame()

        df_prices = pd.DataFrame(
            [
                {"date": p.date, "close": float(p.close), "volume": p.volume}
                for p in prices
            ]
        )
        df_prices.set_index("date", inplace=True)

        # 2. Fetch Sentiment
        sentiment_query = (
            select(DailySentiment)
            .where(DailySentiment.symbol == symbol)
            .where(DailySentiment.date >= start_date)
            .where(DailySentiment.date <= end_date)
            .order_by(DailySentiment.date.asc())
        )
        sentiments = self.db.scalars(sentiment_query).all()

        if sentiments:
            df_sentiments = pd.DataFrame(
                [
                    {"date": s.date, "sentiment": float(s.avg_sentiment)}
                    for s in sentiments
                ]
            )
            df_sentiments.set_index("date", inplace=True)
        else:
            df_sentiments = pd.DataFrame(columns=["sentiment"])

        # 3. Merge (Left join on prices to keep continuous time series)
        df = df_prices.join(df_sentiments, how="left")

        # 4. Fill missing sentiment with Neutral (0.0)
        df["sentiment"] = df["sentiment"].fillna(0.0).astype(float)

        # Sort by date just in case
        df.sort_index(inplace=True)

        return df

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply scaling and transformations."""
        if df.empty:
            return df

        data = df.copy()

        # Log transform volume to handle broad ranges
        # Use log1p to handle 0 volume safely
        data["volume_log"] = np.log1p(data["volume"])

        # Scale features
        # Note: In a real prod system, you'd load pre-fitted scalers for inference.
        # Here we fit on the provided data (assuming it's a batch for training).
        data["close_scaled"] = self.price_scaler.fit_transform(data[["close"]])
        data["volume_scaled"] = self.volume_scaler.fit_transform(data[["volume_log"]])

        # Sentiment is already approx -1 to 1, but let's leave it as is
        # or we could scale it to 0-1 if we wanted different activation functions.
        # LSTM handles -1 to 1 well with Tanh.

        return data[["close_scaled", "volume_scaled", "sentiment"]]

    def create_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create (X, y) sequences for LSTM.
        X: Sequence of features of length `lookback`
        y: Target value (next day's close price)
        """
        features = data.values  # [[close, vol, sent], ...]
        X, y = [], []

        # We need lookback days + 1 target
        for i in range(self.lookback, len(features)):
            # Sequence: from i-lookback to i (exclusive)
            # Target: at i (next step close price)

            seq = features[i - self.lookback : i]
            target = features[i][0]  # Index 0 is close_scaled

            X.append(seq)
            y.append(target)

        return np.array(X), np.array(y)

    def prepare_inference_data(self, symbol: str) -> np.ndarray:
        """
        Prepare the single most recent sequence for prediction.
        Fetches enough recent data to form one sequence.
        """
        # We need 'lookback' days ending today/yesterday.
        # Fetch lookback * 2 to account for weekends/holidays safely
        end_date = date.today()
        start_date = end_date - timedelta(days=self.lookback * 3)

        df = self.fetch_data(symbol, start_date, end_date)

        if len(df) < self.lookback:
            raise ValueError(
                f"Not enough data to predict for {symbol}. Need {self.lookback} days, got {len(df)}."
            )

        # Take the last 'lookback' rows
        df_recent = df.iloc[-self.lookback :]

        # Transform
        df_scaled = self.prepare_features(df_recent)

        # Reshape for LSTM [1, lookback, features]
        return np.expand_dims(df_scaled.values, axis=0)
