"""
Prediction API Routes
Endpoints for model training and price prediction.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from server.api.dependencies import DBSession
from server.models.models import Asset, Price
from server.schemas.schemas import PredictionRequest, PredictionResponse

from server.services.prediction_service import PredictionService
from server.core.database import SessionLocal
from server.core.sanitization import validate_symbol
from sqlalchemy import select

router = APIRouter(tags=["Predictions"])


# Helper to run training in background
def run_training_task(symbol: str):
    """Background task for model training."""
    db = SessionLocal()
    try:
        service = PredictionService(db)
        result = service.train_model(symbol)
        # In a real app, we'd store this result in a job/status table
        # or log it properly
        print(f"Training result for {symbol}: {result}")
    except Exception as e:
        print(f"Training failed for {symbol}: {e}")
    finally:
        db.close()


@router.post("/train/{symbol}")
async def train_model(
    symbol: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    Trigger model training for a symbol in the background.
    """
    symbol = validate_symbol(symbol)
    background_tasks.add_task(run_training_task, symbol)
    return {"status": "accepted", "message": f"Training started for {symbol}"}


from fastapi import Request
from server.core.limiter import limiter, RATE_LIMIT_PREDICT


@router.get("/{symbol}", response_model=PredictionResponse)
@limiter.limit(RATE_LIMIT_PREDICT)
async def predict_price(
    request: Request, symbol: str, db: DBSession
) -> PredictionResponse:
    """
    Generate next-day price prediction using LSTM model.
    """
    symbol = validate_symbol(symbol)
    service = PredictionService(db)

    # Check asset exists
    asset = db.get(Asset, symbol)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset {symbol} not found"
        )

    # Get latest price for reference
    result = db.execute(
        select(Price).where(Price.symbol == symbol).order_by(Price.date.desc()).limit(1)
    )
    latest_price = result.scalar_one_or_none()

    if not latest_price or not latest_price.close:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {symbol}",
        )

    current_price = float(latest_price.close)

    # Attempt prediction
    try:
        pred_result = service.predict_next_price(symbol)

        if pred_result.get("status") == "failed":
            # Fallback to mock if model fails (e.g. not trained yet)
            # This ensures the UI doesn't break during development
            # In prod, we might want to return 503 or 400
            if "Model not found" in pred_result["message"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Model not trained. Please Trigger training first.",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=pred_result["message"],
            )

        predicted_val = pred_result["predicted_price"]

        # Calculate derived stats
        change_pct = ((predicted_val - current_price) / current_price) * 100

        return PredictionResponse(
            symbol=symbol,
            current_price=Decimal(str(round(current_price, 2))),
            predicted_price=Decimal(str(round(predicted_val, 2))),
            direction="up" if predicted_val > current_price else "down",
            change_percent=Decimal(str(round(change_pct, 2))),
            sentiment_contribution=Decimal("0.0"),  # TODO: Calculate this impact
            prediction_date=pred_result["prediction_date"],
            model_version="lstm_v1",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Prediction failed for {symbol}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )
