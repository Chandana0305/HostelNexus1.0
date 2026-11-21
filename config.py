import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from .env when present.
load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    """Shared configuration for local development and production."""

    ENVIRONMENT = os.getenv("FLASK_ENV", "development").lower()
    IS_PRODUCTION = ENVIRONMENT == "production"

    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if IS_PRODUCTION:
            raise RuntimeError("SECRET_KEY must be set in production.")
        SECRET_KEY = "local-development-only-change-before-deployment"

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "hostelnexus")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8

    PREFERRED_URL_SCHEME = "https" if IS_PRODUCTION else "http"
