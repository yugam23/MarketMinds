"""
MarketMinds Pipeline API Routes
Endpoints for triggering and monitoring data pipelines.
"""

import logging
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.api.dependencies import get_db
from server.pipelines.daily_ingestion import (
    DailyIngestionPipeline,
    seed_default_assets,
    run_daily_pipeline,
)
from server.core.sanitization import validate_symbol


logger = logging.getLogger(__name__)
router = APIRouter(tags=["pipeline"])


# =============================================================================
# Response Models
# =============================================================================


class PipelineStatus(BaseModel):
    """Response model for pipeline status."""

    status: Literal["started", "running", "completed", "failed"]
    message: str
    stats: dict | None = None


class SeedResponse(BaseModel):
    """Response model for asset seeding."""

    seeded: list[str]
    message: str


# =============================================================================
# Pipeline State (simple in-memory tracking)
# =============================================================================

_pipeline_state = {"running": False, "last_stats": None}


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/run", response_model=PipelineStatus)
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    days: int = Query(default=30, ge=1, le=365, description="Historical days to fetch"),
    db: Session = Depends(get_db),
) -> PipelineStatus:
    """
    Trigger the daily ingestion pipeline.

    This runs the full pipeline in the background:
    - Fetches OHLC data for all tracked assets
    - Fetches headlines from NewsAPI
    - Stores data in database

    Args:
        days: Number of historical days to fetch (default: 30)

    Returns:
        Pipeline status with message
    """
    global _pipeline_state

    if _pipeline_state["running"]:
        return PipelineStatus(
            status="running",
            message="Pipeline is already running. Please wait.",
            stats=_pipeline_state["last_stats"],
        )

    async def run_pipeline_task():
        global _pipeline_state
        _pipeline_state["running"] = True
        try:
            stats = await run_daily_pipeline(days=days)
            _pipeline_state["last_stats"] = stats
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            _pipeline_state["last_stats"] = {"error": str(e)}
        finally:
            _pipeline_state["running"] = False

    # Run in background
    background_tasks.add_task(run_pipeline_task)

    return PipelineStatus(
        status="started",
        message=f"Pipeline started for {days} days of data. Check /pipeline/status for progress.",
    )


@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status() -> PipelineStatus:
    """
    Get current pipeline status and last run statistics.

    Returns:
        Current status and stats from last run
    """
    global _pipeline_state

    if _pipeline_state["running"]:
        return PipelineStatus(
            status="running",
            message="Pipeline is currently running",
            stats=_pipeline_state["last_stats"],
        )

    if _pipeline_state["last_stats"]:
        return PipelineStatus(
            status="completed",
            message="Pipeline completed",
            stats=_pipeline_state["last_stats"],
        )

    return PipelineStatus(status="completed", message="No pipeline has been run yet")


@router.post("/seed", response_model=SeedResponse)
async def seed_assets(
    db: Session = Depends(get_db),
) -> SeedResponse:
    """
    Seed the database with default tracked assets.

    Seeds: AAPL, MSFT, GOOGL, TSLA, AMZN, BTC-USD, ETH-USD

    Returns:
        List of newly seeded symbols
    """
    try:
        seeded = await seed_default_assets(db)

        if seeded:
            return SeedResponse(
                seeded=seeded, message=f"Seeded {len(seeded)} new assets"
            )
        else:
            return SeedResponse(seeded=[], message="All default assets already exist")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
