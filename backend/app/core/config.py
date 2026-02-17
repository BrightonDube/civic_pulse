import os
import logging

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./civicpulse_dev.db"
    SECRET_KEY: str = "change-me-in-production"
    GROQ_API_KEY: str = ""
    
    model_config = ConfigDict(env_file=".env")


settings = Settings()

if os.getenv("ENV", "development") == "production":
    if settings.SECRET_KEY == "change-me-in-production":
        raise RuntimeError("SECRET_KEY must be set in production")
    if "sqlite" in settings.DATABASE_URL:
        logger.warning("Using SQLite in production is not recommended")
