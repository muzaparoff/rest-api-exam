"""
Application settings and configuration management.

This module provides centralized configuration management using Pydantic BaseSettings
for environment variable handling and type validation.
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables with USERAPI_ prefix.
    """
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/users.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )
    
    # Security Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT token signing secret key"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT token signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # API Configuration
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_title: str = Field(
        default="User Management API",
        description="API title for documentation"
    )
    api_description: str = Field(
        default="Professional REST API for managing users with Israeli validation",
        description="API description for documentation"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="Allowed HTTP methods for CORS"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed headers for CORS"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s",
        description="Log message format"
    )
    log_file: Optional[str] = Field(
        default="/app/logs/api.log",
        description="Log file path (None for stdout only)"
    )
    
    # Performance Configuration
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_request_size: int = Field(
        default=1024 * 1024,  # 1MB
        description="Maximum request size in bytes"
    )
    
    # Monitoring Configuration
    enable_metrics: bool = Field(
        default=True,
        description="Enable request metrics collection"
    )
    slow_request_threshold: float = Field(
        default=1.0,
        description="Log requests slower than this threshold (seconds)"
    )
    
    # Health Check Configuration
    health_check_timeout: int = Field(
        default=5,
        description="Health check timeout in seconds"
    )
    
    # Development/Debug Configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload in development"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is a valid logging level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins format"""
        if isinstance(v, str):
            # Handle comma-separated string from environment
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        """Warn about default JWT secret in production"""
        if v == "your-secret-key-change-in-production":
            logger.warning(
                "Using default JWT secret key. Please set USERAPI_JWT_SECRET_KEY "
                "environment variable for production use."
            )
        if len(v) < 32:
            logger.warning(
                "JWT secret key is shorter than recommended 32 characters. "
                "Consider using a longer, more secure key."
            )
        return v
    
    class Config:
        env_prefix = "USERAPI_"
        env_file = ".env"
        case_sensitive = False
        
        # Example .env file content
        schema_extra = {
            "example": {
                "database_url": "postgresql://user:pass@localhost/userapi",
                "jwt_secret_key": "super-secret-jwt-key-min-32-chars",
                "log_level": "INFO",
                "cors_origins": "http://localhost:3000,https://app.company.com",
                "debug": False
            }
        }

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings instance"""
    return settings

def configure_logging():
    """Configure application logging based on settings"""
    import logging.config
    
    # Create logs directory if it doesn't exist
    if settings.log_file and not os.path.exists(os.path.dirname(settings.log_file)):
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {  # root logger
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if settings.log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "standard",
            "filename": settings.log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5
        }
        # Add file handler to all loggers
        for logger_name in logging_config["loggers"]:
            logging_config["loggers"][logger_name]["handlers"].append("file")
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level}, File: {settings.log_file}")

# Initialize logging when module is imported
configure_logging()
