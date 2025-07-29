from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
import os

class Settings(BaseSettings):
    # App info
    APP_NAME: str 
    APP_VERSION: str
    APP_DESCRIPTION: str

    # File config
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE: int 
    FILE_DEFAULT_CHUNK_SIZE: int

    # MongoDB
    MONGO_URI: str
    MONGO_DB_NAME: str

    # LLM config
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str = None
    OPENAI_API_URL: str = None
    COHERE_API_KEY: str = None

    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None

    # Limits
    INPUT_DEFAULT_MAX_CHARACTERS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPERATURE: float = None

    # Vector Database Configuration
    VECTOR_DB_BACKEND:str
    VECTOR_DB_PATH : str 
    VECTOR_DB_DISTANCE_METHOD : str



    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env")
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
