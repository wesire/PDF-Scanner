"""Logging configuration for PDF Context Narrator."""

import logging
import sys
from pathlib import Path
from typing import Optional

from pdf_context_narrator.config import get_settings


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    settings = get_settings()
    
    # Use provided level or fall back to settings
    log_level = level or settings.log_level
    
    # Create formatter
    formatter = logging.Formatter(settings.log_format)
    
    # Configure root logger
    root_logger = logging.getLogger("pdf_context_narrator")
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    file_path = log_file or settings.log_file
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    root_logger.info(f"Logging configured at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    # Ensure logging is set up
    if not logging.getLogger("pdf_context_narrator").handlers:
        setup_logging()
    
    return logging.getLogger(f"pdf_context_narrator.{name}")
