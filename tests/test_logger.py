"""Tests for logging module."""

import logging

from pdf_context_narrator.logger import get_logger, setup_logging


def test_get_logger():
    """Test logger creation."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert "pdf_context_narrator.test_module" in logger.name


def test_setup_logging():
    """Test logging setup."""
    setup_logging(level="DEBUG")
    logger = logging.getLogger("pdf_context_narrator")
    assert logger.level == logging.DEBUG


def test_logger_has_handlers():
    """Test that logger has handlers configured."""
    get_logger("test")
    root_logger = logging.getLogger("pdf_context_narrator")
    assert len(root_logger.handlers) > 0
