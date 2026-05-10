"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from .env or environment."""

    APP_NAME: str = "Metron API"
    APP_VERSION: str = "1.0.0"
    DEBUG: str | bool = False

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://metron:metron@localhost:5432/metron"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://metron:metron@localhost:5432/metron"

    # ML model path (joblib artifact)
    ML_MODEL_PATH: str = "app/ml/density_model.joblib"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
