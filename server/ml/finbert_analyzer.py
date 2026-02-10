"""
MarketMinds FinBERT Sentiment Analyzer
Financial sentiment analysis using ProsusAI/finbert model.

Architecture:
- FinBERTAnalyzer: Primary analyzer using HuggingFace transformers
- VADERAnalyzer: Lightweight fallback for quick analysis
- Combined approach for robustness

Model Info:
- FinBERT is specifically trained on financial text
- Output: negative, neutral, positive probabilities
- Score mapping: [-1, +1] where -1=bearish, +1=bullish
"""

import logging
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FinBERT Analyzer (Primary)
# =============================================================================


class FinBERTAnalyzer:
    """
    Financial sentiment analyzer using ProsusAI/finbert.

    FinBERT is a BERT model fine-tuned on financial text for
    sentiment classification. It outputs probabilities for
    negative, neutral, and positive sentiment.

    Example:
        analyzer = FinBERTAnalyzer()
        scores = analyzer.analyze(["Apple beats Q4 earnings expectations"])
        # Returns: [0.85]  # Very positive

    Notes:
        - First call will download the model (~400MB)
        - GPU acceleration supported if CUDA available
        - Batch processing for efficiency
    """

    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self, device: str | None = None):
        """
        Initialize FinBERT analyzer.

        Args:
            device: Force device ('cpu', 'cuda', or None for auto-detect)
        """
        self.model = None
        self.tokenizer = None
        self._device = device
        self._initialized = False

    def _load_model(self) -> None:
        """Lazy-load the model on first use."""
        if self._initialized:
            return

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            logger.info(f"Loading FinBERT model: {self.MODEL_NAME}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME
            )

            # Determine device
            if self._device:
                self.device = self._device
            else:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode

            logger.info(f"FinBERT loaded on device: {self.device}")
            self._initialized = True

        except ImportError as e:
            logger.error(f"Required packages not installed: {e}")
            raise ImportError("FinBERT requires: pip install transformers torch") from e
        except Exception as e:
            logger.error(f"Failed to load FinBERT: {e}")
            raise

    def analyze(self, texts: list[str], batch_size: int = 16) -> list[float]:
        """
        Analyze sentiment of financial texts.

        Args:
            texts: List of headlines or text to analyze
            batch_size: Number of texts to process at once

        Returns:
            List of sentiment scores in range [-1, +1]
            -1 = very negative/bearish
             0 = neutral
            +1 = very positive/bullish
        """
        import torch

        self._load_model()

        if not texts:
            return []

        scores = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)

                # FinBERT outputs: [negative, neutral, positive]
                # Map to [-1, 1]: score = positive - negative
                for prob in probs:
                    negative = prob[0].item()
                    positive = prob[2].item()
                    score = positive - negative
                    scores.append(round(score, 4))

        return scores

    def analyze_single(self, text: str) -> float:
        """Analyze a single text and return sentiment score."""
        scores = self.analyze([text])
        return scores[0] if scores else 0.0

    def get_sentiment_label(
        self, score: float
    ) -> Literal["bearish", "neutral", "bullish"]:
        """
        Convert score to human-readable label.

        Args:
            score: Sentiment score in [-1, +1]

        Returns:
            'bearish', 'neutral', or 'bullish'
        """
        if score < -0.15:
            return "bearish"
        elif score > 0.15:
            return "bullish"
        else:
            return "neutral"


# =============================================================================
# VADER Analyzer (Fallback)
# =============================================================================


class VADERAnalyzer:
    """
    Lightweight sentiment analyzer using NLTK's VADER.

    VADER (Valence Aware Dictionary and sEntiment Reasoner) is
    a rule-based sentiment analyzer that works well on social
    media and news headlines.

    Advantages over FinBERT:
    - Much faster (no neural network)
    - No GPU required
    - Works offline

    Disadvantages:
    - Not specifically trained on financial text
    - May miss financial context

    Example:
        analyzer = VADERAnalyzer()
        score = analyzer.analyze_single("Stock market crashes")
        # Returns: -0.64
    """

    def __init__(self):
        """Initialize VADER analyzer."""
        self.sia = None
        self._initialized = False

    def _load_analyzer(self) -> None:
        """Lazy-load VADER on first use."""
        if self._initialized:
            return

        try:
            import nltk
            from nltk.sentiment import SentimentIntensityAnalyzer

            # Download VADER lexicon if not present
            try:
                nltk.data.find("sentiment/vader_lexicon.zip")
            except LookupError:
                logger.info("Downloading VADER lexicon...")
                nltk.download("vader_lexicon", quiet=True)

            self.sia = SentimentIntensityAnalyzer()
            self._initialized = True
            logger.info("VADER analyzer initialized")

        except ImportError as e:
            logger.error(f"NLTK not installed: {e}")
            raise ImportError("VADER requires: pip install nltk") from e

    def analyze(self, texts: list[str]) -> list[float]:
        """
        Analyze sentiment of texts using VADER.

        Args:
            texts: List of texts to analyze

        Returns:
            List of compound scores in range [-1, +1]
        """
        self._load_analyzer()

        scores = []
        for text in texts:
            result = self.sia.polarity_scores(text)
            scores.append(round(result["compound"], 4))

        return scores

    def analyze_single(self, text: str) -> float:
        """Analyze a single text."""
        scores = self.analyze([text])
        return scores[0] if scores else 0.0


# =============================================================================
# Combined Analyzer (with fallback)
# =============================================================================


class SentimentAnalyzer:
    """
    Combined sentiment analyzer with fallback support.

    Attempts FinBERT first, falls back to VADER on failure.
    Useful for:
    - Development environments without GPU
    - Quick analysis when model unavailable
    - Error resilience in production

    Example:
        analyzer = SentimentAnalyzer(use_finbert=True)
        scores = analyzer.analyze(["Tech stocks rally on AI news"])
    """

    def __init__(self, use_finbert: bool = True):
        """
        Initialize combined analyzer.

        Args:
            use_finbert: Whether to try FinBERT first (True) or use VADER only
        """
        self.use_finbert = use_finbert
        self._finbert: FinBERTAnalyzer | None = None
        self._vader: VADERAnalyzer | None = None

    @property
    def finbert(self) -> FinBERTAnalyzer:
        """Lazy-load FinBERT analyzer."""
        if self._finbert is None:
            self._finbert = FinBERTAnalyzer()
        return self._finbert

    @property
    def vader(self) -> VADERAnalyzer:
        """Lazy-load VADER analyzer."""
        if self._vader is None:
            self._vader = VADERAnalyzer()
        return self._vader

    def analyze(self, texts: list[str], batch_size: int = 16) -> list[float]:
        """
        Analyze texts with fallback support.

        Args:
            texts: List of texts to analyze
            batch_size: Batch size for FinBERT

        Returns:
            List of sentiment scores in [-1, +1]
        """
        if not texts:
            return []

        if self.use_finbert:
            try:
                return self.finbert.analyze(texts, batch_size)
            except Exception as e:
                logger.warning(f"FinBERT failed, falling back to VADER: {e}")

        # Fallback to VADER
        return self.vader.analyze(texts)

    def analyze_single(self, text: str) -> float:
        """Analyze a single text."""
        scores = self.analyze([text])
        return scores[0] if scores else 0.0


# =============================================================================
# Factory Function
# =============================================================================


def create_analyzer(use_finbert: bool = True) -> SentimentAnalyzer:
    """
    Create a sentiment analyzer instance.

    Args:
        use_finbert: Use FinBERT (True) or VADER only (False)

    Returns:
        Configured SentimentAnalyzer instance
    """
    return SentimentAnalyzer(use_finbert=use_finbert)
