"""
Common utilities for QuantumAlpha backend services.
"""

from .auth import AuthManager, require_auth, require_role
from .config import get_config_manager
from .database import DatabaseManager
from .logging_utils import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ServiceError,
    ValidationError,
    setup_logger,
)
from .models import Base
from .utils import RateLimiter, SimpleCache, parse_period
from .validation import validate_schema


def get_db_manager(database_url: str = None):
    """Get or create a DatabaseManager instance."""
    import os

    url = database_url or os.environ.get("DATABASE_URL")
    return DatabaseManager(url)


__all__ = [
    "setup_logger",
    "ServiceError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseManager",
    "get_db_manager",
    "Base",
    "AuthManager",
    "require_auth",
    "require_role",
    "get_config_manager",
    "RateLimiter",
    "SimpleCache",
    "parse_period",
    "validate_schema",
]
