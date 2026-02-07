# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Financial Report Analyst"
    env: str = "dev"

    # ✅ ADD THIS (ONE LINE)
    openai_api_key: str | None = None

    # storage
    storage_dir: str = "storage"
    upload_dir: str = "storage/uploads"
    extracted_dir: str = "storage/extracted"
    chunks_dir: str = "storage/chunks"

    # limits/logging
    max_upload_mb: int = 50
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )


settings = Settings()
