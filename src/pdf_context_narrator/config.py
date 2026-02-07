"""Configuration management using Pydantic settings with profile support."""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    # Application settings
    app_name: str = "pdf-context-narrator"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"  # local, offline, cloud
    
    # Data directories
    data_dir: Path = Path("data")
    cache_dir: Path = Path("cache")
    logs_dir: Path = Path("logs")
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    structured_logging: bool = False  # Enable JSON structured logging
    
    # Database settings (for future use)
    database_url: Optional[str] = None
    
    # API settings (for future use)
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    
    # Processing settings
    max_workers: int = 4
    batch_size: int = 10
    
    # Cloud settings (for cloud profile)
    cloud_storage_bucket: Optional[str] = None
    cloud_storage_prefix: Optional[str] = None
    
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
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Settings":
        """
        Load settings from a YAML configuration file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            Settings instance with values from YAML file
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f) or {}
        
        # Create settings instance with YAML values
        return cls(**config_data)
    
    @classmethod
    def from_profile(cls, profile: str) -> "Settings":
        """
        Load settings from a predefined profile.
        
        Args:
            profile: Profile name (local, offline, cloud)
            
        Returns:
            Settings instance configured for the profile
        """
        config_path = Path("configs") / f"{profile}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Profile configuration not found: {config_path}")
        
        return cls.from_yaml(config_path)


# Global settings instance cache
_settings_instance: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None, profile: Optional[str] = None) -> Settings:
    """
    Get settings instance.
    
    Args:
        config_path: Optional path to YAML configuration file
        profile: Optional profile name (local, offline, cloud)
        
    Returns:
        Configured settings instance
        
    Note:
        This function caches the settings instance. To reload settings,
        call clear_settings_cache() first.
    """
    global _settings_instance
    
    if _settings_instance is None:
        if config_path:
            _settings_instance = Settings.from_yaml(config_path)
        elif profile:
            _settings_instance = Settings.from_profile(profile)
        else:
            _settings_instance = Settings()
        
        _settings_instance.create_directories()
    
    return _settings_instance


def clear_settings_cache() -> None:
    """Clear the cached settings instance."""
    global _settings_instance
    _settings_instance = None
