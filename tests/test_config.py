"""
Test configuration and settings
"""
import pytest
from app.core.config import settings


def test_settings_load():
    """Test that settings can be loaded"""
    assert settings.app_name is not None
    assert isinstance(settings.app_name, str)


def test_secret_key_set():
    """Test that secret key is set (even if default)"""
    assert settings.secret_key is not None
    assert len(settings.secret_key) > 0


def test_cors_origins():
    """Test CORS origins are parsed correctly"""
    assert isinstance(settings.cors_origins, list)
    assert len(settings.cors_origins) > 0


def test_allowed_redirect_uris():
    """Test allowed redirect URIs are parsed correctly"""
    assert isinstance(settings.allowed_redirect_uris, list)
    assert len(settings.allowed_redirect_uris) > 0


