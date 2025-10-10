"""
Basic unit tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_recommend_endpoint():
    """Test recommendation endpoint (mock)."""
    response = client.get("/recommend/user_123?k=5")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert len(data["recommendations"]) == 5
    assert "model_version" in data
    assert "latency_ms" in data


def test_recommend_invalid_k():
    """Test recommendation with invalid k parameter."""
    response = client.get("/recommend/user_123?k=200")
    assert response.status_code == 400


def test_ingest_event():
    """Test event ingestion endpoint."""
    event_data = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_id": "550e8400-e29b-41d4-a716-446655440001",
        "event_type": "view",
        "value": 120.5,
    }
    response = client.post("/events", json=event_data)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"


def test_ingest_event_invalid_type():
    """Test event ingestion with invalid event type."""
    event_data = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_id": "550e8400-e29b-41d4-a716-446655440001",
        "event_type": "invalid_type",
    }
    response = client.post("/events", json=event_data)
    assert response.status_code == 422  # Validation error
