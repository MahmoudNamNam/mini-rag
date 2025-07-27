from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
import os

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """
    APP_NAME: str 
    APP_VERSION: str
    APP_DESCRIPTION: str
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE: int 
    FILE_DEFAULT_CHUNK_SIZE: int
    MONGO_URI: str
    MONGO_DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env")
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
