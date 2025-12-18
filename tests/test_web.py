"""
Tests for web API
"""

import pytest
from fastapi.testclient import TestClient
from src.web.api import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Trading Platform API"}

def test_health_endpoint():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"

def test_markets_endpoint():
    """Test markets endpoint"""
    response = client.get("/markets")
    assert response.status_code == 200
    data = response.json()
    assert "markets" in data
    assert isinstance(data["markets"], list)
