"""
Sentiment API Routes
Daily sentiment data endpoints and sentiment analysis.
"""

from datetime import date, timedelta
from typing import List, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from server.api.dependencies import DBSession
from server.models.models import Asset, DailySentiment
from server.schemas.schemas import DailySentimentResponse, SentimentListResponse


router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


# =============================================================================
# Additional Request/Response Models
# =============================================================================


class AnalyzeTextRequest(BaseModel):
    """Request model for text analysis."""

    text: str
    use_finbert: bool = True


class AnalyzeTextResponse(BaseModel):
    """Response model for text analysis."""

    text: str
    score: float
    label: Literal["bearish", "neutral", "bullish"]
    analyzer: str


class SentimentPipelineStatus(BaseModel):
    """Response model for pipeline status."""

    status: Literal["started", "running", "completed", "failed"]
    message: str
    stats: dict | None = None


# Pipeline state tracking
_sentiment_pipeline_state = {"running": False, "last_stats": None}


# =============================================================================
# Existing Endpoints
# =============================================================================


@router.get("/{symbol}", response_model=SentimentListResponse)
async def get_sentiment(
    symbol: str,
    db: DBSession,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of data"),
) -> SentimentListResponse:
    """
    Get daily sentiment data for an asset.

    Args:
        symbol: Trading symbol (e.g., 'AAPL')
        days: Number of days of historical data (default: 30)

    Returns:
        Sentiment data with average scores and headline counts.

    Raises:
        404: Asset not found.
    """
    # Check asset exists
    asset = db.get(Asset, symbol.upper())
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query sentiment
    result = db.execute(
        select(DailySentiment)
        .where(DailySentiment.symbol == symbol.upper())
        .where(DailySentiment.date >= start_date)
        .where(DailySentiment.date <= end_date)
        .order_by(DailySentiment.date.asc())
    )
    sentiments = result.scalars().all()

    return SentimentListResponse(
        symbol=symbol.upper(), data=sentiments, count=len(sentiments)
    )


@router.get("/{symbol}/latest", response_model=DailySentimentResponse)
async def get_latest_sentiment(symbol: str, db: DBSession) -> DailySentiment:
    """
    Get the most recent sentiment for an asset.

    Args:
        symbol: Trading symbol.

    Returns:
        Latest sentiment data.

    Raises:
        404: No sentiment data found.
    """
    result = db.execute(
        select(DailySentiment)
        .where(DailySentiment.symbol == symbol.upper())
        .order_by(DailySentiment.date.desc())
        .limit(1)
    )
    sentiment = result.scalar_one_or_none()

    if not sentiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sentiment data found for {symbol}",
        )

    return sentiment


# =============================================================================
# New Endpoints: Sentiment Analysis
# =============================================================================


@router.post("/analyze", response_model=AnalyzeTextResponse)
async def analyze_text(request: AnalyzeTextRequest) -> AnalyzeTextResponse:
    """
    Analyze sentiment of a single text.

    Args:
        request: Text to analyze and analyzer preference

    Returns:
        Sentiment score (-1 to +1) and label
    """
    from server.ml.finbert_analyzer import create_analyzer

    analyzer = create_analyzer(use_finbert=request.use_finbert)
    score = analyzer.analyze_single(request.text)

    # Determine label
    if score < -0.15:
        label = "bearish"
    elif score > 0.15:
        label = "bullish"
    else:
        label = "neutral"

    return AnalyzeTextResponse(
        text=request.text,
        score=score,
        label=label,
        analyzer="FinBERT" if request.use_finbert else "VADER",
    )


@router.post("/pipeline/run", response_model=SentimentPipelineStatus)
async def run_sentiment_pipeline(
    background_tasks: BackgroundTasks, use_finbert: bool = True, days_back: int = 30
) -> SentimentPipelineStatus:
    """
    Run the sentiment analysis pipeline.

    This pipeline:
    1. Scores all pending headlines with sentiment
    2. Computes daily sentiment aggregates for all assets

    Args:
        use_finbert: Use FinBERT (True) or VADER only (False)
        days_back: Days of history to compute aggregates for

    Returns:
        Pipeline status
    """
    global _sentiment_pipeline_state

    if _sentiment_pipeline_state["running"]:
        return SentimentPipelineStatus(
            status="running",
            message="Sentiment pipeline is already running",
            stats=_sentiment_pipeline_state["last_stats"],
        )

    def run_pipeline():
        global _sentiment_pipeline_state
        _sentiment_pipeline_state["running"] = True
        try:
            from server.services.sentiment_engine import run_sentiment_pipeline

            stats = run_sentiment_pipeline(use_finbert=use_finbert, days_back=days_back)
            _sentiment_pipeline_state["last_stats"] = stats
        except Exception as e:
            _sentiment_pipeline_state["last_stats"] = {"error": str(e)}
        finally:
            _sentiment_pipeline_state["running"] = False

    background_tasks.add_task(run_pipeline)

    return SentimentPipelineStatus(
        status="started",
        message=f"Sentiment pipeline started (FinBERT={use_finbert}, days={days_back})",
    )


@router.get("/pipeline/status", response_model=SentimentPipelineStatus)
async def get_sentiment_pipeline_status() -> SentimentPipelineStatus:
    """
    Get current sentiment pipeline status.

    Returns:
        Current status and stats from last run
    """
    global _sentiment_pipeline_state

    if _sentiment_pipeline_state["running"]:
        return SentimentPipelineStatus(
            status="running",
            message="Sentiment pipeline is running",
            stats=_sentiment_pipeline_state["last_stats"],
        )

    if _sentiment_pipeline_state["last_stats"]:
        return SentimentPipelineStatus(
            status="completed",
            message="Sentiment pipeline completed",
            stats=_sentiment_pipeline_state["last_stats"],
        )

    return SentimentPipelineStatus(
        status="completed", message="No sentiment pipeline has been run yet"
    )


@router.post("/{symbol}/score", response_model=dict)
async def score_headlines_for_symbol(
    symbol: str,
    db: DBSession,
    background_tasks: BackgroundTasks,
    use_finbert: bool = True,
) -> dict:
    """
    Score all unscored headlines for a specific symbol.

    Args:
        symbol: Asset symbol
        use_finbert: Use FinBERT or VADER

    Returns:
        Status message
    """
    # Verify asset exists
    asset = db.get(Asset, symbol.upper())
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )

    def score_symbol():
        from server.core.database import SessionLocal
        from server.services.sentiment_engine import SentimentScoringService

        session = SessionLocal()
        try:
            service = SentimentScoringService(use_finbert=use_finbert)
            count = service.score_headlines_for_symbol(session, symbol.upper())
        finally:
            session.close()

    background_tasks.add_task(score_symbol)

    return {"status": "started", "message": f"Scoring headlines for {symbol.upper()}"}
