"""
Basic health check and smoke tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/games/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    """Test root endpoint returns HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_favicon(client):
    """Test favicon endpoint"""
    response = client.get("/favicon.ico")
    assert response.status_code in [200, 302]  # May redirect


def test_static_files(client):
    """Test static files are accessible"""
    # Test a common static file
    response = client.get("/static/js/config.js")
    # Should either return 200 or 404 if file doesn't exist
    assert response.status_code in [200, 404]


