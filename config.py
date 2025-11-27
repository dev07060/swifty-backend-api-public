"""
Configuration module for Gemini API and application settings.
Validates required environment variables on startup.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration and validate required settings."""
        # Gemini API Configuration
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_api_url: str = os.getenv(
            "GEMINI_API_URL",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        )
        self.gemini_timeout: int = int(os.getenv("GEMINI_TIMEOUT", "30"))
        
        # Server Configuration
        self.max_image_size_mb: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        
        # CORS Configuration
        cors_origins_env = os.getenv("CORS_ORIGINS", "*")
        if cors_origins_env == "*":
            self.cors_origins = ["*"]
        else:
            # Split by comma and strip whitespace
            self.cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate that all required configuration is present and valid.
        
        Raises:
            ConfigurationError: If required configuration is missing or invalid.
        """
        errors = []
        
        # Validate Gemini API Key
        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY environment variable is required")
        elif len(self.gemini_api_key) < 10:
            errors.append("GEMINI_API_KEY appears to be invalid (too short)")
        
        # Validate Gemini API URL
        if not self.gemini_api_url:
            errors.append("GEMINI_API_URL environment variable is required")
        elif not self.gemini_api_url.startswith("https://"):
            errors.append("GEMINI_API_URL must use HTTPS protocol")
        
        # Validate timeout
        if self.gemini_timeout <= 0:
            errors.append("GEMINI_TIMEOUT must be a positive integer")
        
        # Validate max image size
        if self.max_image_size_mb <= 0:
            errors.append("MAX_IMAGE_SIZE_MB must be a positive integer")
        
        # Raise error if any validation failed
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.critical(error_message)
            raise ConfigurationError(error_message)
        
        logger.info("Configuration validated successfully")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Gemini API URL: {self.gemini_api_url}")
        logger.info(f"Gemini Timeout: {self.gemini_timeout}s")
        logger.info(f"Max Image Size: {self.max_image_size_mb}MB")
        logger.info(f"CORS Origins: {', '.join(self.cors_origins) if self.cors_origins != ['*'] else 'All origins (*)'}")

    
    @property
    def max_image_size_bytes(self) -> int:
        """Get maximum image size in bytes."""
        return self.max_image_size_mb * 1024 * 1024


# Global configuration instance
config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The application configuration.
    
    Raises:
        ConfigurationError: If configuration has not been initialized.
    """
    global config
    if config is None:
        raise ConfigurationError("Configuration has not been initialized. Call init_config() first.")
    return config


def init_config() -> Config:
    """
    Initialize the global configuration instance.
    
    Returns:
        Config: The initialized configuration.
    
    Raises:
        ConfigurationError: If configuration validation fails.
    """
    global config
    config = Config()
    return config
