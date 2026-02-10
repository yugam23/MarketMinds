"""
MarketMinds Test Configuration
Pytest fixtures for testing.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from server.main import app
from server.core.database import get_db
from server.core.security import create_access_token
from server.models.models import Base, Asset
from server.models.user import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create database tables and provide session for test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provide test client with overridden database."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        hashed_password="hashedpassword",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        email="admin@example.com",
        hashed_password="hashedpassword",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def normal_user_token(sample_user):
    """Create a token for normal user."""
    return create_access_token(subject=sample_user.email)


@pytest.fixture
def admin_user_token(admin_user):
    """Create a token for admin user."""
    return create_access_token(subject=admin_user.email)


@pytest.fixture
def auth_headers(normal_user_token):
    """Return headers for normal user."""
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture
def admin_headers(admin_user_token):
    """Return headers for admin user."""
    return {"Authorization": f"Bearer {admin_user_token}"}


@pytest.fixture
def sample_asset(db_session):
    asset = Asset(
        symbol="RELIANCE.NS", name="Reliance Industries Ltd", asset_type="stock"
    )
    db_session.add(asset)
    db_session.commit()
    return asset


@pytest.fixture
def registered_user(db_session):
    """
    Create a user with a known password for login testing.
    Returns tuple of (user, plain_password).
    """
    from server.core.security import get_password_hash

    plain_password = "testpassword123"
    user = User(
        email="registered@example.com",
        hashed_password=get_password_hash(plain_password),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    return user, plain_password
