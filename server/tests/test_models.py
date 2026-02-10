"""
Test Models
"""

from sqlalchemy.orm import Session
from server.models.user import User
from server.models.models import Asset


def test_user_model(db_session: Session):
    user = User(email="model@test.com", hashed_password="pw", is_active=True)
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.query(User).filter(User.email == "model@test.com").first()
    assert retrieved is not None
    assert retrieved.email == "model@test.com"


def test_asset_model(db_session: Session):
    asset = Asset(symbol="TEST.NS", name="Test Asset", asset_type="stock")
    db_session.add(asset)
    db_session.commit()

    retrieved = db_session.query(Asset).filter(Asset.symbol == "TEST.NS").first()
    assert retrieved is not None
    assert retrieved.name == "Test Asset"
