"""
ML Model Prewarming
Utility to preload ML models on application startup for faster first predictions.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global model cache
_model_cache: dict = {}


def prewarm_sentiment_model() -> bool:
    """
    Preload the FinBERT sentiment analysis model.

    Returns:
        True if model loaded successfully, False otherwise
    """
    try:
        from server.ml.finbert_analyzer import SentimentAnalyzer

        logger.info("Prewarming sentiment analysis model...")
        analyzer = SentimentAnalyzer()
        _model_cache["sentiment"] = analyzer

        # Warm up the model with a test sentence
        _ = analyzer.analyze("Market outlook is positive.")
        logger.info("✓ Sentiment model prewarmed successfully")
        return True

    except Exception as e:
        logger.warning(f"Failed to prewarm sentiment model: {e}")
        return False


def prewarm_lstm_model() -> bool:
    """
    Preload the LSTM prediction model structure.

    Note: The actual model weights are loaded per-symbol,
    but we can initialize the TensorFlow graph here.

    Returns:
        True if model framework is ready, False otherwise
    """
    try:
        from server.ml.lstm_model import LSTMPricePredictor

        logger.info("Prewarming LSTM model framework...")
        predictor = LSTMPricePredictor()
        _model_cache["lstm"] = predictor
        logger.info("✓ LSTM model framework prewarmed successfully")
        return True

    except Exception as e:
        logger.warning(f"Failed to prewarm LSTM model: {e}")
        return False


def prewarm_all_models() -> dict:
    """
    Prewarm all ML models on application startup.

    Returns:
        Dictionary with model names and their prewarm status
    """
    logger.info("=" * 50)
    logger.info("Prewarming ML models...")
    logger.info("=" * 50)

    results = {
        "sentiment": prewarm_sentiment_model(),
        "lstm": prewarm_lstm_model(),
    }

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    logger.info(
        f"Model prewarming complete: {success_count}/{total_count} models ready"
    )
    logger.info("=" * 50)

    return results


def get_cached_model(model_name: str) -> Optional[object]:
    """
    Retrieve a prewarmed model from cache.

    Args:
        model_name: Name of the model ("sentiment" or "lstm")

    Returns:
        The cached model instance, or None if not cached
    """
    return _model_cache.get(model_name)


def clear_model_cache() -> None:
    """
    Clear all cached models from memory.

    Useful for testing or memory management.
    """
    global _model_cache
    _model_cache = {}
    logger.info("Model cache cleared")
