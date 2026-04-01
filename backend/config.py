"""
Configuration module for the application.

Loads configuration from environment variables and a .env file.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    TESTING = os.getenv("FLASK_TESTING", "false").lower() == "true"

    # JWT configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = False  # Managed by auth module

    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Example API Key
    API_KEY = os.getenv("API_KEY")
