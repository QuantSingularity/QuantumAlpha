import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    TESTING = os.getenv("FLASK_TESTING", "false").lower() == "true"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = False

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    API_KEY = os.getenv("API_KEY")
