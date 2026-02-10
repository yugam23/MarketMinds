"""
LSTM Prediction Model (Robust)
Deep learning model for price prediction with Mock fallback.

Architecture:
- LSTM Layer 1 (50 units, return_sequences=True)
- Dropout (0.2)
- LSTM Layer 2 (50 units)
- Dropout (0.2)
- Dense Output Layer (1 unit)

Fallback:
- If TensorFlow is unavailable (e.g. DLL errors), uses a MockModel
  that predicts based on recent trends and simple statistics.
"""

import json
import logging
import os
import random
from typing import Optional, Tuple, Any

import numpy as np

logger = logging.getLogger(__name__)

# Constants
MODEL_DIR = "models"
LOOKBACK = 7
FEATURES = 3  # Close, Volume, Sentiment


class MockModel:
    """Simple mock model for when TensorFlow is unavailable."""

    def __init__(self):
        self.last_loss = 0.0
        self.stats = {}

    def fit(self, X, y, **kwargs):
        """Simulate training."""
        logger.warning("Using MockModel.fit() - TensorFlow not available")
        # Calculate simple stats from y (target is scaled price)
        self.stats = {
            "mean": float(np.mean(y)),
            "std": float(np.std(y)),
            "last": float(y[-1]) if len(y) > 0 else 0.5,
        }
        self.last_loss = 0.01

        # Return a mock history object
        class History:
            history = {"loss": [0.1, 0.05, 0.01], "mae": [0.2, 0.1, 0.05]}

        return History()

    def predict(self, X):
        """Simulate prediction."""
        # X shape: (batch_size, lookback, features)
        # Return array of shape (batch, 1)
        predictions = []
        for i in range(len(X)):
            # Use last price from input sequence + small random noise + sentiment influence
            # Feature 0 is Close, Feature 2 is Sentiment
            last_close = X[i, -1, 0]
            sentiment = X[i, -1, 2]

            # Simple logic: Positive sentiment pushes price up slightly
            sentiment_impact = sentiment * 0.01
            noise = random.uniform(-0.02, 0.02)

            pred = last_close + sentiment_impact + noise
            predictions.append([pred])

        return np.array(predictions)

    def save(self, path: str):
        """Save stats to JSON."""
        with open(path, "w") as f:
            json.dump(self.stats, f)

    def load(self, path: str):
        """Load stats from JSON."""
        with open(path, "r") as f:
            self.stats = json.load(f)


class PricePredictorLSTM:
    """
    LSTM-based price predictor.
    Wraps TensorFlow/Keras model operations.
    Gracefully falls back to MockModel if TensorFlow is missing/broken.
    """

    def __init__(self, model_dir: str = MODEL_DIR):
        self.model = None
        self.model_dir = model_dir
        self.use_mock = False
        self._ensure_model_dir()

    def _ensure_model_dir(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _get_model_path(self, symbol: str, version: str = "v1") -> str:
        # If using mock, use .json
        if self.use_mock:
            return os.path.join(self.model_dir, f"{symbol}_mock_{version}.json")
        return os.path.join(self.model_dir, f"{symbol}_lstm_{version}.keras")

    def build_model(self, lookback: int = LOOKBACK, features: int = FEATURES):
        """Build the Keras LSTM model or fall back to Mock."""
        try:
            # Try importing TensorFlow
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, Input

            # Test simple operation to catch DLL errors early
            import tensorflow as tf

            _ = tf.constant(1)

            model = Sequential(
                [
                    Input(shape=(lookback, features)),
                    LSTM(units=50, return_sequences=True),
                    Dropout(0.2),
                    LSTM(units=50, return_sequences=False),
                    Dropout(0.2),
                    Dense(units=25, activation="relu"),
                    Dense(units=1),
                ]
            )
            model.compile(optimizer="adam", loss="mean_squared_error")
            self.model = model
            self.use_mock = False
            return model

        except (ImportError, Exception) as e:
            logger.error(f"TensorFlow unavailable ({e}). Swapping to MockModel.")
            self.use_mock = True
            self.model = MockModel()
            return self.model

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 25,
        batch_size: int = 32,
        validation_split: float = 0.1,
    ):
        """Train the model."""
        if self.model is None:
            self.build_model(lookback=X_train.shape[1], features=X_train.shape[2])

        if self.use_mock:
            return self.model.fit(X_train, y_train)

        return self.model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            # Try to restore context if possible, or raise
            raise ValueError("Model not loaded or built.")

        return self.model.predict(X)

    def save(self, symbol: str, version: str = "v1"):
        """Save model for a specific symbol."""
        if self.model is None:
            logger.warning("No model to save.")
            return

        path = self._get_model_path(symbol, version)

        if self.use_mock:
            self.model.save(path)
        else:
            self.model.save(path)

        logger.info(f"Model saved to {path} (Mock={self.use_mock})")

    def load(self, symbol: str, version: str = "v1") -> bool:
        """
        Load model for a symbol.
        Tries Keras first, then JSON (mock).
        """
        # Try Keras path
        keras_path = os.path.join(self.model_dir, f"{symbol}_lstm_{version}.keras")
        json_path = os.path.join(self.model_dir, f"{symbol}_mock_{version}.json")

        # Try Loading TensorFlow Model
        try:
            if os.path.exists(keras_path):
                from tensorflow.keras.models import load_model

                self.model = load_model(keras_path)
                self.use_mock = False
                logger.info(f"Loaded Keras model for {symbol}")
                return True
        except (ImportError, Exception) as e:
            logger.warning(f"Failed to load Keras model ({e}). Checking for mock.")

        # Try Loading Mock Model
        if os.path.exists(json_path):
            try:
                self.model = MockModel()
                self.model.load(json_path)
                self.use_mock = True
                logger.info(f"Loaded Mock model for {symbol}")
                return True
            except Exception as e:
                logger.error(f"Failed to load mock model: {e}")

        logger.warning(f"No valid model found for {symbol}")
        return False
