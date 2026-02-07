"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    # Application settings
    app_name: str = "pdf-context-narrator"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Data directories
    data_dir: Path = Path("data")
    cache_dir: Path = Path("cache")
    logs_dir: Path = Path("logs")
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # Database settings (for future use)
    database_url: Optional[str] = None
    
    # API settings (for future use)
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    
    # Processing settings
    max_workers: int = 4
    batch_size: int = 10
    memory_limit_mb: Optional[int] = None
    checkpoint_dir: Path = Path("checkpoints")
    
    # OCR settings
    ocr_low_text_threshold: float = 50.0  # Minimum chars per page for "normal" text
    ocr_max_retries: int = 3
    ocr_retry_delay: float = 1.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PDF_CN_",
        case_sensitive=False,
        extra="ignore",
    )
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses lru_cache to ensure we only create one Settings instance.
    """
    settings = Settings()
    settings.create_directories()
    return settings
