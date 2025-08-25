# src/helper/config.py
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import List, Optional, Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    # --- App info ---
    APP_NAME: str
    APP_VERSION: str
    APP_DESCRIPTION: str

    # --- File config ---
    FILE_ALLOWED_TYPES: List[str]
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # --- MongoDB ---
    MONGO_URI: str
    MONGO_DB_NAME: str

    # --- POSTGRES ---
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str

    # --- LLM config ---
    GENERATION_BACKEND_LITERAL: Optional[List[str]] = None
    GENERATION_BACKEND: str

    EMBEDDING_BACKEND_LITERAL: Optional[List[str]] = None
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    GENERATION_MODEL_ID_LITERAL: Optional[List[str]] = None
    GENERATION_MODEL_ID: Optional[str] = None

    EMBEDDING_MODEL_ID_LITERAL: Optional[List[str]] = None
    EMBEDDING_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_SIZE: Optional[int] = None

    # --- Limits ---
    INPUT_DEFAULT_MAX_CHARACTERS: Optional[int] = None
    GENERATION_DEFAULT_MAX_TOKENS: Optional[int] = None
    GENERATION_DEFAULT_TEMPERATURE: Optional[float] = None

    # --- Vector DB ---
    VECTOR_DB_BACKEND_LITERAL: Optional[List[str]] = None
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str

    VECTOR_DB_DISTANCE_METHOD_LITERAL: Optional[List[str]] = None
    VECTOR_DB_DISTANCE_METHOD: str

    # --- Template Configs ---
    PRIMARY_LANG_LITERAL: Optional[List[str]] = None
    PRIMARY_LANG: str = "en"
    DEFAULT_LANG: str = "en"

    # .env loading
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
        case_sensitive=False,
    )

    @field_validator(
        "FILE_ALLOWED_TYPES",
        "GENERATION_BACKEND_LITERAL",
        "EMBEDDING_BACKEND_LITERAL",
        "GENERATION_MODEL_ID_LITERAL",
        "EMBEDDING_MODEL_ID_LITERAL",
        "VECTOR_DB_BACKEND_LITERAL",
        "VECTOR_DB_DISTANCE_METHOD_LITERAL",
        "PRIMARY_LANG_LITERAL",
        mode="before",
    )
    @classmethod
    def _parse_list_env(cls, v: Any) -> Any:
        if v is None or isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                try:
                    return json.loads(s)
                except Exception:
                    # fall through to comma-split if JSON fails
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return v

    # --- model-level literal checks (runs after field validation) ---
    @model_validator(mode="after")
    def _validate_dynamic_literals(self) -> Self:
        def check(field_name: str, literal_field: str) -> None:
            literals = getattr(self, literal_field, None)
            value = getattr(self, field_name, None)
            if literals and value is not None and value not in literals:
                raise ValueError(
                    f"{field_name} must be one of {literals}, got {value!r}"
                )

        check("GENERATION_BACKEND", "GENERATION_BACKEND_LITERAL")
        check("EMBEDDING_BACKEND", "EMBEDDING_BACKEND_LITERAL")
        check("GENERATION_MODEL_ID", "GENERATION_MODEL_ID_LITERAL")
        check("EMBEDDING_MODEL_ID", "EMBEDDING_MODEL_ID_LITERAL")
        check("VECTOR_DB_BACKEND", "VECTOR_DB_BACKEND_LITERAL")
        check("VECTOR_DB_DISTANCE_METHOD", "VECTOR_DB_DISTANCE_METHOD_LITERAL")
        check("PRIMARY_LANG", "PRIMARY_LANG_LITERAL")
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
