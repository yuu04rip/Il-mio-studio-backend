from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import ConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./app.db"
    STORAGE_PATH: str = "./storage"

    # sostituisce la inner class Config
    model_config = ConfigDict(env_file=".env")


settings = Settings()