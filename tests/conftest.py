"""
Pytest configuration and fixtures
"""
import os

# Set environment variables BEFORE importing app to avoid RuntimeError
os.environ.setdefault("USE_COGNITO", "true")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DEPLOYMENT_MODE", "local")
# Set Cognito settings for tests (can be empty strings, app will handle gracefully)
os.environ.setdefault("COGNITO_USER_POOL_ID", "test-pool-id")
os.environ.setdefault("COGNITO_CLIENT_ID", "test-client-id")
os.environ.setdefault("COGNITO_REGION", "us-east-1")
os.environ.setdefault("COGNITO_CALLBACK_URL", "http://localhost:8000/auth/callback")

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing"""
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key-for-testing")
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("USE_COGNITO", "true")  # Required - app raises error if False
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "test-pool-id")
    monkeypatch.setenv("COGNITO_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("COGNITO_REGION", "us-east-1")


