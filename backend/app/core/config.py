from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/civicpulse"
    SECRET_KEY: str = "dev-secret-key"
    
    class Config:
        env_file = ".env"


settings = Settings()
