"""
Test API routers
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_games_router_exists(client):
    """Test that games router is accessible"""
    # Test health endpoint
    response = client.get("/api/games/health")
    assert response.status_code == 200


def test_list_games_endpoint(client):
    """Test list games endpoint"""
    response = client.get("/api/games/list")
    # Should return 200 even if empty
    assert response.status_code == 200
    data = response.json()
    assert "games" in data
    assert isinstance(data["games"], list)


def test_auth_endpoints_exist(client):
    """Test that auth endpoints exist (may return errors without config)"""
    # These endpoints may return errors without proper OAuth config,
    # but they should exist (not 404)
    response = client.get("/auth/login")
    # Should not be 404 (might be 500 if not configured, which is OK)
    assert response.status_code != 404





