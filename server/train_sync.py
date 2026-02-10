import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from server.core.database import SessionLocal
from server.services.prediction_service import PredictionService


def train_manual(symbol: str):
    db = SessionLocal()
    try:
        print(f"Initializing PredictionService for {symbol}...")
        service = PredictionService(db)

        print(f"Starting training for {symbol}...")
        result = service.train_model(symbol)

        print(f"Training Result: {result}")

    except Exception as e:
        print(f"Training Failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    train_manual("AAPL")
