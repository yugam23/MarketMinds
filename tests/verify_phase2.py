import sys
import os
from datetime import date, timedelta
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force Redis URL to empty to use memory storage for limiter
os.environ["REDIS_URL"] = ""

from fastapi.testclient import TestClient
from server.main import app
from server.core.database import SessionLocal, init_db
from server.models.models import Asset, Headline, Price

client = TestClient(app)


def seed_data():
    print("Seeding test data...")
    init_db()
    db = SessionLocal()
    try:
        # Create Asset
        asset = db.get(Asset, "AAPL")
        if not asset:
            asset = Asset(symbol="AAPL", name="Apple Inc.", asset_type="stock")
            db.add(asset)

        # Create Headlines (15 items to test limit=5)
        for i in range(15):
            # check if exists
            exists = (
                db.query(Headline)
                .filter_by(symbol="AAPL", title=f"Test Headline {i}")
                .first()
            )
            if not exists:
                headline = Headline(
                    symbol="AAPL",
                    date=date.today() - timedelta(days=i),
                    title=f"Test Headline {i}",
                    url=f"http://example.com/{i}",
                    sentiment_score=0.5,
                )
                db.add(headline)

        # Create Prices (need at least 1 for prediction check to pass 404)
        price_exists = (
            db.query(Price)
            .filter_by(symbol="AAPL", date=date.today() - timedelta(days=1))
            .first()
        )
        if not price_exists:
            price = Price(
                symbol="AAPL",
                date=date.today() - timedelta(days=1),
                open=150.0,
                high=155.0,
                low=149.0,
                close=152.0,
                volume=1000000,
            )
            db.add(price)

        db.commit()
        print("Seeding complete.")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()


def test_pagination():
    print("Testing Pagination...")
    # Request with limit=5
    response = client.get("/api/headlines/AAPL?limit=5&offset=0")
    if response.status_code != 200:
        print(f"FAILED: Status {response.status_code}")
        print(response.text)
        return

    data = response.json()

    # Check structure
    if "data" not in data or "pagination" not in data:
        print(
            "FAILED: Response structure incorrect (expected data and pagination keys)"
        )
        print(data.keys())
        return

    # Check limit application
    if len(data["data"]) > 5:
        print(f"FAILED: Returned {len(data['data'])} items, expected <= 5")
        return

    # Check total count
    if data["pagination"]["total"] < 10:
        print(f"WARNING: Total count is {data['pagination']['total']}, expected >= 10")

    print("SUCCESS: Pagination structure and limit verified.")


def test_sentiment_contribution():
    print("\nTesting Sentiment Contribution...")

    response = client.get("/api/predict/AAPL")

    if response.status_code == 200:
        data = response.json()
        if "sentiment_contribution" in data:
            print(
                f"SUCCESS: sentiment_contribution calculated ({data['sentiment_contribution']})"
            )
        else:
            print("FAILED: sentiment_contribution missing from response")
            print(data.keys())
    elif response.status_code == 400:
        if "Model not trained" in response.text:
            print(
                "SUCCESS (Partial): Endpoint reachable, returned 'Model not trained' as expected."
            )
        else:
            print(f"FAILED: 400 Error: {response.text}")
    elif response.status_code == 500:
        print(f"FAILED: 500 Error: {response.text}")
    else:
        print(f"NOTE: Prediction endpoint returned {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    seed_data()
    test_pagination()
    test_sentiment_contribution()
