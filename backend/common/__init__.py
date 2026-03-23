"""
Common utilities for QuantumAlpha services.
"""

# Logging, errors and service utilities
from .logging_utils import (
    setup_logger,
    ServiceError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
)

# Database
from .database import DatabaseManager

# Models
from .models import Base

# Auth
from .auth import AuthManager, require_auth, require_role

# Config
from .config import get_config_manager

# Utils (RateLimiter, SimpleCache, etc.)
from .utils import RateLimiter, SimpleCache

# Validation
from .validation import validate_schema


# Convenience function to get a db manager instance
def get_db_manager(database_url: str = None):
    """Get or create a DatabaseManager instance."""
    import os

    url = database_url or os.environ.get("DATABASE_URL")
    return DatabaseManager(url)


__all__ = [
    # Logging & Errors
    "setup_logger",
    "ServiceError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    # Database
    "DatabaseManager",
    "get_db_manager",
    # Models
    "Base",
    # Auth
    "AuthManager",
    "require_auth",
    "require_role",
    # Config
    "get_config_manager",
    # Utils
    "RateLimiter",
    "SimpleCache",
    # Validation
    "validate_schema",
]
