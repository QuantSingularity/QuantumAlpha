"""
Utility functions for QuantumAlpha services.
Provides common helper functions used across services.
"""

import hashlib
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password

    Args:
        password: Password to hash

    Returns:
        Hashed password
    """
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()
    return f"{salt}${pwdhash}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a password

    Args:
        stored_password: Stored hashed password
        provided_password: Password to verify

    Returns:
        True if password is correct, False otherwise
    """
    salt, stored_hash = stored_password.split("$")
    pwdhash = hashlib.pbkdf2_hmac(
        "sha256", provided_password.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()
    return pwdhash == stored_hash


def parse_timeframe(timeframe: str) -> Tuple[int, str]:
    """Parse a timeframe string

    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')

    Returns:
        Tuple of (value, unit)

    Raises:
        ValueError: If timeframe is invalid
    """
    if not timeframe:
        raise ValueError("Timeframe cannot be empty")
    value = ""
    unit = ""
    for char in timeframe:
        if char.isdigit():
            value += char
        else:
            unit += char
    if not value or not unit:
        raise ValueError(f"Invalid timeframe format: {timeframe}")
    value = int(value)
    if unit not in ["m", "h", "d", "wk", "mo"]:
        raise ValueError(f"Invalid timeframe unit: {unit}")
    return (value, unit)


def timeframe_to_seconds(timeframe: str) -> int:
    """Convert a timeframe to seconds

    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')

    Returns:
        Number of seconds

    Raises:
        ValueError: If timeframe is invalid
    """
    value, unit = parse_timeframe(timeframe)
    if unit == "m":
        return value * 60
    elif unit == "h":
        return value * 60 * 60
    elif unit == "d":
        return value * 24 * 60 * 60
    elif unit == "wk":
        return value * 7 * 24 * 60 * 60
    elif unit == "mo":
        return value * 30 * 24 * 60 * 60
    else:
        raise ValueError(f"Invalid timeframe unit: {unit}")


def timeframe_to_timedelta(timeframe: str) -> timedelta:
    """Convert a timeframe to timedelta

    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')

    Returns:
        Timedelta object

    Raises:
        ValueError: If timeframe is invalid
    """
    seconds = timeframe_to_seconds(timeframe)
    return timedelta(seconds=seconds)


def parse_period(period: str) -> datetime:
    """Parse a period string to get start date

    Args:
        period: Period string (e.g., '1d', '1wk', '1mo', '1y')

    Returns:
        Start date

    Raises:
        ValueError: If period is invalid
    """
    if not period:
        raise ValueError("Period cannot be empty")
    now = datetime.now(timezone.utc)
    if period == "1d":
        return now - timedelta(days=1)
    elif period == "1wk":
        return now - timedelta(weeks=1)
    elif period == "1mo":
        return now - timedelta(days=30)
    elif period == "3mo":
        return now - timedelta(days=90)
    elif period == "6mo":
        return now - timedelta(days=180)
    elif period == "1y":
        return now - timedelta(days=365)
    elif period == "5y":
        return now - timedelta(days=365 * 5)
    elif period == "max":
        return datetime(1970, 1, 1)
    else:
        raise ValueError(f"Invalid period: {period}")


def to_json_serializable(obj: object) -> object:
    """Convert an object to a JSON serializable format

    Args:
        obj: Object to convert

    Returns:
        JSON serializable object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    elif isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: to_json_serializable(value) for key, value in obj.items()}
    else:
        return obj


def ensure_directory(directory: str) -> None:
    """Ensure a directory exists

    Args:
        directory: Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def generate_api_key() -> Tuple[str, str]:
    """Generate an API key and secret

    Returns:
        Tuple of (key, secret)
    """
    key = secrets.token_hex(16)
    secret = secrets.token_hex(32)
    return (key, secret)


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, calls_per_second: float) -> None:
        """Initialize rate limiter

        Args:
            calls_per_second: Maximum calls per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_call_time = time.time()


class SimpleCache:
    """Simple in-memory cache"""

    def __init__(self, max_size: int = 1000, ttl: int = 300) -> None:
        """Initialize cache

        Args:
            max_size: Maximum number of items in cache
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        timestamp = self.timestamps.get(key, 0)
        if time.time() - timestamp > self.ttl:
            self.delete(key)
            return None
        return self.cache[key]

    def set(self, key: str, value: object) -> None:
        """Set a value in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            self.delete(oldest_key)
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """Delete a value from cache

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]

    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        self.timestamps.clear()
