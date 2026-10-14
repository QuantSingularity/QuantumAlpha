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


def get_db_manager(database_url=None):
    import os

    url = None
    if isinstance(database_url, str):
        url = database_url
    elif isinstance(database_url, dict):
        url = (
            database_url.get("database_url")
            or database_url.get("DATABASE_URL")
            or database_url.get("postgres_url")
        )
    if not url:
        url = os.environ.get("DATABASE_URL")
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
