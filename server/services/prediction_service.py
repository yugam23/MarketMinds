"""
Prediction Service
Orchestrates model training and price prediction.
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session
import numpy as np

from server.services.feature_engineering import FeatureEngineer
from server.ml.lstm_model import PricePredictorLSTM

logger = logging.getLogger(__name__)


import os


class PredictionService:
    """
    Service for managing price predictions.
    """

    def __init__(self, db: Session):
        self.db = db
        self.feature_engineer = FeatureEngineer(db)
        # Use absolute path to avoid CWD issues
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(base_dir, "models")
        self.predictor = PricePredictorLSTM(model_dir=model_dir)

    def train_model(self, symbol: str, days_data: int = 365) -> Dict[str, Any]:
        """
        Train a model for the given symbol.
        """
        logger.info(f"Starting model training for {symbol}")

        # 1. Fetch Data
        end_date = date.today()
        start_date = end_date - timedelta(days=days_data)

        df = self.feature_engineer.fetch_data(symbol, start_date, end_date)

        if len(df) < 50:
            msg = f"Insufficient data for {symbol}. Got {len(df)} records."
            logger.warning(msg)
            return {"status": "failed", "message": msg}

        # 2. Prepare Features
        df_scaled = self.feature_engineer.prepare_features(df)
        X, y = self.feature_engineer.create_sequences(df_scaled)

        if len(X) == 0:
            return {"status": "failed", "message": "Not enough data for sequences."}

        # 3. Train Model
        # Using a simple 70/30 split for validation inside the train method or similar
        # For now relying on internal validation split of the model class
        history = self.predictor.train(X, y, epochs=20, batch_size=32)

        # 4. Save Model
        self.predictor.save(symbol)

        # 5. Return Stats
        final_loss = history.history["loss"][-1]
        return {
            "status": "success",
            "message": f"Model trained for {symbol}",
            "final_loss": float(final_loss),
            "data_points": len(X),
        }

    def predict_next_price(self, symbol: str) -> Dict[str, Any]:
        """
        Predict the next day's close price.
        """
        # 1. Load Model
        if not self.predictor.load(symbol):
            return {
                "status": "failed",
                "message": "Model not found. Train model first.",
            }

        # 2. Prepare Data (Single Sequence)
        try:
            X_input = self.feature_engineer.prepare_inference_data(symbol)
        except ValueError as e:
            return {"status": "failed", "message": str(e)}

        # 3. Predict
        # Output is scaled price (0-1)
        predicted_scaled = self.predictor.predict(X_input)
        pred_value = float(predicted_scaled[0][0])

        # 4. Inverse Transform (Denormalize)
        # We need the scaler used for training...
        # But here we re-fit the scaler on recent data in prepare_inference_data.
        # This is an approximation. Ideally we save the scaler.
        # However, for MinMaxScaler(0,1), if we fit on recent window,
        # the min/max might differ from training history.
        # For this MVP, we will use the scaler attached to feature_engineer
        # which was jus fit in 'prepare_inference_data'.

        scaler = self.feature_engineer.price_scaler
        # inverse_transform expects 2D array
        pred_price = scaler.inverse_transform([[pred_value]])[0][0]

        return {
            "symbol": symbol,
            "predicted_price": round(pred_price, 2),
            "prediction_date": date.today() + timedelta(days=1),
            "confidence_score": 0.0,  # Placeholder for confidence
            "used_sentiment": False,  # TODO checks if sentiment was actually used
        }
