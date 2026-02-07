from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/civicpulse"
    SECRET_KEY: str = "dev-secret-key"
    ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:4173"]
    )

    class Config:
        env_file = ".env"


settings = Settings()
