"""Application settings, loaded from environment variables.

No secrets are hardcoded here. Real values come from the .env file
(which is git-ignored) or from the deployment environment.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # "../.env" is used when running the backend directly from the backend/ folder.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_name: str = "MediLens API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/medilens.db"

    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 10
    allowed_origins: str = "http://localhost:5173"
    ocr_min_native_text_chars: int = 100

    llm_provider: Literal["ollama", "gemini", "none"] = "none"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
