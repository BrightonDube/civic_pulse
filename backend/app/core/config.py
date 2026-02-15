from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/civicpulse"
    SECRET_KEY: str = "dev-secret-key"
    
    model_config = ConfigDict(env_file=".env")


settings = Settings()
