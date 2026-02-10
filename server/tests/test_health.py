"""
Test Health Endpoint
"""

import pytest


def test_health_endpoint(client):
    """Test that health endpoint returns correct response."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["db"] == "connected"
    assert "version" in data


def test_root_endpoint(client):
    """Test that root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "MarketMinds" in data["message"]
