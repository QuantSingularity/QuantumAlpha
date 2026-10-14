import json
import logging
import logging.handlers
import os
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional


def setup_logger(
    name: str, log_level: int = logging.INFO, log_file: Optional[str] = None
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


class ServiceError(Exception):

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message} - {json.dumps(self.details)}"


class ValidationError(ServiceError):

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, 400, details)


class NotFoundError(ServiceError):

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, 404, details)


class AuthenticationError(ServiceError):

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, 401, details)


class AuthorizationError(ServiceError):

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, 403, details)


def log_exceptions(logger: logging.Logger) -> Callable:

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceError as e:
                logger.error(f"Service error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                raise ServiceError(str(e))

        return wrapper

    return decorator
