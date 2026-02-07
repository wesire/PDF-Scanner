"""Tests for configuration module."""

import pytest
from pathlib import Path

from pdf_context_narrator.config import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    assert settings.app_name == "pdf-context-narrator"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.max_workers == 4


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_create_directories(tmp_path):
    """Test directory creation."""
    settings = Settings(
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        logs_dir=tmp_path / "logs",
    )
    settings.create_directories()
    
    assert settings.data_dir.exists()
    assert settings.cache_dir.exists()
    assert settings.logs_dir.exists()
